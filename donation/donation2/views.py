import pdfkit
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DonationForm, DonationCategoryForm, DonationEventForm
from myapp.models import DonationEvent, DonationCategory, Donation
from myapp.forms import DonationEventForm
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.db import models
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
from django.contrib import messages
from datetime import timedelta, datetime
from .ai_services import DonationAIService, UnifiedAIAssistant, DonorEngagementService
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .models import DonorEngagementMessage, DonationCart, DonationCartItem
import logging
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from decimal import Decimal

# Initialize AI services
ai_service = DonationAIService()
unified_assistant = UnifiedAIAssistant()

logger = logging.getLogger(__name__)

def donate(request):
    if request.method == 'POST':
        # Handle AJAX donation submission
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                event_id = request.POST.get('event')
                donor_name = request.POST.get('donor_name')
                donor_email = request.POST.get('donor_email')
                amount = request.POST.get('amount')
                payment_method = request.POST.get('payment_method')
                message = request.POST.get('message', '')
                
                if not all([event_id, donor_name, donor_email, amount, payment_method]):
                    return JsonResponse({
                        'success': False,
                        'message': 'Please fill in all required fields.'
                    })
                
                try:
                    event = DonationEvent.objects.get(id=event_id)
                    amount = Decimal(amount)
                    if amount <= 0:
                        return JsonResponse({
                            'success': False,
                            'message': 'Amount must be greater than zero.'
                        })
                except (DonationEvent.DoesNotExist, ValueError):
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid event or amount.'
                    })
                
                # Create donation
                donation = Donation.objects.create(
                    event=event,
                    donor_name=donor_name,
                    donor_email=donor_email,
                    amount=amount,
                    payment_method=payment_method,
                    message=message,
                    status='completed'
                )
                
                # Update event current amount
                event.current_amount += amount
                event.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your donation!'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while processing your donation.'
                })
        
        # Handle regular form submission
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            
            # Check for potential fraud using AI
            fraud_probability = ai_service.predict_fraud_probability(donation)
            if fraud_probability > 0.8:  # High probability of fraud
                messages.warning(request, 'This donation has been flagged for review. Our team will verify it shortly.')
                donation.is_flagged = True
            
            donation.save()
            return redirect('thank_you')
    else:
        form = DonationForm()
    
    # Get all active donation events
    donation_events = DonationEvent.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-created_at')
    
    return render(request, 'donation2/donate.html', {
        'form': form,
        'donation_events': donation_events
    })

def thank_you(request):
    return render(request, 'donation2/thank_you.html')

def donation_list(request):
    donations = Donation.objects.all().order_by('-created_at')
    return render(request, 'donation2/donation_list.html', {'donations': donations})

def donation_report(request):
    start_date = request.GET.get('start_date', timezone.now().replace(month=timezone.now().month-1, day=1))
    end_date = request.GET.get('end_date', timezone.now())

    donations = Donation.objects.filter(date__gte=start_date, date__lte=end_date)
    total_donations = donations.aggregate(total_amount=models.Sum('amount'))  # `models` is now defined

    context = {
        'donations': donations,
        'total_donations': total_donations,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'donation2/donation_report.html', context)

def donation_receipt(request, donation_id):
    try:
        donation = Donation.objects.get(id=donation_id)
    except Donation.DoesNotExist:
        messages.error(request, "Donation not found.")
        return redirect('donation_list')

    context = {
        'donation': donation,
    }

    return render(request, 'donation2/donation_receipt.html', context)

