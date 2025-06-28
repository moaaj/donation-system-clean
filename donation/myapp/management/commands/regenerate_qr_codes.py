from django.core.management.base import BaseCommand
from myapp.models import DonationEvent

class Command(BaseCommand):
    help = 'Regenerates QR codes for all donation events'

    def handle(self, *args, **kwargs):
        events = DonationEvent.objects.all()
        count = 0
        
        for event in events:
            # Clear existing QR code
            if event.qr_code:
                event.qr_code.delete(save=False)
            
            # Generate new QR code
            event.generate_qr_code()
            event.save()
            count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully regenerated QR code for event: {event.title}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully regenerated QR codes for {count} events')
        ) 