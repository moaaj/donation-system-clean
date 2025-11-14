from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.utils import timezone
from decimal import Decimal
from .models import WaqafAsset, Contributor, Contribution, FundDistribution, WaqafCart, WaqafCartItem
from .forms import WaqafContributionForm, ContributorForm, WaqafAssetForm
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
import io
from django.db.models import Q
import csv
from django.contrib.auth.decorators import login_required
from myapp.forms import DonationEventForm
from myapp.models import DonationEvent
from .ai_services import WaqafAIService
from django import forms
from .decorators import waqaf_admin_required

def calculate_fund_status():
    total_contributions = Contribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    total_distributions = FundDistribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    balance = total_contributions - total_distributions
    return {
        'total_contributions': total_contributions,
        'total_distributions': total_distributions,
        'balance': balance
    }

@waqaf_admin_required
def waqaf_dashboard(request):
    # Get the total number of assets and total value (excluding archived)
    total_assets = WaqafAsset.objects.filter(is_archived=False).count()
    total_value = WaqafAsset.objects.filter(is_archived=False).aggregate(models.Sum('current_value'))['current_value__sum'] or 0

    # Get the total number of contributors and total amount contributed
    total_contributors = Contributor.objects.count()
    total_contributed = Contribution.objects.filter(payment_status='COMPLETED').aggregate(models.Sum('amount'))['amount__sum'] or 0

        # Get assets with available slots (excluding archived)
    available_assets = WaqafAsset.objects.filter(slots_available__gt=0, is_archived=False)

    # Get contribution data for charts
    contributions_by_asset = Contribution.objects.values('asset__name').annotate(
        total_amount=models.Sum('amount'),
        total_slots=models.Sum('number_of_slots')
    ).order_by('-total_amount')[:5]

    # Get monthly contribution data
    monthly_contributions = Contribution.objects.annotate(
        month=models.functions.TruncMonth('date_contributed')
    ).values('month').annotate(
        total=models.Sum('amount')
    ).order_by('month')[:12]
    
    # Convert datetime objects to strings for JSON serialization
    monthly_contributions = [
        {
            'month': item['month'].strftime('%Y-%m-%d'),
            'total': float(item['total'])
        }
        for item in monthly_contributions
    ]
    
    # If no monthly data, create sample data for the last 6 months
    if not monthly_contributions:
        from datetime import datetime, timedelta
        from django.utils import timezone
        sample_data = []
        for i in range(6):
            date = timezone.now() - timedelta(days=30*i)
            sample_data.append({
                'month': date.strftime('%Y-%m-%d'),
                'total': 0
            })
        monthly_contributions = sample_data

    # Get payment status distribution
    payment_status = Contribution.objects.values('payment_status').annotate(
        count=models.Count('id')
    )
    
    # If no payment status data, create sample data
    if not payment_status:
        payment_status = [
            {'payment_status': 'COMPLETED', 'count': 0},
            {'payment_status': 'PENDING', 'count': 0},
            {'payment_status': 'FAILED', 'count': 0}
        ]

    # Calculate fund status
    fund_status = calculate_fund_status()

    # In waqaf_dashboard view, after getting available_assets
    assets_progress = []
    for asset in available_assets:
        filled_slots = asset.total_slots - asset.slots_available
        progress_percent = (filled_slots / asset.total_slots * 100) if asset.total_slots > 0 else 0
        assets_progress.append({
            'id': asset.id,
            'name': asset.name,
            'description': asset.description,
            'target_amount': asset.target_amount,
            'current_value': asset.current_value,
            'total_slots': asset.total_slots,
            'slots_available': asset.slots_available,
            'filled_slots': filled_slots,
            'progress_percent': progress_percent,
        })

    certificate_id = request.session.pop('certificate_id', None)
    
    # Get count of archived assets for admin reference
    archived_count = WaqafAsset.objects.filter(is_archived=True).count()
    
    context = {
        'total_assets': total_assets,
        'total_value': total_value,
        'total_contributors': total_contributors,
        'total_contributed': total_contributed,
        'available_assets': available_assets,
        'contributions_by_asset': list(contributions_by_asset),
        'monthly_contributions': list(monthly_contributions),
        'payment_status': list(payment_status),
        'fund_status': fund_status,
        'certificate_id': certificate_id,
        'assets_progress': assets_progress,
        'archived_count': archived_count,
    }

    return render(request, 'waqaf/waqaf_dashboard.html', context)