def donation_event_detail(request, event_id):
    event = get_object_or_404(DonationEvent, id=event_id)
    # Calculate progress percent
    if event.target_amount > 0:
        progress_percent = min(100, round((event.current_amount / event.target_amount) * 100, 2))
    else:
        progress_percent = 0
    
    # Calculate fundraising duration in days
    fundraising_duration = (event.end_date - event.start_date).days
    
    # Get AI-powered insights
    sentiment_analysis = ai_service.analyze_event_sentiment(event.description)
    
    # Calculate percentages for sentiment analysis
    sentiment_analysis['confidence_percent'] = round(sentiment_analysis['confidence'] * 100, 1)
    sentiment_analysis['positive_percent'] = round(sentiment_analysis['detailed_scores']['positive'] * 100, 1)
    sentiment_analysis['neutral_percent'] = round(sentiment_analysis['detailed_scores']['neutral'] * 100, 1)
    sentiment_analysis['negative_percent'] = round(sentiment_analysis['detailed_scores']['negative'] * 100, 1)
    sentiment_analysis['emotional_intensity_percent'] = round(sentiment_analysis['emotional_intensity'] * 100, 1)
    sentiment_analysis['subjectivity_percent'] = round(sentiment_analysis['subjectivity'] * 100, 1)
    
    # Store sentiment analysis results in the event model
    event.sentiment_score = sentiment_analysis['polarity']
    event.sentiment_subjectivity = sentiment_analysis['subjectivity']
    event.save()
    
    impact_prediction = ai_service.predict_donation_impact(event)
    
    # Get personalized recommendations if user is authenticated
    recommendations = None
    if request.user.is_authenticated:
        recommendations = ai_service.get_donation_recommendations(request.user)
    
    return render(request, 'donation2/donation_event_detail.html', {
        'event': event,
        'progress_percent': progress_percent,
        'fundraising_duration': fundraising_duration,
        'sentiment_analysis': sentiment_analysis,
        'impact_prediction': impact_prediction,
        'recommendations': recommendations,
    })

def donation_categories(request):
    categories = DonationCategory.objects.all().order_by('-created_at')
    return render(request, 'donation2/donation_categories.html', {'categories': categories})

def add_donation_category(request):
    if request.method == 'POST':
        form = DonationCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('donation_categories')
    else:
        form = DonationCategoryForm()
    return render(request, 'donation2/add_donation_category.html', {'form': form})

def edit_donation_category(request, category_id):
    category = get_object_or_404(DonationCategory, id=category_id)
    if request.method == 'POST':
        form = DonationCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('donation_categories')
    else:
        form = DonationCategoryForm(instance=category)
    return render(request, 'donation2/edit_donation_category.html', {'form': form, 'category': category})

def delete_donation_category(request, category_id):
    category = get_object_or_404(DonationCategory, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('donation_categories')
    return render(request, 'donation2/delete_donation_category.html', {'category': category})

def donation_events(request):
    events = DonationEvent.objects.all().order_by('-created_at')
    return render(request, 'donation2/donation_events.html', {'events': events})

def add_donation_event(request):
    if request.method == 'POST':
        form = DonationEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, 'Event added successfully.')
            return redirect('donation_events')
    else:
        form = DonationEventForm()
    return render(request, 'donation2/add_donation_event.html', {'form': form})

def edit_donation_event(request, event_id):
    event = get_object_or_404(DonationEvent, id=event_id)
    if request.method == 'POST':
        form = DonationEventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('donation_events')
    else:
        form = DonationEventForm(instance=event)
    return render(request, 'donation2/edit_donation_event.html', {'form': form, 'event': event})

def delete_donation_event(request, event_id):
    """Delete a donation event (admin only)"""
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to delete donation events.")
    
    event = get_object_or_404(DonationEvent, id=event_id)
    
    if request.method == 'POST':
        event_name = event.title
        event.delete()
        messages.success(request, f'Donation event "{event_name}" has been deleted successfully.')
        return redirect('donation_events')
    
    return render(request, 'donation2/delete_donation_event_confirm.html', {
        'event': event
    })

@csrf_exempt
@require_http_methods(["POST"])
def chat_message(request):
    """Handle chat messages from the frontend"""
    try:
        message = request.POST.get('message', '').strip()
        if not message:
            return JsonResponse({
                'error': 'Message cannot be empty'
            }, status=400)

        user = request.user if request.user.is_authenticated else None
        
        # Process message using unified assistant
        response = unified_assistant.process_message(message, user)
        
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

