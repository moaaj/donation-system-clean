from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
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

def calculate_fund_status():
    total_contributions = Contribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    total_distributions = FundDistribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    balance = total_contributions - total_distributions
    return {
        'total_contributions': total_contributions,
        'total_distributions': total_distributions,
        'balance': balance
    }

def waqaf_dashboard(request):
    # Get the total number of assets and total value
    total_assets = WaqafAsset.objects.count()
    total_value = WaqafAsset.objects.aggregate(models.Sum('current_value'))['current_value__sum'] or 0

    # Get the total number of contributors and total amount contributed
    total_contributors = Contributor.objects.count()
    total_contributed = Contribution.objects.filter(payment_status='COMPLETED').aggregate(models.Sum('amount'))['amount__sum'] or 0

    # Get assets with available slots
    available_assets = WaqafAsset.objects.filter(slots_available__gt=0)

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
    }

    return render(request, 'waqaf/waqaf_dashboard.html', context)

def waqaf(request):
    # Check if user is admin
    is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    
    if is_admin:
        # Admin view - show all assets with management options
        all_assets = WaqafAsset.objects.all()
        
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
        
        context = {
            'is_admin': True,
            'assets_progress': assets_progress,
            'total_assets': all_assets.count(),
            'total_contributions': Contribution.objects.count(),
            'total_amount': Contribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        }
    else:
        # Regular user view - show available assets with cart functionality
        available_assets = WaqafAsset.objects.filter(slots_available__gt=0)
        
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
                # Get available assets for the template
                available_assets = WaqafAsset.objects.filter(slots_available__gt=0)
                return render(request, 'waqaf/contribute.html', {
                    'contributor_form': contributor_form,
                    'contribution_form': contribution_form,
                    'available_assets': available_assets
                })
            
            # Validate slots availability
            if contribution.number_of_slots > asset.slots_available:
                messages.error(request, f'Only {asset.slots_available} slots available for this asset.')
                # Get available assets for the template
                available_assets = WaqafAsset.objects.filter(slots_available__gt=0)
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
            
            return redirect('waqaf:waqaf_dashboard')
    else:
        contributor_form = ContributorForm()
        contribution_form = WaqafContributionForm()
    
    # Get available assets for the template (moved outside if/else to ensure it's always defined)
    available_assets = WaqafAsset.objects.filter(slots_available__gt=0)
    if not available_assets.exists():
        messages.warning(request, 'No waqaf assets are currently available for contribution.')

    return render(request, 'waqaf/contribute.html', {
        'contributor_form': contributor_form,
        'contribution_form': contribution_form,
        'available_assets': available_assets
    })

def asset_detail(request, asset_id):
    asset = get_object_or_404(WaqafAsset, id=asset_id)
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

def download_certificate(request, contribution_id):
    contribution = Contribution.objects.get(id=contribution_id)
    # Get total contribution amount for this contributor
    total_amount = Contribution.objects.filter(
        contributor=contribution.contributor,
        payment_status='COMPLETED'
    ).aggregate(total=models.Sum('amount'))['total'] or 0

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

    # Amount badge (simple red circle)
    p.setFillColorRGB(1, 0, 0)
    p.circle(120, 200, 30, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(120, 195, f"RM{total_amount:.2f}")
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
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{contribution.id}.pdf"'
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
    
    ai_service = WaqafAIService()
    analytics_data = ai_service.get_analytics()
    
    return render(request, 'waqaf/ai_analytics.html', {
        'analytics_data': analytics_data
    })

# Waqaf Cart Views
@login_required
def get_or_create_waqaf_cart(request):
    """Get or create a cart for the current user"""
    cart, created = WaqafCart.objects.get_or_create(user=request.user)
    return cart

@login_required
def add_to_waqaf_cart(request, asset_id):
    """Add a waqaf asset to cart"""
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
            
            # Check if item already exists in cart
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
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def view_waqaf_cart(request):
    """View the waqaf cart"""
    cart = get_or_create_waqaf_cart(request)
    return render(request, 'waqaf/cart.html', {
        'cart': cart,
        'cart_items': cart.items.all()
    })

@login_required
def update_waqaf_cart_item(request, item_id):
    """Update quantity of a cart item"""
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(WaqafCartItem, id=item_id, cart__user=request.user)
            new_quantity = int(request.POST.get('quantity', 1))
            
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
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def remove_from_waqaf_cart(request, item_id):
    """Remove an item from cart"""
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(WaqafCartItem, id=item_id, cart__user=request.user)
            asset_name = cart_item.asset.name
            cart_item.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'{asset_name} removed from cart'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def clear_waqaf_cart(request):
    """Clear all items from cart"""
    if request.method == 'POST':
        try:
            cart = get_or_create_waqaf_cart(request)
            cart.clear()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart cleared'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def checkout_waqaf_cart(request):
    """Checkout the waqaf cart"""
    cart = get_or_create_waqaf_cart(request)
    
    if request.method == 'POST':
        try:
            # Get contributor info
            contributor_name = request.POST.get('contributor_name')
            contributor_email = request.POST.get('contributor_email')
            contributor_phone = request.POST.get('contributor_phone')
            contributor_address = request.POST.get('contributor_address')
            
            if not contributor_name:
                messages.error(request, 'Contributor name is required')
                return render(request, 'waqaf/checkout.html', {'cart': cart})
            
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
            for item in cart.items.all():
                contribution = Contribution.objects.create(
                    contributor=contributor,
                    asset=item.asset,
                    number_of_slots=item.number_of_slots,
                    amount=item.total_amount,
                    payment_status='PENDING',
                    dedicated_for=request.POST.get('dedicated_for', ''),
                    payment_type='ONE_OFF'
                )
                contributions.append(contribution)
                
                # Update asset slots
                item.asset.slots_available -= item.number_of_slots
                item.asset.save()
            
            # Clear cart
            cart.clear()
            
            messages.success(request, f'Successfully created {len(contributions)} contribution(s)')
            return redirect('waqaf:waqaf_success')
            
        except Exception as e:
            messages.error(request, f'Error during checkout: {str(e)}')
    
    return render(request, 'waqaf/checkout.html', {'cart': cart})

@login_required
def waqaf_success(request):
    """Success page after waqaf contribution"""
    return render(request, 'waqaf/success.html')

@login_required
def get_waqaf_cart_count(request):
    """Get cart count for navigation"""
    try:
        cart = get_or_create_waqaf_cart(request)
        count = cart.total_slots
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
        # Check if asset has any contributions
        contributions_count = Contribution.objects.filter(asset=asset).count()
        
        if contributions_count > 0:
            messages.error(request, f'Cannot delete "{asset.name}" because it has {contributions_count} contribution(s). Please remove all contributions first.')
            return redirect('waqaf:waqaf')
        
        asset_name = asset.name
        asset.delete()
        messages.success(request, f'Waqaf asset "{asset_name}" has been deleted successfully!')
        return redirect('waqaf:waqaf')
    
    # Show confirmation page
    contributions_count = Contribution.objects.filter(asset=asset).count()
    
    return render(request, 'waqaf/delete_asset_confirm.html', {
        'asset': asset,
        'contributions_count': contributions_count
    })