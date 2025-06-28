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
from .models import DonorEngagementMessage
import logging
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

# Initialize AI services
ai_service = DonationAIService()
unified_assistant = UnifiedAIAssistant()

logger = logging.getLogger(__name__)

def donate(request):
    if request.method == 'POST':
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
    return render(request, 'donation2/donate.html', {'form': form})

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
        form = DonationEventForm(request.POST)
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
        form = DonationEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('donation_events')
    else:
        form = DonationEventForm(instance=event)
    return render(request, 'donation2/edit_donation_event.html', {'form': form, 'event': event})

def delete_donation_event(request, event_id):
    event = get_object_or_404(DonationEvent, id=event_id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('donation_events')
    return render(request, 'donation2/delete_donation_event.html', {'event': event})

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
    """Get all engagement messages for the current user."""
    try:
        messages = DonorEngagementMessage.objects.filter(
            donor=request.user,
            is_sent=False
        ).order_by('-created_at')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'messages': [
                    {
                        'type': message.get_message_type_display(),
                        'content': message.message_content,
                        'event': message.event.title,
                        'event_id': message.event.id,
                        'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    for message in messages
                ]
            })
        
        # For regular page load, render the HTML template
        return render(request, 'donation2/donor_messages.html', {
            'messages': messages
        })
        
    except Exception as e:
        logger.error(f"Error in get_donor_messages: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Failed to load messages. Please try again later.',
                'messages': []  # Return empty messages array for AJAX requests
            }, status=500)
        messages.error(request, 'Failed to load messages. Please try again later.')
        return redirect('donation_events')
