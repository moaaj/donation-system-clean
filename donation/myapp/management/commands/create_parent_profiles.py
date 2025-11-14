from django.core.management.base import BaseCommand
from django.db import transaction
from myapp.models import Parent, UserProfile


class Command(BaseCommand):
    help = 'Create UserProfile records for all parent accounts'

    def handle(self, *args, **options):
        self.stdout.write('Creating UserProfile records for parent accounts...')
        
        with transaction.atomic():
            parents = Parent.objects.all().select_related('user')
            created_count = 0
            
            for parent in parents:
                # Check if UserProfile already exists
                profile, created = UserProfile.objects.get_or_create(
                    user=parent.user,
                    defaults={
                        'role': 'parent',
                        'phone_number': parent.phone_number,
                        'address': parent.address,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'Created UserProfile for: {parent.user.get_full_name()} ({parent.user.username})')
                else:
                    # Update existing profile to parent role if needed
                    if profile.role != 'parent':
                        profile.role = 'parent'
                        profile.phone_number = parent.phone_number
                        profile.address = parent.address
                        profile.save()
                        self.stdout.write(f'Updated UserProfile for: {parent.user.get_full_name()} ({parent.user.username})')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {parents.count()} parent profiles. Created: {created_count}')
        )