def generate_donor_engagement_messages(request, event_id):
    """Generate and store AI-powered engagement messages for donors."""
    event = get_object_or_404(DonationEvent, id=event_id)
    engagement_service = DonorEngagementService()
    
    # Get recent donations
    recent_donations = event.donations.filter(created_at__gte=datetime.now() - timedelta(days=30))
    
    for donation in recent_donations:
        # Generate thank you message
        impact_details = f"Your donation of ${donation.amount} helps us reach our goal of ${event.target_amount}"
        thank_you_message = engagement_service.generate_thank_you_message(
            donation.donor.username,
            donation.amount,
            event.title,
            impact_details
        )
        
        DonorEngagementMessage.objects.create(
            donor=donation.donor,
            event=event,
            message_type='thank_you',
            message_content=thank_you_message
        )
        
        # Generate impact report
        impact_report = engagement_service.generate_impact_report(event, donation)
        DonorEngagementMessage.objects.create(
            donor=donation.donor,
            event=event,
            message_type='impact_report',
            message_content=impact_report
        )
    
    # Generate re-engagement suggestions for past donors
    past_donors = User.objects.filter(donations__event=event).distinct()
    for donor in past_donors:
        reengagement_message = engagement_service.generate_reengagement_suggestion(donor, event)
        DonorEngagementMessage.objects.create(
            donor=donor,
            event=event,
            message_type='reengagement',
            message_content=reengagement_message
        )
    
    # Generate anniversary messages
    for donation in event.donations.all():
        days_since_donation = (datetime.now() - donation.created_at).days
        if days_since_donation % 30 == 0:  # Monthly anniversary
            anniversary_message = engagement_service.generate_anniversary_message(
                donation.donor,
                event,
                days_since_donation
            )
            DonorEngagementMessage.objects.create(
                donor=donation.donor,
                event=event,
                message_type='anniversary',
                message_content=anniversary_message
            )
    
    return JsonResponse({'status': 'success', 'message': 'Engagement messages generated successfully'})

@login_required
def get_donor_messages(request):
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to access this page.")
    
    messages_list = DonorEngagementMessage.objects.all().order_by('-created_at')
    return render(request, 'donation2/donor_messages.html', {'messages': messages_list})

