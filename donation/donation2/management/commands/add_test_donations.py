from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import DonationEvent, Donation, DonationCategory
from decimal import Decimal
import random
from datetime import timedelta
from django.db import models

class Command(BaseCommand):
    help = 'Add test donation data for analytics testing'

    def handle(self, *args, **options):
        # Get or create a category
        category, created = DonationCategory.objects.get_or_create(
            name='General',
            defaults={'description': 'General donations'}
        )
        
        # Get or create Ramadan event
        ramadan_event, created = DonationEvent.objects.get_or_create(
            title='Ramadan Fundraising Campaign',
            defaults={
                'description': 'Help support our community during Ramadan',
                'target_amount': Decimal('50000.00'),
                'start_date': timezone.now().date() - timedelta(days=30),
                'end_date': timezone.now().date() + timedelta(days=60),
                'is_active': True,
                'category': category
            }
        )
        
        # Get or create other events
        school_event, created = DonationEvent.objects.get_or_create(
            title='School Building Fund',
            defaults={
                'description': 'Help build new classrooms for our students',
                'target_amount': Decimal('100000.00'),
                'start_date': timezone.now().date() - timedelta(days=15),
                'end_date': timezone.now().date() + timedelta(days=45),
                'is_active': True,
                'category': category
            }
        )
        
        library_event, created = DonationEvent.objects.get_or_create(
            title='Library Development',
            defaults={
                'description': 'Support our library with new books and equipment',
                'target_amount': Decimal('25000.00'),
                'start_date': timezone.now().date() - timedelta(days=10),
                'end_date': timezone.now().date() + timedelta(days=20),
                'is_active': True,
                'category': category
            }
        )
        
        # Sample donor names
        donor_names = [
            'Ahmad bin Abdullah', 'Fatima binti Omar', 'Mohammed Al-Rashid',
            'Aisha binti Hassan', 'Omar bin Khalid', 'Khadijah binti Ali',
            'Yusuf bin Ibrahim', 'Zainab binti Ahmed', 'Hassan bin Mustafa',
            'Mariam binti Yusuf', 'Ali bin Rashid', 'Aminah binti Khalil',
            'Khalid bin Omar', 'Noor binti Ahmed', 'Ibrahim bin Hassan',
            'Layla binti Yusuf', 'Mustafa bin Ali', 'Huda binti Khalid',
            'Rashid bin Omar', 'Sara binti Ibrahim'
        ]
        
        # Payment methods
        payment_methods = ['bank_transfer', 'online']
        
        # Add donations for Ramadan event
        ramadan_donations = [
            {'name': 'Ahmad bin Abdullah', 'amount': Decimal('500.00'), 'method': 'bank_transfer'},
            {'name': 'Fatima binti Omar', 'amount': Decimal('750.00'), 'method': 'bank_transfer'},
            {'name': 'Mohammed Al-Rashid', 'amount': Decimal('1000.00'), 'method': 'online'},
            {'name': 'Aisha binti Hassan', 'amount': Decimal('300.00'), 'method': 'online'},
            {'name': 'Omar bin Khalid', 'amount': Decimal('1200.00'), 'method': 'bank_transfer'},
            {'name': 'Khadijah binti Ali', 'amount': Decimal('450.00'), 'method': 'online'},
            {'name': 'Yusuf bin Ibrahim', 'amount': Decimal('800.00'), 'method': 'bank_transfer'},
            {'name': 'Zainab binti Ahmed', 'amount': Decimal('650.00'), 'method': 'bank_transfer'},
            {'name': 'Hassan bin Mustafa', 'amount': Decimal('900.00'), 'method': 'online'},
            {'name': 'Mariam binti Yusuf', 'amount': Decimal('400.00'), 'method': 'online'},
            {'name': 'Ali bin Rashid', 'amount': Decimal('1100.00'), 'method': 'bank_transfer'},
            {'name': 'Aminah binti Khalil', 'amount': Decimal('550.00'), 'method': 'online'},
            {'name': 'Khalid bin Omar', 'amount': Decimal('700.00'), 'method': 'bank_transfer'},
            {'name': 'Noor binti Ahmed', 'amount': Decimal('850.00'), 'method': 'bank_transfer'},
            {'name': 'Ibrahim bin Hassan', 'amount': Decimal('600.00'), 'method': 'online'},
        ]
        
        # Add donations for School Building Fund
        school_donations = [
            {'name': 'Layla binti Yusuf', 'amount': Decimal('2000.00'), 'method': 'bank_transfer'},
            {'name': 'Mustafa bin Ali', 'amount': Decimal('1500.00'), 'method': 'online'},
            {'name': 'Huda binti Khalid', 'amount': Decimal('3000.00'), 'method': 'bank_transfer'},
            {'name': 'Rashid bin Omar', 'amount': Decimal('1200.00'), 'method': 'online'},
            {'name': 'Sara binti Ibrahim', 'amount': Decimal('1800.00'), 'method': 'online'},
            {'name': 'Ahmad bin Abdullah', 'amount': Decimal('2500.00'), 'method': 'bank_transfer'},
            {'name': 'Fatima binti Omar', 'amount': Decimal('900.00'), 'method': 'bank_transfer'},
            {'name': 'Mohammed Al-Rashid', 'amount': Decimal('1600.00'), 'method': 'online'},
        ]
        
        # Add donations for Library Development
        library_donations = [
            {'name': 'Aisha binti Hassan', 'amount': Decimal('300.00'), 'method': 'online'},
            {'name': 'Omar bin Khalid', 'amount': Decimal('500.00'), 'method': 'bank_transfer'},
            {'name': 'Khadijah binti Ali', 'amount': Decimal('400.00'), 'method': 'online'},
            {'name': 'Yusuf bin Ibrahim', 'amount': Decimal('600.00'), 'method': 'online'},
            {'name': 'Zainab binti Ahmed', 'amount': Decimal('350.00'), 'method': 'bank_transfer'},
        ]
        
        # Create donations for Ramadan event
        for donation_data in ramadan_donations:
            donation, created = Donation.objects.get_or_create(
                event=ramadan_event,
                donor_name=donation_data['name'],
                amount=donation_data['amount'],
                payment_method=donation_data['method'],
                defaults={
                    'donor_email': f"{donation_data['name'].replace(' ', '.').lower()}@example.com",
                    'status': 'completed',
                    'message': 'Thank you for supporting our Ramadan campaign!'
                }
            )
            if created:
                self.stdout.write(f"Created donation: {donation_data['name']} - ${donation_data['amount']}")
        
        # Create donations for School Building Fund
        for donation_data in school_donations:
            donation, created = Donation.objects.get_or_create(
                event=school_event,
                donor_name=donation_data['name'],
                amount=donation_data['amount'],
                payment_method=donation_data['method'],
                defaults={
                    'donor_email': f"{donation_data['name'].replace(' ', '.').lower()}@example.com",
                    'status': 'completed',
                    'message': 'Thank you for supporting our school building project!'
                }
            )
            if created:
                self.stdout.write(f"Created donation: {donation_data['name']} - ${donation_data['amount']}")
        
        # Create donations for Library Development
        for donation_data in library_donations:
            donation, created = Donation.objects.get_or_create(
                event=library_event,
                donor_name=donation_data['name'],
                amount=donation_data['amount'],
                payment_method=donation_data['method'],
                defaults={
                    'donor_email': f"{donation_data['name'].replace(' ', '.').lower()}@example.com",
                    'status': 'completed',
                    'message': 'Thank you for supporting our library development!'
                }
            )
            if created:
                self.stdout.write(f"Created donation: {donation_data['name']} - ${donation_data['amount']}")
        
        # Update current amounts for events
        ramadan_total = Donation.objects.filter(event=ramadan_event).aggregate(total=models.Sum('amount'))['total'] or 0
        school_total = Donation.objects.filter(event=school_event).aggregate(total=models.Sum('amount'))['total'] or 0
        library_total = Donation.objects.filter(event=library_event).aggregate(total=models.Sum('amount'))['total'] or 0
        
        ramadan_event.current_amount = ramadan_total
        ramadan_event.save()
        
        school_event.current_amount = school_total
        school_event.save()
        
        library_event.current_amount = library_total
        library_event.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test donations!\n'
                f'Ramadan Event: ${ramadan_total} (Target: ${ramadan_event.target_amount})\n'
                f'School Building: ${school_total} (Target: ${school_event.target_amount})\n'
                f'Library Development: ${library_total} (Target: ${library_event.target_amount})'
            )
        )
