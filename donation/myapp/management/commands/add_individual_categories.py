from django.core.management.base import BaseCommand
from myapp.models import FeeCategory

class Command(BaseCommand):
    help = 'Add individual student fee categories (Overtime, Demerit Penalties, etc.)'

    def handle(self, *args, **options):
        categories_data = [
            {
                'name': 'Overtime',
                'description': 'Fees for overtime activities, late pickups, or extended hours',
                'category_type': 'individual'
            },
            {
                'name': 'Demerit Penalties',
                'description': 'Penalties for behavioral issues, rule violations, or disciplinary actions',
                'category_type': 'individual'
            },
            {
                'name': 'Late Payment Penalties',
                'description': 'Additional charges for late payment of fees',
                'category_type': 'individual'
            },
            {
                'name': 'Damage Fees',
                'description': 'Fees for damage to school property or equipment',
                'category_type': 'individual'
            },
            {
                'name': 'Special Services',
                'description': 'Fees for special services, tutoring, or additional support',
                'category_type': 'individual'
            },
            {
                'name': 'Transportation Fees',
                'description': 'Additional transportation or bus service fees',
                'category_type': 'individual'
            },
            {
                'name': 'Activity Fees',
                'description': 'Fees for special activities, events, or programs',
                'category_type': 'individual'
            },
            {
                'name': 'Library Fines',
                'description': 'Fines for overdue books or library materials',
                'category_type': 'individual'
            },
            {
                'name': 'Uniform Replacement',
                'description': 'Fees for replacement of lost or damaged uniforms',
                'category_type': 'individual'
            },
            {
                'name': 'Other Penalties',
                'description': 'Other miscellaneous penalties or fees',
                'category_type': 'individual'
            }
        ]

        created_count = 0
        updated_count = 0

        for category_data in categories_data:
            category, created = FeeCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'category_type': category_data['category_type'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created category: {category.name}')
                )
                created_count += 1
            else:
                # Update existing category if needed
                if category.category_type != category_data['category_type']:
                    category.category_type = category_data['category_type']
                    category.save()
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated category: {category.name}')
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Category already exists: {category.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} categories created, {updated_count} categories updated'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Individual student fee categories are now ready to use!'
            )
        ) 