@login_required
def donation_analytics(request):
    """Comprehensive analytics for donation events and campaigns"""
    if not request.user.is_staff:
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get filter parameters
    event_id = request.GET.get('event_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base queryset for donation events
    events = DonationEvent.objects.all().order_by('-created_at')
    
    # Filter by specific event if provided
    if event_id:
        events = events.filter(id=event_id)
    
    # Filter by date range if provided
    if start_date:
        events = events.filter(start_date__gte=start_date)
    if end_date:
        events = events.filter(end_date__lte=end_date)
    
    analytics_data = []
    
    for event in events:
        # Get donations for this event - include all statuses for now
        donations = Donation.objects.filter(event=event)
        
        # Debug: Print donation count for this event
        print(f"Event: {event.title}, Donations found: {donations.count()}")
        for donation in donations:
            print(f"  - Donation: {donation.donor_name}, Amount: {donation.amount}, Status: {donation.status}")
        
        # Calculate analytics
        total_donated = donations.aggregate(total=models.Sum('amount'))['total'] or 0
        donor_count = donations.count()
        
        # Calculate target progress
        if event.target_amount > 0:
            progress_percent = min(100, round((total_donated / event.target_amount) * 100, 2))
        else:
            progress_percent = 0
        
        # Check if target is reached
        target_reached = total_donated >= event.target_amount
        
        # Calculate date reached (when target was achieved)
        date_reached = None
        if target_reached and event.target_amount > 0:
            cumulative_amount = 0
            for donation in donations.order_by('created_at'):
                cumulative_amount += donation.amount
                if cumulative_amount >= event.target_amount:
                    date_reached = donation.created_at
                    break
        
        # Calculate average donation amount
        avg_donation = 0
        if donor_count > 0:
            avg_donation = total_donated / donor_count
        
        # Get donation method breakdown
        payment_methods = donations.values('payment_method').annotate(
            count=models.Count('id'),
            total=models.Sum('amount')
        )
        
        # Get daily donation trends
        daily_donations = donations.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=models.Count('id'),
            total=models.Sum('amount')
        ).order_by('day')
        
        # Calculate days remaining or completed
        today = timezone.now().date()
        if event.end_date >= today:
            days_remaining = (event.end_date - today).days
            days_completed = (today - event.start_date).days
        else:
            days_remaining = 0
            days_completed = (event.end_date - event.start_date).days
        
        # Calculate completion rate
        total_days = (event.end_date - event.start_date).days
        if total_days > 0:
            completion_rate = min(100, round((days_completed / total_days) * 100, 2))
        else:
            completion_rate = 0
        
        analytics_data.append({
            'event': event,
            'total_donated': total_donated,
            'donor_count': donor_count,
            'progress_percent': progress_percent,
            'target_reached': target_reached,
            'date_reached': date_reached,
            'avg_donation': avg_donation,
            'payment_methods': payment_methods,
            'daily_donations': daily_donations,
            'days_remaining': days_remaining,
            'days_completed': days_completed,
            'completion_rate': completion_rate,
            'total_days': total_days,
        })
    
    # Overall statistics - include all donations regardless of status
    all_donations = Donation.objects.all()
    if start_date:
        all_donations = all_donations.filter(created_at__date__gte=start_date)
    if end_date:
        all_donations = all_donations.filter(created_at__date__lte=end_date)
    
    overall_stats = {
        'total_events': events.count(),
        'total_donations': all_donations.count(),
        'total_amount': all_donations.aggregate(total=models.Sum('amount'))['total'] or 0,
        'avg_donation': all_donations.aggregate(avg=models.Avg('amount'))['avg'] or 0,
        'active_events': events.filter(is_active=True).count(),
        'completed_events': events.filter(end_date__lt=today).count(),
    }
    
    context = {
        'analytics_data': analytics_data,
        'overall_stats': overall_stats,
        'events': events,
        'selected_event_id': event_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'donation2/donation_analytics.html', context)

