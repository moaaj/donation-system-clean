from django.core.management.base import BaseCommand
from myapp.models import FeeStructure

class Command(BaseCommand):
    help = 'Clean up duplicate fee structures with different form formats'

    def handle(self, *args, **options):
        self.stdout.write("🧹 Cleaning up duplicate fee structures...")
        
        # Get all fee structures
        all_fee_structures = FeeStructure.objects.filter(is_active=True)
        
        # Group by normalized form names
        form_groups = {}
        for fs in all_fee_structures:
            # Normalize form name (extract just the number)
            form_normalized = str(fs.form).replace('Form', '').strip()
            if form_normalized not in form_groups:
                form_groups[form_normalized] = []
            form_groups[form_normalized].append(fs)
        
        deleted_count = 0
        
        for form_num, fee_structures in form_groups.items():
            if len(fee_structures) > 1:
                self.stdout.write(f"\n📋 Found {len(fee_structures)} fee structures for Form {form_num}:")
                
                # Keep the one with the highest amount (assuming it's more accurate)
                best_fs = max(fee_structures, key=lambda x: x.amount or 0)
                
                for fs in fee_structures:
                    self.stdout.write(f"   - {fs.form}: RM {fs.amount} (ID: {fs.id})")
                
                self.stdout.write(f"   ✅ Keeping: {best_fs.form} with RM {best_fs.amount}")
                
                # Delete the others
                for fs in fee_structures:
                    if fs.id != best_fs.id:
                        self.stdout.write(f"   🗑️  Deleting: {fs.form} with RM {fs.amount}")
                        fs.delete()
                        deleted_count += 1
        
        if deleted_count == 0:
            self.stdout.write("✅ No duplicate fee structures found")
        else:
            self.stdout.write(f"\n✅ Deleted {deleted_count} duplicate fee structures")
        
        # Show final state
        self.stdout.write("\n📊 Final Fee Structures:")
        for fs in FeeStructure.objects.filter(is_active=True).order_by('form'):
            self.stdout.write(f"   - {fs.form}: RM {fs.amount}")
        
        self.stdout.write("\n✨ Cleanup completed!")
