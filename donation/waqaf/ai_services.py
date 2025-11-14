from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
import numpy as np
from decimal import Decimal
from .models import WaqafAsset, Contributor, Contribution, FundDistribution
from django.db.models.functions import TruncMonth

class WaqafAIService:
    @staticmethod
    def predict_asset_value(asset_id):
        """Predict future value of a Waqaf asset based on historical data"""
        try:
            asset = WaqafAsset.objects.get(id=asset_id)
            
            # Get historical distributions for this asset
            distributions = FundDistribution.objects.filter(asset=asset).order_by('date_distributed')
            
            if not distributions.exists():
                return {
                    'current_value': asset.current_value,
                    'predicted_value': asset.current_value,
                    'confidence': 'low',
                    'message': 'Insufficient historical data for prediction'
                }
            
            # Ensure we have enough data points for meaningful prediction
            if len(distributions) < 2:
                return {
                    'current_value': asset.current_value,
                    'predicted_value': asset.current_value,
                    'confidence': 'low',
                    'message': 'Need at least 2 data points for prediction'
                }
            
            # Extract values and ensure they are valid numbers
            values = []
            for d in distributions:
                try:
                    value = float(d.amount)
                    if value > 0:  # Only include positive values
                        values.append(value)
                except (ValueError, TypeError):
                    continue
            
            if len(values) < 2:
                return {
                    'current_value': asset.current_value,
                    'predicted_value': asset.current_value,
                    'confidence': 'low',
                    'message': 'Insufficient valid data points for prediction'
                }
            
            # Use simple moving average instead of linear regression
            window_size = min(3, len(values))
            recent_values = values[-window_size:]
            predicted_value = sum(recent_values) / len(recent_values)
            
            # Calculate trend
            if len(values) >= 2:
                trend = 'increasing' if values[-1] > values[0] else 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'current_value': asset.current_value,
                'predicted_value': round(predicted_value, 2),
                'confidence': 'high' if len(values) > 5 else 'medium',
                'trend': trend,
                'message': 'Prediction based on recent values'
            }
            
        except Exception as e:
            return {
                'current_value': asset.current_value,
                'predicted_value': asset.current_value,
                'confidence': 'low',
                'message': f'Error in prediction: {str(e)}'
            }

    @staticmethod
    def analyze_contribution_patterns():
        """Analyze contribution patterns and provide insights"""
        # Get contribution data for the last 12 months
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        
        contributions = Contribution.objects.filter(
            date_contributed__range=(start_date, end_date)
        )
        
        # Calculate monthly contribution trends using TruncMonth
        monthly_trends = contributions.annotate(
            month=TruncMonth('date_contributed')
        ).values('month').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        # Calculate average contribution amount
        avg_contribution = contributions.aggregate(
            avg_amount=Avg('amount')
        )['avg_amount'] or Decimal('0.00')
        
        # Convert average to float for comparison
        avg_contribution_float = float(avg_contribution)
        
        # Identify peak contribution periods
        peak_periods = []
        for trend in monthly_trends:
            # Convert total_amount to float for comparison
            total_amount_float = float(trend['total_amount'])
            if total_amount_float > avg_contribution_float * 1.5:  # 50% above average
                peak_periods.append({
                    'month': trend['month'].strftime('%Y-%m'),
                    'amount': trend['total_amount']
                })
        
        # Format monthly trends for display
        formatted_trends = []
        for trend in monthly_trends:
            formatted_trends.append({
                'month': trend['month'].strftime('%Y-%m'),
                'total_amount': trend['total_amount'],
                'count': trend['count']
            })
        
        return {
            'monthly_trends': formatted_trends,
            'average_contribution': round(avg_contribution, 2),
            'peak_periods': peak_periods,
            'total_contributions': contributions.count()
        }

    @staticmethod
    def get_asset_management_recommendations():
        """Generate recommendations for asset management"""
        assets = WaqafAsset.objects.all()
        recommendations = []
        
        for asset in assets:
            # Calculate utilization rate
            filled_slots = asset.total_slots - asset.slots_available
            utilization_rate = (filled_slots / asset.total_slots * 100) if asset.total_slots > 0 else 0
            
            # Get recent distributions
            recent_distributions = FundDistribution.objects.filter(
                asset=asset,
                date_distributed__gte=timezone.now() - timedelta(days=90)
            )
            
            # Generate recommendations based on utilization and distributions
            if utilization_rate < 30:
                recommendations.append({
                    'asset': asset.name,
                    'type': 'utilization',
                    'message': f'Low utilization rate ({utilization_rate}%). Consider reducing slot price or increasing marketing efforts.',
                    'priority': 'high'
                })
            
            if not recent_distributions.exists():
                recommendations.append({
                    'asset': asset.name,
                    'type': 'distribution',
                    'message': 'No recent fund distributions. Review distribution strategy.',
                    'priority': 'medium'
                })
        
        return recommendations

    @staticmethod
    def analyze_donor_engagement():
        """Analyze donor engagement patterns and provide recommendations"""
        contributors = Contributor.objects.all()
        engagement_data = []
        
        for contributor in contributors:
            # Get contribution history
            contributions = Contribution.objects.filter(contributor=contributor)
            
            if not contributions.exists():
                continue
            
            # Calculate engagement metrics
            total_contributed = contributions.aggregate(total=Sum('amount'))['total'] or 0
            contribution_frequency = contributions.count()
            last_contribution = contributions.latest('date_contributed').date_contributed
            
            # Calculate engagement score (simple example)
            days_since_last = (timezone.now() - last_contribution).days
            engagement_score = 100 - (days_since_last / 365 * 100) if days_since_last < 365 else 0
            
            engagement_data.append({
                'contributor': contributor.name,
                'total_contributed': total_contributed,
                'contribution_frequency': contribution_frequency,
                'last_contribution': last_contribution,
                'engagement_score': round(engagement_score, 2),
                'recommendation': 'High engagement' if engagement_score > 70 else 
                                'Medium engagement' if engagement_score > 30 else 
                                'Low engagement'
            })
        
        return sorted(engagement_data, key=lambda x: x['engagement_score'], reverse=True)

    @staticmethod
    def get_analytics():
        """Get comprehensive analytics data for the waqaf system"""
        try:
            # Get contribution patterns
            contribution_patterns = WaqafAIService.analyze_contribution_patterns()
            
            # Get asset management recommendations
            asset_recommendations = WaqafAIService.get_asset_management_recommendations()
            
            # Get donor engagement analysis
            donor_engagement = WaqafAIService.analyze_donor_engagement()
            
            # Get overall statistics
            total_assets = WaqafAsset.objects.count()
            total_contributors = Contributor.objects.count()
            total_contributions = Contribution.objects.count()
            total_amount_contributed = Contribution.objects.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            # Get active assets (with available slots)
            active_assets = WaqafAsset.objects.filter(slots_available__gt=0).count()
            
            # Get recent contributions (last 30 days)
            recent_contributions = Contribution.objects.filter(
                date_contributed__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            # Get recent contributions amount
            recent_amount = Contribution.objects.filter(
                date_contributed__gte=timezone.now() - timedelta(days=30)
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            return {
                'contribution_patterns': contribution_patterns,
                'asset_recommendations': asset_recommendations,
                'donor_engagement': donor_engagement,
                'overall_stats': {
                    'total_assets': total_assets,
                    'total_contributors': total_contributors,
                    'total_contributions': total_contributions,
                    'total_amount_contributed': total_amount_contributed,
                    'active_assets': active_assets,
                    'recent_contributions': recent_contributions,
                    'recent_amount': recent_amount,
                }
            }
            
        except Exception as e:
            return {
                'error': f'Error generating analytics: {str(e)}',
                'contribution_patterns': {},
                'asset_recommendations': [],
                'donor_engagement': [],
                'overall_stats': {}
            } 