@login_required
def donation_analytics_api(request):
    """JSON API endpoint for donation analytics"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get filter parameters
    event_id = request.GET.get('event_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base queryset for donation events
    events = DonationEvent.objects.all().order_by('-created_at')
    
    # Filter by specific event if provided
    if event_id:
        events = events.filter(id=event_id)
    
    # Filter by date range if provided
    if start_date:
        events = events.filter(start_date__gte=start_date)
    if end_date:
        events = events.filter(end_date__lte=end_date)
    
    analytics_data = []
    
    for event in events:
        # Get donations for this event
        donations = Donation.objects.filter(event=event, status='completed')
        
        # Calculate analytics
        total_donated = donations.aggregate(total=models.Sum('amount'))['total'] or 0
        donor_count = donations.count()
        
        # Calculate target progress
        if event.target_amount > 0:
            progress_percent = min(100, round((total_donated / event.target_amount) * 100, 2))
        else:
            progress_percent = 0
        
        # Check if target is reached
        target_reached = total_donated >= event.target_amount
        
        # Calculate date reached (when target was achieved)
        date_reached = None
        if target_reached and event.target_amount > 0:
            cumulative_amount = 0
            for donation in donations.order_by('created_at'):
                cumulative_amount += donation.amount
                if cumulative_amount >= event.target_amount:
                    date_reached = donation.created_at.isoformat()
                    break
        
        # Calculate average donation amount
        avg_donation = 0
        if donor_count > 0:
            avg_donation = float(total_donated / donor_count)
        
        # Get donation method breakdown
        payment_methods = list(donations.values('payment_method').annotate(
            count=models.Count('id'),
            total=models.Sum('amount')
        ))
        
        # Convert Decimal to float for JSON serialization
        for method in payment_methods:
            method['total'] = float(method['total'])
        
        # Get daily donation trends
        daily_donations = list(donations.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=models.Count('id'),
            total=models.Sum('amount')
        ).order_by('day'))
        
        # Convert Decimal to float for JSON serialization
        for day in daily_donations:
            day['total'] = float(day['total'])
        
        # Calculate days remaining or completed
        today = timezone.now().date()
        if event.end_date >= today:
            days_remaining = (event.end_date - today).days
            days_completed = (today - event.start_date).days
        else:
            days_remaining = 0
            days_completed = (event.end_date - event.start_date).days
        
        # Calculate completion rate
        total_days = (event.end_date - event.start_date).days
        if total_days > 0:
            completion_rate = min(100, round((days_completed / total_days) * 100, 2))
        else:
            completion_rate = 0
        
        analytics_data.append({
            'event_id': event.id,
            'event_title': event.title,
            'event_description': event.description,
            'category': event.category.name,
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat(),
            'target_amount': float(event.target_amount),
            'total_donated': float(total_donated),
            'donor_count': donor_count,
            'progress_percent': progress_percent,
            'target_reached': target_reached,
            'date_reached': date_reached,
            'avg_donation': avg_donation,
            'payment_methods': payment_methods,
            'daily_donations': daily_donations,
            'days_remaining': days_remaining,
            'days_completed': days_completed,
            'completion_rate': completion_rate,
            'total_days': total_days,
            'is_active': event.is_active,
        })
    
    # Overall statistics - include all donations regardless of status
    all_donations = Donation.objects.all()
    if start_date:
        all_donations = all_donations.filter(created_at__date__gte=start_date)
    if end_date:
        all_donations = all_donations.filter(created_at__date__lte=end_date)
    
    overall_stats = {
        'total_events': events.count(),
        'total_donations': all_donations.count(),
        'total_amount': float(all_donations.aggregate(total=models.Sum('amount'))['total'] or 0),
        'avg_donation': float(all_donations.aggregate(avg=models.Avg('amount'))['avg'] or 0),
        'active_events': events.filter(is_active=True).count(),
        'completed_events': events.filter(end_date__lt=today).count(),
    }
    
    return JsonResponse({
        'analytics_data': analytics_data,
        'overall_stats': overall_stats,
        'filters': {
            'event_id': event_id,
            'start_date': start_date,
            'end_date': end_date,
        }
    })

@login_required
def get_or_create_cart(request):
    """Get or create a cart for the current user"""
    cart, created = DonationCart.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'is_active': True}
    )
    return cart

@login_required
def add_to_cart(request, event_id):
    """Add a donation event to the user's cart"""
    if request.method == 'POST':
        event = get_object_or_404(DonationEvent, id=event_id)
        amount = request.POST.get('amount')
        message = request.POST.get('message', '')
        
        if not amount:
            messages.error(request, 'Please specify an amount for your donation.')
            return redirect('donation_event_detail', event_id=event_id)
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Donation amount must be greater than zero.')
                return redirect('donation_event_detail', event_id=event_id)
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
            return redirect('donation_event_detail', event_id=event_id)
        
        cart = get_or_create_cart(request)
        
        # Check if event is already in cart
        cart_item, created = DonationCartItem.objects.get_or_create(
            cart=cart,
            event=event,
            defaults={
                'amount': amount,
                'message': message
            }
        )
        
        if not created:
            # Update existing item
            cart_item.amount = amount
            cart_item.message = message
            cart_item.save()
            messages.success(request, f'Updated {event.title} in your cart - ${amount}')
        else:
            messages.success(request, f'Added {event.title} to your cart - ${amount}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Added {event.title} to cart',
                'cart_count': cart.get_total_items(),
                'cart_total': float(cart.get_total_amount())
            })
        
        return redirect('view_cart')
    
    return redirect('donation_event_detail', event_id=event_id)

