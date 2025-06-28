from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from .models import WaqafAsset, Contributor, Contribution, FundDistribution
from .forms import WaqafContributionForm, ContributorForm
from django.http import HttpResponse
from reportlab.pdfgen import canvas
import io
from django.db.models import Q
import csv
from django.contrib.auth.decorators import login_required
from myapp.forms import DonationEventForm
from myapp.models import DonationEvent
from .ai_services import WaqafAIService

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

    # Get payment status distribution
    payment_status = Contribution.objects.values('payment_status').annotate(
        count=models.Count('id')
    )

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
    context = {}
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
                return render(request, 'waqaf/contribute.html', {
                    'contributor_form': contributor_form,
                    'contribution_form': contribution_form
                })
            
            # Validate slots availability
            if contribution.number_of_slots > asset.slots_available:
                messages.error(request, f'Only {asset.slots_available} slots available for this asset.')
                return render(request, 'waqaf/contribute.html', {
                    'contributor_form': contributor_form,
                    'contribution_form': contribution_form
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
        
        # Debug information
        available_assets = WaqafAsset.objects.filter(slots_available__gt=0)
        if not available_assets.exists():
            messages.warning(request, 'No waqaf assets are currently available for contribution.')
    
    return render(request, 'waqaf/contribute.html', {
        'contributor_form': contributor_form,
        'contribution_form': contribution_form,
        'available_assets': available_assets  # Add this for debugging
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
    """View for AI-powered Waqaf analytics"""
    # Get asset value predictions
    asset_predictions = []
    for asset in WaqafAsset.objects.all():
        prediction = WaqafAIService.predict_asset_value(asset.id)
        asset_predictions.append({
            'asset': asset,
            'prediction': prediction
        })
    
    # Get contribution pattern analysis
    contribution_patterns = WaqafAIService.analyze_contribution_patterns()
    
    # Get asset management recommendations
    asset_recommendations = WaqafAIService.get_asset_management_recommendations()
    
    # Get donor engagement analysis
    donor_engagement = WaqafAIService.analyze_donor_engagement()
    
    context = {
        'asset_predictions': asset_predictions,
        'contribution_patterns': contribution_patterns,
        'asset_recommendations': asset_recommendations,
        'donor_engagement': donor_engagement,
    }
    
    return render(request, 'waqaf/ai_analytics.html', context)