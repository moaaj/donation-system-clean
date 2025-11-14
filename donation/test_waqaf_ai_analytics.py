#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from waqaf.ai_services import WaqafAIService
from waqaf.models import WaqafAsset, Contributor, Contribution

def test_waqaf_ai_analytics():
    """Test the waqaf AI analytics functionality"""
    
    print("=" * 60)
    print("TESTING WAQAF AI ANALYTICS FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test get_analytics method
        print("\n📊 Testing get_analytics method...")
        analytics_data = WaqafAIService.get_analytics()
        
        print("✅ Analytics data retrieved successfully")
        print(f"   - Contribution patterns: {len(analytics_data.get('contribution_patterns', {}))} items")
        print(f"   - Asset recommendations: {len(analytics_data.get('asset_recommendations', []))} items")
        print(f"   - Donor engagement: {len(analytics_data.get('donor_engagement', []))} items")
        print(f"   - Overall stats: {len(analytics_data.get('overall_stats', {}))} items")
        
        # Test individual methods
        print("\n📈 Testing individual analytics methods...")
        
        # Test contribution patterns
        contribution_patterns = WaqafAIService.analyze_contribution_patterns()
        print(f"✅ Contribution patterns: {len(contribution_patterns.get('monthly_trends', []))} monthly trends")
        
        # Test asset recommendations
        asset_recommendations = WaqafAIService.get_asset_management_recommendations()
        print(f"✅ Asset recommendations: {len(asset_recommendations)} recommendations")
        
        # Test donor engagement
        donor_engagement = WaqafAIService.analyze_donor_engagement()
        print(f"✅ Donor engagement: {len(donor_engagement)} donors analyzed")
        
        # Test asset predictions
        assets = WaqafAsset.objects.all()
        print(f"\n🏢 Testing asset predictions for {assets.count()} assets...")
        
        for asset in assets:
            prediction = WaqafAIService.predict_asset_value(asset.id)
            print(f"   - {asset.name}: Current RM {prediction['current_value']}, Predicted RM {prediction['predicted_value']} ({prediction['confidence']} confidence)")
        
        # Show overall statistics
        overall_stats = analytics_data.get('overall_stats', {})
        print(f"\n📋 Overall Statistics:")
        print(f"   - Total Assets: {overall_stats.get('total_assets', 0)}")
        print(f"   - Total Contributors: {overall_stats.get('total_contributors', 0)}")
        print(f"   - Total Contributions: {overall_stats.get('total_contributions', 0)}")
        print(f"   - Total Amount: RM {overall_stats.get('total_amount_contributed', 0)}")
        print(f"   - Active Assets: {overall_stats.get('active_assets', 0)}")
        print(f"   - Recent Contributions: {overall_stats.get('recent_contributions', 0)}")
        print(f"   - Recent Amount: RM {overall_stats.get('recent_amount', 0)}")
        
        print("\n✅ All AI analytics tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error testing AI analytics: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_waqaf_ai_analytics()