def waqaf(request):
    # Check if user is admin
    is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    
    if is_admin:
        # Admin view - show all assets with management options (excluding archived)
        all_assets = WaqafAsset.objects.filter(is_archived=False)
        
        # Calculate progress for each asset
        assets_progress = []
        for asset in all_assets:
            filled_slots = asset.total_slots - asset.slots_available
            progress_percent = (filled_slots / asset.total_slots * 100) if asset.total_slots > 0 else 0
            contributions_count = Contribution.objects.filter(asset=asset).count()
            
            assets_progress.append({
                'id': asset.id,
                'name': asset.name,
                'description': asset.description,
                'target_amount': asset.target_amount,
                'current_value': asset.current_value,
                'total_slots': asset.total_slots,
                'slots_available': asset.slots_available,
                'slot_price': asset.slot_price,
                'progress_percent': progress_percent,
                'filled_slots': filled_slots,
                'contributions_count': contributions_count
            })
        
        # Get count of archived assets for admin reference
        archived_count = WaqafAsset.objects.filter(is_archived=True).count()
        
        context = {
            'is_admin': True,
            'assets_progress': assets_progress,
            'total_assets': all_assets.count(),
            'total_contributions': Contribution.objects.count(),
            'total_amount': Contribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0,
            'archived_count': archived_count
        }
    else:
        # Regular user view - show available assets with cart functionality (excluding archived)
        available_assets = WaqafAsset.objects.filter(slots_available__gt=0, is_archived=False)
        
        # Calculate progress for each asset
        assets_progress = []
        for asset in available_assets:
            filled_slots = asset.total_slots - asset.slots_available
            progress_percent = (filled_slots / asset.total_slots * 100) if asset.total_slots > 0 else 0
            assets_progress.append({
                'id': asset.id,
                'name': asset.name,
                'description': asset.description,
                'target_amount': asset.target_amount,
                'current_value': asset.current_value,
                'total_slots': asset.total_slots,
                'slots_available': asset.slots_available,
                'slot_price': asset.slot_price,
                'progress_percent': progress_percent,
                'filled_slots': filled_slots
            })
        
        context = {
            'is_admin': False,
            'assets_progress': assets_progress,
            'total_assets': available_assets.count()
        }
    
    return render(request, 'waqaf/waqaf.html', context)

def contribute_waqaf(request):
    if request.method == 'POST':
        contributor_form = ContributorForm(request.POST)
        contribution_form = WaqafContributionForm(request.POST)
        
        if contributor_form.is_valid() and contribution_form.is_valid():
            # Get or create contributor
            email = contributor_form.cleaned_data['email']
            contributor = Contributor.objects.filter(email=email).first()
            
            if contributor:
                # Update existing contributor's information
                for field, value in contributor_form.cleaned_data.items():
                    setattr(contributor, field, value)
                contributor.save()
            else:
                # Create new contributor
                contributor = contributor_form.save()
            
            # Create contribution
            contribution = contribution_form.save(commit=False)
            contribution.contributor = contributor
            
            # Get the asset and validate it exists
            asset = contribution.asset
            if not asset:
                messages.error(request, 'Please select a valid waqaf asset.')
                # Get available assets for the template (excluding archived)
                available_assets = WaqafAsset.objects.filter(slots_available__gt=0, is_archived=False)
                return render(request, 'waqaf/contribute.html', {
                    'contributor_form': contributor_form,
                    'contribution_form': contribution_form,
                    'available_assets': available_assets
                })
            
            # Validate slots availability
            if contribution.number_of_slots > asset.slots_available:
                messages.error(request, f'Only {asset.slots_available} slots available for this asset.')
                # Get available assets for the template (excluding archived)
                available_assets = WaqafAsset.objects.filter(slots_available__gt=0, is_archived=False)
                return render(request, 'waqaf/contribute.html', {
                    'contributor_form': contributor_form,
                    'contribution_form': contribution_form,
                    'available_assets': available_assets
                })
            
            # Calculate amount based on number of slots and asset price
            contribution.amount = contribution.number_of_slots * asset.slot_price
            
            # Set payment status to COMPLETED automatically
            contribution.payment_status = 'COMPLETED'
            
            contribution.save()
            
            # Always generate certificate after every contribution
            request.session['certificate_id'] = contribution.id
            
            # For anonymous users, redirect to homepage; for authenticated users, redirect to dashboard
            if request.user.is_authenticated:
                return redirect('waqaf:waqaf_dashboard')
            else:
                messages.success(request, 'Thank you for your waqaf contribution! Your certificate is ready for download.')
                return redirect('waqaf:waqaf_success')
    else:
        contributor_form = ContributorForm()
        contribution_form = WaqafContributionForm()
    
    # Get available assets for the template (moved outside if/else to ensure it's always defined) (excluding archived)
    available_assets = WaqafAsset.objects.filter(slots_available__gt=0, is_archived=False)
    if not available_assets.exists():
        messages.warning(request, 'No waqaf assets are currently available for contribution.')

    return render(request, 'waqaf/contribute.html', {
        'contributor_form': contributor_form,
        'contribution_form': contribution_form,
        'available_assets': available_assets
    })

