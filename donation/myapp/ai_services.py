from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from .models import Payment, FeeStatus, FeeStructure

class PaymentPredictionService:
    def __init__(self):
        self.model = LinearRegression()

    def prepare_training_data(self):
        """Prepare historical payment data for training"""
        # Get last 12 months of payment data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        payments = Payment.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date
        ).values('payment_date').annotate(
            total_amount=Sum('amount'),
            payment_count=Count('id')
        ).order_by('payment_date')

        # Prepare features (X) and target (y)
        X = []
        y = []
        
        for payment in payments:
            # Features: day of month, day of week, month
            date = payment['payment_date']
            X.append([
                date.day,
                date.weekday(),
                date.month
            ])
            y.append(float(payment['total_amount']))

        return np.array(X), np.array(y)

    def train_model(self):
        """Train the prediction model"""
        X, y = self.prepare_training_data()
        if len(X) > 0:
            self.model.fit(X, y)
            return True
        return False

    def predict_next_month_payments(self):
        """Predict total payments for the next month"""
        if not self.train_model():
            return None

        # Prepare next month's dates
        next_month = timezone.now().date() + timedelta(days=30)
        dates = [next_month + timedelta(days=i) for i in range(30)]
        
        # Prepare features for prediction
        X_pred = np.array([[date.day, date.weekday(), date.month] for date in dates])
        
        # Make predictions
        predictions = self.model.predict(X_pred)
        
        return {
            'total_predicted': float(np.sum(predictions)),
            'daily_predictions': [float(pred) for pred in predictions],
            'dates': [date.strftime('%Y-%m-%d') for date in dates]
        }

    def get_payment_risk_assessment(self, student_id):
        """Assess payment risk for a specific student"""
        # Get student's payment history
        payments = Payment.objects.filter(
            student_id=student_id
        ).order_by('payment_date')

        if not payments.exists():
            return {'risk_level': 'unknown', 'confidence': 0}

        # Calculate payment metrics
        total_payments = payments.count()
        
        # Get fee statuses for the student
        fee_statuses = FeeStatus.objects.filter(
            student_id=student_id,
            fee_structure__in=payments.values_list('fee_structure', flat=True)
        )
        
        late_payments = 0
        total_days_late = 0
        
        for payment in payments:
            fee_status = fee_statuses.filter(fee_structure=payment.fee_structure).first()
            if fee_status and payment.payment_date > fee_status.due_date:
                late_payments += 1
                total_days_late += (payment.payment_date - fee_status.due_date).days
        
        avg_days_late = total_days_late / late_payments if late_payments > 0 else 0

        # Calculate risk score (0-100)
        risk_score = (
            (late_payments / total_payments) * 50 +  # 50% weight for late payment ratio
            (min(avg_days_late / 30, 1) * 50)  # 50% weight for average days late
        )

        # Determine risk level
        if risk_score < 20:
            risk_level = 'low'
        elif risk_score < 50:
            risk_level = 'medium'
        else:
            risk_level = 'high'

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'confidence': 1 - (1 / total_payments),  # More confidence with more data
            'metrics': {
                'total_payments': total_payments,
                'late_payments': late_payments,
                'avg_days_late': avg_days_late
            }
        }

    def get_fee_structure_recommendations(self):
        """Generate recommendations for fee structure optimization"""
        fee_structures = FeeStructure.objects.all()
        recommendations = []

        for structure in fee_structures:
            # Get payment success rate
            total_expected = Payment.objects.filter(
                fee_structure=structure
            ).count()
            
            successful_payments = Payment.objects.filter(
                fee_structure=structure,
                status='completed'
            ).count()

            success_rate = (successful_payments / total_expected) if total_expected > 0 else 0

            # Get fee statuses for this structure
            fee_statuses = FeeStatus.objects.filter(fee_structure=structure)
            
            # Calculate average delay
            late_payments = []
            for payment in Payment.objects.filter(fee_structure=structure):
                fee_status = fee_statuses.filter(student=payment.student).first()
                if fee_status and payment.payment_date > fee_status.due_date:
                    late_payments.append((payment.payment_date - fee_status.due_date).days)
            
            avg_delay = sum(late_payments) / len(late_payments) if late_payments else 0

            # Generate recommendation
            if success_rate < 0.7:
                recommendations.append({
                    'fee_structure': structure,
                    'issue': 'low_success_rate',
                    'current_rate': success_rate,
                    'suggestion': 'Consider reducing the amount or adjusting the payment schedule'
                })
            elif avg_delay > 15:
                recommendations.append({
                    'fee_structure': structure,
                    'issue': 'high_delay',
                    'current_delay': avg_delay,
                    'suggestion': 'Consider implementing early payment incentives'
                })

        return recommendations 