@login_required
def view_cart(request):
    """View the user's donation cart"""
    cart = get_or_create_cart(request)
    cart_items = cart.cart_items.all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_amount': cart.get_total_amount(),
        'total_items': cart.get_total_items(),
    }
    
    return render(request, 'donation2/cart.html', context)

@login_required
def update_cart_item(request, item_id):
    """Update a cart item's amount or message"""
    if request.method == 'POST':
        cart_item = get_object_or_404(DonationCartItem, id=item_id, cart__user=request.user)
        amount = request.POST.get('amount')
        message = request.POST.get('message', '')
        
        if not amount:
            messages.error(request, 'Please specify an amount.')
            return redirect('view_cart')
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero.')
                return redirect('view_cart')
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
            return redirect('view_cart')
        
        cart_item.amount = amount
        cart_item.message = message
        cart_item.save()
        
        messages.success(request, f'Updated {cart_item.event.title} - ${amount}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Cart item updated',
                'cart_total': float(cart_item.cart.get_total_amount())
            })
        
        return redirect('view_cart')
    
    return redirect('view_cart')

@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    cart_item = get_object_or_404(DonationCartItem, id=item_id, cart__user=request.user)
    event_title = cart_item.event.title
    cart_item.delete()
    
    messages.success(request, f'Removed {event_title} from your cart.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = get_or_create_cart(request)
        return JsonResponse({
            'success': True,
            'message': f'Removed {event_title} from cart',
            'cart_count': cart.get_total_items(),
            'cart_total': float(cart.get_total_amount())
        })
    
    return redirect('view_cart')

@login_required
def clear_cart(request):
    """Clear all items from the cart"""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        cart.clear_cart()
        messages.success(request, 'Your cart has been cleared.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Cart cleared',
                'cart_count': 0,
                'cart_total': 0.0
            })
    
    return redirect('view_cart')

@login_required
def checkout_cart(request):
    """Checkout process for cart items"""
    cart = get_or_create_cart(request)
    cart_items = cart.cart_items.all()
    
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('donation_events')
    
    if request.method == 'POST':
        # Process all donations in cart
        donor_name = request.POST.get('donor_name')
        donor_email = request.POST.get('donor_email')
        payment_method = request.POST.get('payment_method')
        
        if not all([donor_name, donor_email, payment_method]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'donation2/checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'total_amount': cart.get_total_amount()
            })
        
        # Create donations for each cart item
        created_donations = []
        for item in cart_items:
            donation = Donation.objects.create(
                event=item.event,
                donor_name=donor_name,
                donor_email=donor_email,
                amount=item.amount,
                payment_method=payment_method,
                status='completed',
                message=item.message
            )
            created_donations.append(donation)
            
            # Update event current amount
            item.event.current_amount += item.amount
            item.event.save()
        
        # Clear the cart
        cart.clear_cart()
        
        messages.success(request, f'Successfully donated ${cart.get_total_amount()} across {len(created_donations)} events!')
        
        # Redirect to thank you page or receipt
        return redirect('donation_success', donation_ids=','.join(str(d.id) for d in created_donations))
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_amount': cart.get_total_amount(),
        'total_items': cart.get_total_items(),
    }
    
    return render(request, 'donation2/checkout.html', context)

@login_required
def donation_success(request, donation_ids):
    """Success page after completing donations"""
    donation_id_list = donation_ids.split(',')
    donations = Donation.objects.filter(id__in=donation_id_list, donor_email=request.user.email)
    
    context = {
        'donations': donations,
        'total_amount': sum(d.amount for d in donations),
        'donation_count': len(donations)
    }
    
    return render(request, 'donation2/donation_success.html', context)

@login_required
def get_cart_count(request):
    """Get cart count for AJAX requests (for navbar)"""
    cart = get_or_create_cart(request)
    return JsonResponse({
        'cart_count': cart.get_total_items(),
        'cart_total': float(cart.get_total_amount())
    })