def asset_detail(request, asset_id):
    asset = get_object_or_404(WaqafAsset, id=asset_id, is_archived=False)
    contributions = Contribution.objects.filter(asset=asset).order_by('-date_contributed')
    
    # Calculate filled slots
    filled_slots = asset.total_slots - asset.slots_available
    filled_percentage = (filled_slots / asset.total_slots * 100) if asset.total_slots > 0 else 0
    
    context = {
        'asset': asset,
        'contributions': contributions,
        'filled_slots': filled_slots,
        'filled_percentage': filled_percentage,
    }
    
    return render(request, 'waqaf/asset_detail.html', context)

@login_required
def archive_asset(request, asset_id):
    """Archive a waqaf asset (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        asset = get_object_or_404(WaqafAsset, id=asset_id)
        asset.archive(user=request.user)
        return JsonResponse({
            'success': True, 
            'message': f'Asset "{asset.name}" has been archived successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Failed to archive asset: {str(e)}'
        }, status=500)

@login_required
def unarchive_asset(request, asset_id):
    """Unarchive a waqaf asset (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        asset = get_object_or_404(WaqafAsset, id=asset_id)
        asset.unarchive()
        return JsonResponse({
            'success': True, 
            'message': f'Asset "{asset.name}" has been unarchived successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Failed to unarchive asset: {str(e)}'
        }, status=500)

@login_required
def view_archived_assets(request):
    """View archived waqaf assets (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Permission denied')
        return redirect('waqaf:waqaf')
    
    archived_assets = WaqafAsset.objects.filter(is_archived=True).order_by('-archived_at')
    
    # Calculate progress for each archived asset
    for asset in archived_assets:
        filled_slots = asset.total_slots - asset.slots_available
        asset.progress_percent = (filled_slots / asset.total_slots * 100) if asset.total_slots > 0 else 0
        asset.filled_slots = filled_slots
    
    context = {
        'archived_assets': archived_assets,
        'is_admin': True,
        'total_archived': archived_assets.count(),
    }
    
    return render(request, 'waqaf/archived_assets.html', context)

def download_certificate(request, contribution_id):
    contribution = Contribution.objects.get(id=contribution_id)
    # Use the amount for this specific contribution
    contribution_amount = contribution.amount

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(600, 400))

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(300, 370, "MASJID TAMAN PULAI INDAH (MTPI)")

    # Title in gold color
    p.setFont("Helvetica-Bold", 32)
    p.setFillColorRGB(0.85, 0.65, 0.13)  # Gold color
    p.drawCentredString(300, 330, "WAQF CERTIFICATE")
    p.setFillColorRGB(0, 0, 0)

    # Certification text
    p.setFont("Helvetica", 12)
    p.drawCentredString(300, 300, "This is to certify that")
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(300, 285, f"{contribution.contributor.name}")
    p.setFont("Helvetica", 12)
    p.drawCentredString(300, 270, "is the holder of")
    p.setFont("Helvetica-Bold", 13)
    p.drawCentredString(300, 255, "WAQF CERTIFICATE SHARE FOR DEVELOPMENT LOT")
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(300, 240, "Masjid Taman Pulai Indah (MTPI)")
    
    # Contribution details
    p.setFont("Helvetica", 10)
    p.drawCentredString(300, 220, f"Asset: {contribution.asset.name}")
    p.drawCentredString(300, 210, f"Slots: {contribution.number_of_slots} | Price per Slot: RM{contribution.asset.slot_price:.2f}")

    # Amount badge (simple red circle)
    p.setFillColorRGB(1, 0, 0)
    p.circle(120, 200, 30, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(120, 195, f"RM{contribution_amount:.2f}")
    p.setFillColorRGB(0, 0, 0)

    # Date
    p.setFont("Helvetica", 12)
    p.drawString(80, 170, f"Date of Waqf: {contribution.date_contributed.strftime('%Y-%m-%d')}")

    # Footer (Chairman)
    p.setFont("Helvetica", 12)
    p.drawString(420, 120, "_________________________")
    p.drawString(420, 105, "Chairman")
    p.drawString(420, 90, "Masjid Taman Pulai Indah")

    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="waqaf_certificate_{contribution.id}.pdf"'
    return response

def waqaf_report(request):
    query = request.GET.get('q', '')
    contributions = Contribution.objects.all()
    if query:
        contributions = contributions.filter(
            Q(contributor__name__icontains=query) |
            Q(asset__name__icontains=query) |
            Q(payment_reference__icontains=query)
        )
    # CSV export
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=\"waqaf_pledges.csv\"'
        writer = csv.writer(response)
        writer.writerow(['Contributor', 'Asset', 'Slots', 'Amount', 'Status', 'Date'])
        for c in contributions:
            writer.writerow([c.contributor.name, c.asset.name, c.number_of_slots, c.amount, c.payment_status, c.date_contributed])
        return response
    return render(request, 'waqaf/waqaf_report.html', {'contributions': contributions, 'query': query})

def generate_qr_code(request, event_id):
    event = DonationEvent.objects.get(id=event_id)
    event.generate_qr_code()
    event.save()
    return redirect('waqaf:waqaf_dashboard')

@login_required
def add_donation_event(request):
    if request.method == 'POST':
        form = DonationEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            # QR code is generated and saved in the model's save() method
            event.save()
            messages.success(request, 'Event added successfully.')
            return redirect('donation_events')
    else:
        form = DonationEventForm()
    return render(request, 'myapp/add_donation_event.html', {'form': form})

@login_required
def waqaf_ai_analytics(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('waqaf:waqaf_dashboard')
    
    try:
        # Get analytics data
        analytics_data = WaqafAIService.get_analytics()
        
        # Get asset predictions for all assets
        assets = WaqafAsset.objects.all()
        asset_predictions = []
        for asset in assets:
            prediction = WaqafAIService.predict_asset_value(asset.id)
            asset_predictions.append({
                'asset': asset,
                'prediction': prediction
            })
        
        return render(request, 'waqaf/ai_analytics.html', {
            'asset_predictions': asset_predictions,
            'contribution_patterns': analytics_data.get('contribution_patterns', {}),
            'asset_recommendations': analytics_data.get('asset_recommendations', []),
            'donor_engagement': analytics_data.get('donor_engagement', []),
            'overall_stats': analytics_data.get('overall_stats', {})
        })
        
    except Exception as e:
        messages.error(request, f"Error loading analytics: {str(e)}")
        return redirect('waqaf:waqaf_dashboard')

# Waqaf Cart Views
def get_or_create_waqaf_cart(request):
    """Get or create a cart for the current user (supports anonymous users)"""
    if request.user.is_authenticated:
        # For authenticated users, use database cart
        cart, created = WaqafCart.objects.get_or_create(user=request.user)
        return cart
    else:
        # For anonymous users, use session-based cart
        if 'waqaf_cart' not in request.session:
            request.session['waqaf_cart'] = []
        return request.session['waqaf_cart']

def add_to_waqaf_cart(request, asset_id):
    """Add a waqaf asset to cart (supports anonymous users)"""
    if request.method == 'POST':
        try:
            asset = get_object_or_404(WaqafAsset, id=asset_id)
            cart = get_or_create_waqaf_cart(request)
            
            # Get number of slots from form
            number_of_slots = int(request.POST.get('number_of_slots', 1))
            
            if number_of_slots <= 0:
                return JsonResponse({'success': False, 'message': 'Number of slots must be greater than 0'})
            
            if number_of_slots > asset.slots_available:
                return JsonResponse({'success': False, 'message': f'Only {asset.slots_available} slots available'})
            
            if request.user.is_authenticated:
                # For authenticated users, use database cart
                cart_item, created = WaqafCartItem.objects.get_or_create(
                    cart=cart,
                    asset=asset,
                    defaults={'number_of_slots': number_of_slots}
                )
                
                if not created:
                    # Update existing item
                    cart_item.number_of_slots += number_of_slots
                    cart_item.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Added {number_of_slots} slot(s) of {asset.name} to cart',
                    'cart_count': cart.total_slots
                })
            else:
                # For anonymous users, use session-based cart
                cart_item = {
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'number_of_slots': number_of_slots,
                    'slot_price': float(asset.slot_price),
                    'total_amount': float(number_of_slots * asset.slot_price),
                    'added_at': timezone.now().isoformat()
                }
                
                # Check if asset is already in cart
                existing_index = None
                for i, item in enumerate(cart):
                    if item['asset_id'] == asset.id:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    # Update existing item
                    cart[existing_index]['number_of_slots'] += number_of_slots
                    cart[existing_index]['total_amount'] = cart[existing_index]['number_of_slots'] * cart[existing_index]['slot_price']
                else:
                    # Add new item to cart
                    cart.append(cart_item)
                
                # Save cart to session
                request.session['waqaf_cart'] = cart
                
                return JsonResponse({
                    'success': True,
                    'message': f'Added {number_of_slots} slot(s) of {asset.name} to cart',
                    'cart_count': sum(item['number_of_slots'] for item in cart)
                })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def view_waqaf_cart(request):
    """View the waqaf cart (supports anonymous users)"""
    cart = get_or_create_waqaf_cart(request)
    
    # Calculate totals for anonymous users
    if not request.user.is_authenticated:
        total_slots = sum(item['number_of_slots'] for item in cart)
        total_amount = sum(item['total_amount'] for item in cart)
        # Create a mock cart object with the calculated totals
        class MockCart:
            def __init__(self, items, total_slots, total_amount):
                self.items = items
                self.total_slots = total_slots
                self.total_amount = total_amount
            
            def __getattr__(self, name):
                # This allows the template to access total_slots and total_amount
                if name == 'total_slots':
                    return self.total_slots
                elif name == 'total_amount':
                    return self.total_amount
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        cart_data = MockCart(cart, total_slots, total_amount)
        cart_items = cart
    else:
        cart_data = cart
        cart_items = cart.items.all()
    
    return render(request, 'waqaf/cart.html', {
        'cart': cart_data,
        'cart_items': cart_items
    })

def update_waqaf_cart_item(request, item_id):
    """Update quantity of a cart item (supports anonymous users)"""
    if request.method == 'POST':
        try:
            new_quantity = int(request.POST.get('quantity', 1))
            
            if request.user.is_authenticated:
                # For authenticated users, use database cart
                cart_item = get_object_or_404(WaqafCartItem, id=item_id, cart__user=request.user)
                
                if new_quantity <= 0:
                    cart_item.delete()
                    return JsonResponse({'success': True, 'message': 'Item removed from cart'})
                
                if new_quantity > cart_item.asset.slots_available:
                    return JsonResponse({'success': False, 'message': f'Only {cart_item.asset.slots_available} slots available'})
                
                cart_item.number_of_slots = new_quantity
                cart_item.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Cart updated',
                    'total_amount': cart_item.total_amount,
                    'cart_total': cart_item.cart.total_amount
                })
            else:
                # For anonymous users, use session-based cart
                cart = request.session.get('waqaf_cart', [])
                try:
                    item_index = int(item_id)
                    if 0 <= item_index < len(cart):
                        if new_quantity <= 0:
                            cart.pop(item_index)
                            request.session['waqaf_cart'] = cart
                            return JsonResponse({'success': True, 'message': 'Item removed from cart'})
                        
                        # Check slots availability
                        asset = WaqafAsset.objects.get(id=cart[item_index]['asset_id'])
                        if new_quantity > asset.slots_available:
                            return JsonResponse({'success': False, 'message': f'Only {asset.slots_available} slots available'})
                        
                        cart[item_index]['number_of_slots'] = new_quantity
                        cart[item_index]['total_amount'] = new_quantity * cart[item_index]['slot_price']
                        request.session['waqaf_cart'] = cart
                        
                        return JsonResponse({
                            'success': True,
                            'message': 'Cart updated',
                            'total_amount': cart[item_index]['total_amount'],
                            'cart_total': sum(item['total_amount'] for item in cart)
                        })
                    else:
                        return JsonResponse({'success': False, 'message': 'Item not found in cart'})
                except (ValueError, IndexError, WaqafAsset.DoesNotExist):
                    return JsonResponse({'success': False, 'message': 'Invalid item'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def remove_from_waqaf_cart(request, item_id):
    """Remove an item from cart (supports anonymous users)"""
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                # For authenticated users, use database cart
                cart_item = get_object_or_404(WaqafCartItem, id=item_id, cart__user=request.user)
                asset_name = cart_item.asset.name
                cart_item.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': f'{asset_name} removed from cart'
                })
            else:
                # For anonymous users, use session-based cart
                cart = request.session.get('waqaf_cart', [])
                try:
                    item_index = int(item_id)
                    if 0 <= item_index < len(cart):
                        asset_name = cart[item_index]['asset_name']
                        cart.pop(item_index)
                        request.session['waqaf_cart'] = cart
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'{asset_name} removed from cart'
                        })
                    else:
                        return JsonResponse({'success': False, 'message': 'Item not found in cart'})
                except (ValueError, IndexError):
                    return JsonResponse({'success': False, 'message': 'Invalid item'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def clear_waqaf_cart(request):
    """Clear all items from cart (supports anonymous users)"""
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                # For authenticated users, use database cart
                cart = get_or_create_waqaf_cart(request)
                cart.clear()
            else:
                # For anonymous users, use session-based cart
                request.session['waqaf_cart'] = []
            
            return JsonResponse({
                'success': True,
                'message': 'Cart cleared'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def checkout_waqaf_cart(request):
    """Checkout the waqaf cart (supports anonymous users)"""
    cart = get_or_create_waqaf_cart(request)
    
    # Calculate totals for anonymous users
    if not request.user.is_authenticated:
        total_slots = sum(item['number_of_slots'] for item in cart)
        total_amount = sum(item['total_amount'] for item in cart)
        # Create a mock cart object with the calculated totals
        class MockCart:
            def __init__(self, items, total_slots, total_amount):
                self.items = items
                self.total_slots = total_slots
                self.total_amount = total_amount
            
            def __getattr__(self, name):
                # This allows the template to access total_slots and total_amount
                if name == 'total_slots':
                    return self.total_slots
                elif name == 'total_amount':
                    return self.total_amount
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        cart_data = MockCart(cart, total_slots, total_amount)
    else:
        cart_data = cart
    
    if request.method == 'POST':
        try:
            # Get contributor info
            contributor_name = request.POST.get('contributor_name')
            contributor_email = request.POST.get('contributor_email')
            contributor_phone = request.POST.get('contributor_phone')
            contributor_address = request.POST.get('contributor_address')
            
            if not contributor_name:
                messages.error(request, 'Contributor name is required')
                return render(request, 'waqaf/checkout.html', {'cart': cart_data})
            
            # Create or get contributor
            contributor, created = Contributor.objects.get_or_create(
                email=contributor_email,
                defaults={
                    'name': contributor_name,
                    'phone': contributor_phone,
                    'address': contributor_address
                }
            )
            
            if not created:
                # Update existing contributor
                contributor.name = contributor_name
                contributor.phone = contributor_phone
                contributor.address = contributor_address
                contributor.save()
            
            # Create contributions for each cart item
            contributions = []
            
            if request.user.is_authenticated:
                # For authenticated users, process database cart items
                for item in cart.items.all():
                    contribution = Contribution.objects.create(
                        contributor=contributor,
                        asset=item.asset,
                        number_of_slots=item.number_of_slots,
                        amount=item.total_amount,
                        payment_status='COMPLETED',
                        dedicated_for=request.POST.get('dedicated_for', ''),
                        payment_type='ONE_OFF'
                    )
                    contributions.append(contribution)
                    
                    # Update asset slots
                    item.asset.slots_available -= item.number_of_slots
                    item.asset.save()
                
                # Clear cart
                cart.clear()
            else:
                # For anonymous users, process session cart items
                for item in cart:
                    asset = WaqafAsset.objects.get(id=item['asset_id'])
                    contribution = Contribution.objects.create(
                        contributor=contributor,
                        asset=asset,
                        number_of_slots=item['number_of_slots'],
                        amount=Decimal(str(item['total_amount'])),
                        payment_status='COMPLETED',
                        dedicated_for=request.POST.get('dedicated_for', ''),
                        payment_type='ONE_OFF'
                    )
                    contributions.append(contribution)
                    
                    # Update asset slots
                    asset.slots_available -= item['number_of_slots']
                    asset.save()
                
                # Clear session cart
                request.session['waqaf_cart'] = []
            
            # Store the first contribution ID in session for certificate generation
            if contributions:
                request.session['certificate_id'] = contributions[0].id
            
            messages.success(request, f'Successfully created {len(contributions)} contribution(s)')
            return redirect('waqaf:waqaf_success')
            
        except Exception as e:
            messages.error(request, f'Error during checkout: {str(e)}')
    
    return render(request, 'waqaf/checkout.html', {'cart': cart_data})

def waqaf_success(request):
    """Success page after waqaf contribution (supports anonymous users)"""
    # Get the latest contribution for this session
    contribution_id = request.session.get('certificate_id')
    contribution = None
    if contribution_id:
        try:
            contribution = Contribution.objects.get(id=contribution_id)
        except Contribution.DoesNotExist:
            pass
    
    context = {
        'contribution': contribution,
        'is_anonymous': not request.user.is_authenticated
    }
    
    return render(request, 'waqaf/success.html', context)

def get_waqaf_cart_count(request):
    """Get cart count for navigation (supports anonymous users)"""
    try:
        cart = get_or_create_waqaf_cart(request)
        
        if request.user.is_authenticated:
            # For authenticated users, use database cart
            count = cart.total_slots
        else:
            # For anonymous users, use session-based cart
            count = sum(item['number_of_slots'] for item in cart)
        
        return JsonResponse({'count': count})
    except:
        return JsonResponse({'count': 0})

@login_required
def add_waqaf_asset(request):
    """Add a new waqaf asset (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied. Admin only.")
        return redirect('waqaf:waqaf')
    
    if request.method == 'POST':
        form = WaqafAssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            # Set available slots equal to total slots for new assets
            asset.slots_available = asset.total_slots
            asset.save()
            messages.success(request, f'Waqaf asset "{asset.name}" has been created successfully!')
            return redirect('waqaf:waqaf')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WaqafAssetForm()
    
    return render(request, 'waqaf/add_asset.html', {
        'form': form,
        'title': 'Add Waqaf Asset'
    })

@login_required
def delete_waqaf_asset(request, asset_id):
    """Delete a waqaf asset (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied. Admin only.")
        return redirect('waqaf:waqaf')
    
    asset = get_object_or_404(WaqafAsset, id=asset_id)
    
    if request.method == 'POST':
        # Get contribution count for warning message
        contributions_count = Contribution.objects.filter(asset=asset).count()
        
        asset_name = asset.name
        asset.delete()
        
        if contributions_count > 0:
            messages.warning(request, f'Waqaf asset "{asset_name}" has been deleted successfully! {contributions_count} contribution(s) were also removed.')
        else:
            messages.success(request, f'Waqaf asset "{asset_name}" has been deleted successfully!')
        
        return redirect('waqaf:waqaf')
    
    # Show confirmation page
    contributions_count = Contribution.objects.filter(asset=asset).count()
    
    return render(request, 'waqaf/delete_asset_confirm.html', {
        'asset': asset,
        'contributions_count': contributions_count
    })