@login_required
def donation_history(request):
    """View user's donation history with search and filtering"""
    # Get search parameters
    search_month = request.GET.get('month', '')
    search_year = request.GET.get('year', '')
    search_event = request.GET.get('event', '')
    
    # Get user's donations
    donations = Donation.objects.filter(donor_email=request.user.email).order_by('-created_at')
    
    # Apply filters
    if search_month:
        donations = donations.filter(created_at__month=search_month)
    
    if search_year:
        donations = donations.filter(created_at__year=search_year)
    
    if search_event:
        donations = donations.filter(event__title__icontains=search_event)
    
    # Get unique events for filter dropdown
    user_events = Donation.objects.filter(donor_email=request.user.email).values_list('event__title', flat=True).distinct()
    
    # Calculate statistics
    total_donated = donations.aggregate(total=models.Sum('amount'))['total'] or 0
    total_donations = donations.count()
    avg_donation = donations.aggregate(avg=models.Avg('amount'))['avg'] or 0
    
    # Get months and years for filter dropdowns
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    # Get years from donation dates
    years = []
    user_donations = Donation.objects.filter(donor_email=request.user.email)
    for donation in user_donations:
        year = donation.created_at.year
        if year not in years:
            years.append(year)
    years.sort(reverse=True)
    
    context = {
        'donations': donations,
        'total_donated': total_donated,
        'total_donations': total_donations,
        'avg_donation': avg_donation,
        'months': months,
        'years': years,
        'user_events': user_events,
        'search_month': search_month,
        'search_year': search_year,
        'search_event': search_event,
    }
    
    return render(request, 'donation2/donation_history.html', context)

@login_required
def donation_receipt_detail(request, donation_id):
    """View detailed receipt for a specific donation"""
    donation = get_object_or_404(Donation, id=donation_id, donor_email=request.user.email)
    
    context = {
        'donation': donation,
    }
    
    return render(request, 'donation2/donation_receipt_detail.html', context)

@login_required
def download_receipt_pdf(request, donation_id):
    """Download donation receipt as PDF"""
    donation = get_object_or_404(Donation, id=donation_id, donor_email=request.user.email)
    
    # Generate PDF receipt
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from io import BytesIO
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width/2, height-1*inch, "Donation Receipt")
    
    # Organization info
    p.setFont("Helvetica", 12)
    p.drawString(1*inch, height-1.5*inch, "Charity Platform")
    p.drawString(1*inch, height-1.7*inch, "Making a difference one contribution at a time")
    
    # Receipt details
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, height-2.5*inch, "Receipt Details:")
    
    p.setFont("Helvetica", 12)
    y_position = height-2.8*inch
    
    details = [
        ("Receipt ID:", f"#{donation.id:06d}"),
        ("Date:", donation.created_at.strftime("%B %d, %Y")),
        ("Time:", donation.created_at.strftime("%I:%M %p")),
        ("Donor Name:", donation.donor_name),
        ("Donor Email:", donation.donor_email),
        ("Event:", donation.event.title),
        ("Amount:", f"${donation.amount:,.2f}"),
        ("Payment Method:", donation.get_payment_method_display()),
        ("Status:", donation.get_status_display()),
    ]
    
    for label, value in details:
        p.drawString(1*inch, y_position, label)
        p.drawString(3*inch, y_position, value)
        y_position -= 0.3*inch
    
    # Message if exists
    if donation.message:
        p.drawString(1*inch, y_position-0.3*inch, "Message:")
        p.drawString(1*inch, y_position-0.6*inch, donation.message)
    
    # Footer
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, 1*inch, "Thank you for your generous donation!")
    p.drawCentredString(width/2, 0.8*inch, "Your contribution makes a real difference in our community.")
    
    p.showPage()
    p.save()
    
    # Get PDF content
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="donation_receipt_{donation.id}.pdf"'
    response.write(pdf)
    
    return response
