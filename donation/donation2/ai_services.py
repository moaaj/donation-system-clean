import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob
import joblib
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Sum
from myapp.models import DonationEvent, Donation, FeeStructure, FeeStatus, Payment
from decimal import Decimal
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from django.utils import timezone
from nltk.sentiment import SentimentIntensityAnalyzer
from django.contrib.auth.models import User
from openai import OpenAI

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

class DonationAIService:
    def __init__(self):
        self.fraud_model = None
        self.recommendation_model = None
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
    def train_fraud_detection_model(self, historical_donations):
        """Train a model to detect potentially fraudulent donations"""
        features = self._extract_donation_features(historical_donations)
        labels = [d.is_fraud for d in historical_donations]
        
        self.fraud_model = RandomForestClassifier(n_estimators=100)
        self.fraud_model.fit(features, labels)
        
    def predict_fraud_probability(self, donation):
        """Predict the probability of a donation being fraudulent"""
        if not self.fraud_model:
            return 0.0
            
        features = self._extract_donation_features([donation])
        return self.fraud_model.predict_proba(features)[0][1]
        
    def get_donation_recommendations(self, user, n_recommendations=5):
        """Get personalized donation event recommendations for a user"""
        # Get user's donation history by email
        user_donations = Donation.objects.filter(donor_email=user.email)
        
        # Get categories user has donated to
        user_categories = user_donations.values_list('event__category', flat=True).distinct()
        
        # Find active events in those categories, excluding events already donated to
        recommended_events = DonationEvent.objects.filter(
            category__in=user_categories,
            is_active=True
        ).exclude(
            donations__donor_email=user.email
        ).annotate(
            avg_donation=Avg('donations__amount'),
            donation_count=Count('donations')
        ).order_by('-donation_count')[:n_recommendations]
        
        return recommended_events
        
    def analyze_event_sentiment(self, event_description):
        """Analyze the sentiment of an event description using VADER with enhanced features"""
        # Initialize VADER sentiment analyzer
        sia = SentimentIntensityAnalyzer()
        
        # Clean and preprocess the text
        cleaned_text = self._preprocess_text(event_description)
        
        # Get sentiment scores
        sentiment_scores = sia.polarity_scores(cleaned_text)
        
        # Calculate weighted sentiment score with enhanced features
        compound_score = sentiment_scores['compound']
        
        # Calculate enhanced subjectivity
        total_words = len(cleaned_text.split())
        if total_words > 0:
            # Enhanced subjectivity calculation considering word intensity
            subjectivity = (sentiment_scores['pos'] + sentiment_scores['neg']) / total_words
            # Adjust subjectivity based on word intensity
            intensity_factor = abs(sentiment_scores['pos'] - sentiment_scores['neg'])
            subjectivity = subjectivity * (1 + intensity_factor)
            # Normalize subjectivity to 0-1 range
            subjectivity = min(1.0, subjectivity)
        else:
            subjectivity = 0.0
        
        # Calculate emotional intensity
        emotional_intensity = abs(sentiment_scores['pos'] - sentiment_scores['neg'])
        
        # Determine sentiment category
        if compound_score >= 0.05:
            sentiment_category = 'positive'
        elif compound_score <= -0.05:
            sentiment_category = 'negative'
        else:
            sentiment_category = 'neutral'
        
        # Calculate confidence score
        confidence = abs(compound_score) * (1 - subjectivity)
        
        # Get key emotional words
        emotional_words = self._extract_emotional_words(cleaned_text)
        
        return {
            'polarity': compound_score,  # -1 to 1
            'subjectivity': subjectivity,  # 0 to 1
            'emotional_intensity': emotional_intensity,  # 0 to 1
            'sentiment_category': sentiment_category,
            'confidence': confidence,  # 0 to 1
            'emotional_words': emotional_words,
            'detailed_scores': {
                'positive': sentiment_scores['pos'],
                'negative': sentiment_scores['neg'],
                'neutral': sentiment_scores['neu']
            }
        }

    def _preprocess_text(self, text):
        """Preprocess text for better sentiment analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def _extract_emotional_words(self, text):
        """Extract words that contribute to the sentiment"""
        sia = SentimentIntensityAnalyzer()
        words = text.split()
        emotional_words = []
        
        for word in words:
            score = sia.polarity_scores(word)['compound']
            if abs(score) > 0.1:  # Only include words with significant sentiment
                emotional_words.append({
                    'word': word,
                    'score': score
                })
        
        # Sort by absolute score
        emotional_words.sort(key=lambda x: abs(x['score']), reverse=True)
        return emotional_words[:5]  # Return top 5 emotional words
        
    def predict_donation_impact(self, event):
        """Predict the potential impact of a donation event"""
        # Get historical data for similar events
        similar_events = DonationEvent.objects.filter(
            category=event.category,
            target_amount__range=(event.target_amount * Decimal('0.8'), event.target_amount * Decimal('1.2'))
        )
        
        if not similar_events:
            return None
            
        avg_completion_rate = similar_events.aggregate(
            avg_rate=Avg('current_amount') / Avg('target_amount')
        )['avg_rate']
        
        if avg_completion_rate is None:
            avg_completion_rate = 0
        
        predicted_completion = event.target_amount * Decimal(str(avg_completion_rate))
        days_to_completion = (event.end_date - datetime.now().date()).days
        
        return {
            'predicted_completion_rate': avg_completion_rate,
            'predicted_amount': predicted_completion,
            'estimated_days_to_completion': days_to_completion
        }
        
    def _extract_donation_features(self, donations):
        """Extract features from donations for fraud detection"""
        features = []
        for donation in donations:
            feature_vector = [
                float(donation.amount),
                (donation.created_at - donation.event.created_at).total_seconds(),
                float(donation.event.target_amount),
                float(donation.event.current_amount),
                len(donation.event.donations.all())  # Number of donations for this event
            ]
            features.append(feature_vector)
        return np.array(features)

class UnifiedAIAssistant:
    def __init__(self):
        self.greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'halo', 'hai']
        self.farewells = ['bye', 'goodbye', 'see you', 'farewell', 'thank you', 'thanks', 'selamat tinggal', 'terima kasih']
        
        # Enhanced keywords for better module identification
        self.module_keywords = {
            'donation': ['donation', 'donate', 'fundraising', 'contribute', 'give', 'charity', 'sumbangan', 'derma', 'tabung'],
            'fees': ['fee', 'fees', 'payment', 'pay', 'school fees', 'tuition', 'payment status', 'yuran', 'bayar', 'bayaran'],
            'events': ['event', 'events', 'activity', 'activities', 'schedule', 'calendar', 'acara', 'aktiviti', 'program'],
            'waqaf': ['waqaf', 'endowment', 'islamic endowment', 'religious endowment', 'charitable trust', 'wakaf'],
            'student': ['student', 'students', 'registration', 'enroll', 'pelajar', 'murid', 'daftar'],
            'receipt': ['receipt', 'resit', 'invoice', 'bil', 'proof', 'bukti'],
            'help': ['help', 'bantuan', 'tolong', 'assist', 'support', 'sokongan']
        }
        
        # Common question patterns
        self.question_patterns = {
            'how': ['how', 'bagaimana', 'macam mana', 'cara'],
            'what': ['what', 'apa', 'apakah'],
            'when': ['when', 'bila', 'kapan'],
            'where': ['where', 'mana', 'di mana'],
            'why': ['why', 'kenapa', 'mengapa'],
            'who': ['who', 'siapa']
        }
        
        # Download required NLTK data
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        self.sia = SentimentIntensityAnalyzer()

    def process_message(self, message, user=None):
        """Process user message and return appropriate response"""
        original_message = message
        message = message.lower().strip()
        
        # Check for greetings
        if any(greeting in message for greeting in self.greetings):
            return self._get_greeting_response(user)
        
        # Check for farewells
        if any(farewell in message for farewell in self.farewells):
            return self._get_farewell_response()
        
        # Handle help requests
        if any(help_word in message for help_word in self.module_keywords['help']):
            return self._get_help_response()
        
        # Identify question type for better responses
        question_type = self._identify_question_type(message)
        
        # Identify module and handle accordingly
        modules = self._identify_modules(message)  # Can identify multiple modules
        
        if 'donation' in modules:
            return self._handle_donation_query(message, user, question_type)
        elif 'fees' in modules:
            return self._handle_fees_query(message, user, question_type)
        elif 'events' in modules:
            return self._handle_events_query(message, user, question_type)
        elif 'waqaf' in modules:
            return self._handle_waqaf_query(message, user, question_type)
        elif 'student' in modules:
            return self._handle_student_query(message, user, question_type)
        elif 'receipt' in modules:
            return self._handle_receipt_query(message, user, question_type)
        
        # Try to provide intelligent response based on keywords
        return self._get_intelligent_response(message, user)

    def _handle_student_query(self, message, user, question_type='general'):
        """Handle student-related queries"""
        from myapp.models import Student
        
        if 'register' in message or 'registration' in message:
            return {
                'message': "👨‍🎓 **Student Registration Process:**\n\n📋 **Required Information:**\n• Student ID (unique)\n• NRIC number\n• Full name (first & last)\n• Class/Form level\n• Phone number\n• Program details\n\n📝 **Registration Steps:**\n1. Fill out student registration form\n2. Provide required documents\n3. Submit application\n4. Wait for approval\n5. Receive confirmation\n\nNeed help with the registration form?",
                'suggestions': ['Registration form', 'Required documents', 'Class levels', 'Contact admin']
            }
        
        elif 'information' in message or 'details' in message:
            if user and user.is_authenticated:
                try:
                    if hasattr(user, 'myapp_profile') and user.myapp_profile.role == 'student':
                        student = user.myapp_profile.student
                        response = f"👨‍🎓 **Your Student Information:**\n\n"
                        response += f"📋 **Name**: {student.first_name} {student.last_name}\n"
                        response += f"🆔 **Student ID**: {student.student_id}\n"
                        response += f"📚 **Level**: {student.get_level_display_value()}\n"
                        if student.class_name:
                            response += f"🏫 **Class**: {student.class_name}\n"
                        response += f"📱 **Phone**: {student.phone_number or 'Not provided'}\n"
                        response += f"✅ **Status**: {'Active' if student.is_active else 'Inactive'}"
                        
                        return {
                            'message': response,
                            'suggestions': ['Update information', 'Check fees', 'Payment history', 'Download receipt']
                        }
                except:
                    pass
            
            return {
                'message': "🔐 Please log in to view your student information.",
                'suggestions': ['Login', 'Registration info', 'Contact admin']
            }
        
        return {
            'message': "👨‍🎓 **Student Services Help**\n\nI can help you with:\n• Student registration process\n• View student information\n• Class and level details\n• Academic matters\n• Contact information\n\nWhat would you like to know?",
            'suggestions': ['Registration process', 'My student info', 'Class levels', 'Academic help']
        }
    
    def _handle_receipt_query(self, message, user, question_type='general'):
        """Handle receipt-related queries"""
        from myapp.models import Payment
        
        if user and user.is_authenticated:
            try:
                if hasattr(user, 'myapp_profile') and user.myapp_profile.role == 'student':
                    student = user.myapp_profile.student
                    recent_payments = Payment.objects.filter(
                        student=student, 
                        status='completed'
                    ).order_by('-payment_date')[:5]
                    
                    if recent_payments.exists():
                        response = "🧾 **Available Receipts:**\n\n"
                        for payment in recent_payments:
                            response += f"📄 **Payment #{payment.id}**\n"
                            response += f"   Amount: RM {payment.amount}\n"
                            response += f"   Date: {payment.payment_date}\n"
                            response += f"   Method: {payment.get_payment_method_display()}\n"
                            if payment.receipt_number:
                                response += f"   Receipt: {payment.receipt_number}\n"
                            response += "\n"
                        
                        return {
                            'message': response,
                            'suggestions': ['Download receipt', 'Email receipt', 'Print receipt', 'Payment history']
                        }
                    else:
                        return {
                            'message': "📭 No completed payments found. Make a payment first to generate receipts.",
                            'suggestions': ['Check fees', 'Make payment', 'Payment methods']
                        }
            except:
                pass
        
        return {
            'message': "🧾 **Receipt Information:**\n\n📋 **About Receipts:**\n• Generated automatically after successful payment\n• Available for download immediately\n• Can be emailed to your address\n• Include all payment details\n• Valid for tax purposes\n\n🔐 Login to access your receipts.",
            'suggestions': ['Login', 'Payment methods', 'How to pay?']
        }
    
    def _get_intelligent_response(self, message, user):
        """Generate intelligent response for unrecognized queries"""
        # Analyze sentiment
        sentiment = self.sia.polarity_scores(message)
        
        # Check for common keywords and provide helpful responses
        if 'problem' in message or 'issue' in message or 'error' in message:
            return {
                'message': "🔧 **Having Problems?**\n\nI'm here to help! Common issues and solutions:\n\n💳 **Payment Issues:**\n• Check payment method details\n• Verify account balance\n• Contact bank if needed\n\n🔐 **Login Problems:**\n• Reset password\n• Check username spelling\n• Clear browser cache\n\n📱 **Technical Issues:**\n• Refresh the page\n• Try different browser\n• Contact technical support\n\nWhat specific problem are you facing?",
                'suggestions': ['Payment problems', 'Login issues', 'Technical support', 'Contact admin']
            }
        
        elif 'contact' in message or 'phone' in message or 'email' in message:
            return {
                'message': "📞 **Contact Information:**\n\n🏫 **School Office:**\n• Phone: +60X-XXX-XXXX\n• Email: admin@school.edu.my\n• Office Hours: 8:00 AM - 5:00 PM\n\n💻 **Technical Support:**\n• Email: support@school.edu.my\n• Response time: 24-48 hours\n\n📍 **Address:**\nSchool Administration Office\n[School Address]\n\nHow else can I help you?",
                'suggestions': ['Office hours', 'Email admin', 'Technical support', 'Visit office']
            }
        
        # Default response with sentiment consideration
        if sentiment['compound'] < -0.1:  # Negative sentiment
            return {
                'message': "😔 I sense you might be frustrated. I'm here to help make things easier!\n\n🤝 **I can assist with:**\n• School fees and payments\n• Donation events\n• Student services\n• Technical issues\n• General questions\n\nPlease tell me what's bothering you, and I'll do my best to help! 💪",
                'suggestions': ['I have a problem', 'Payment issues', 'Technical help', 'Contact admin']
            }
        else:
            return {
                'message': "🤔 I'm not sure I understand that specific question, but I'm here to help!\n\n💡 **I can help you with:**\n• 🏫 School fees and payments\n• 💰 Donations and fundraising\n• 🕌 Waqaf (Islamic endowment)\n• 📅 Events and activities\n• 👨‍🎓 Student services\n\nTry asking me something like 'Check my fees' or 'Show donation events'!",
                'suggestions': [
                    'Check my fees',
                    'Show donation events',
                    'What is waqaf?',
                    'Upcoming events',
                    'Help me'
                ]
            }

    def _identify_modules(self, message):
        """Identify which modules the query belongs to (can be multiple)"""
        identified_modules = []
        for module, keywords in self.module_keywords.items():
            if any(keyword in message for keyword in keywords):
                identified_modules.append(module)
        return identified_modules
    
    def _identify_question_type(self, message):
        """Identify the type of question being asked"""
        for q_type, patterns in self.question_patterns.items():
            if any(pattern in message for pattern in patterns):
                return q_type
        return 'general'
    
    def _get_help_response(self):
        """Generate help response"""
        return {
            'message': "I'm here to help! I can assist you with:\n\n🏫 **School Fees & Payments**\n- Check fee status\n- Make payments\n- Apply for waivers\n\n💰 **Donations**\n- Current donation events\n- How to donate\n- Payment methods\n\n🕌 **Waqaf (Islamic Endowment)**\n- What is waqaf\n- Available assets\n- How to contribute\n\n📅 **Events & Activities**\n- Upcoming events\n- Event details\n- How to participate\n\n👨‍🎓 **Student Services**\n- Registration process\n- Student information\n- Academic matters\n\nJust ask me anything!",
            'suggestions': [
                'Check my fees',
                'Show donation events',
                'What is waqaf?',
                'Upcoming events',
                'How to register?'
            ]
        }

    def _get_greeting_response(self, user=None):
        """Generate personalized greeting response"""
        if user and user.is_authenticated:
            name = user.first_name if user.first_name else user.username
            message = f"Hello {name}! 👋 Welcome back! I'm your AI assistant and I'm here to help you with:"
        else:
            message = "Hello! 👋 I'm your AI assistant and I'm here to help you with:"
        
        message += "\n\n🏫 **School Fees & Payments**\n💰 **Donations & Fundraising**\n🕌 **Waqaf (Islamic Endowment)**\n📅 **Events & Activities**\n👨‍🎓 **Student Services**\n\nWhat can I help you with today?"
        
        suggestions = [
            'Check my fees',
            'Show donation events', 
            'What is waqaf?',
            'Upcoming events',
            'How to make payment?'
        ]
        
        # Add personalized suggestions for authenticated users
        if user and user.is_authenticated:
            suggestions.insert(0, 'My account status')
        
        return {
            'message': message,
            'suggestions': suggestions
        }

    def _get_farewell_response(self):
        """Generate farewell response"""
        return {
            'message': "Thank you for chatting with me! If you need any help with donations, fees, or events, feel free to ask anytime.",
            'suggestions': []
        }

    def _handle_donation_query(self, message, user, question_type='general'):
        """Handle donation-related queries with enhanced responses"""
        from myapp.models import DonationEvent, Donation
        
        if 'current' in message or 'active' in message or 'events' in message:
            active_events = DonationEvent.objects.filter(is_active=True).order_by('-created_at')
            if active_events.exists():
                response = "💰 **Current Donation Events:**\n\n"
                for event in active_events[:4]:
                    progress = (event.current_amount / event.target_amount * 100) if event.target_amount > 0 else 0
                    progress_bar = "🟩" * int(progress // 10) + "⬜" * (10 - int(progress // 10))
                    response += f"🎯 **{event.title}**\n"
                    response += f"   Progress: RM {event.current_amount:,.2f} / RM {event.target_amount:,.2f}\n"
                    response += f"   {progress_bar} {progress:.1f}%\n"
                    if event.end_date:
                        response += f"   📅 Ends: {event.end_date}\n"
                    response += "\n"
                
                return {
                    'message': response,
                    'suggestions': ['How to donate?', 'Payment methods', 'Event details', 'Donation history']
                }
            return {
                'message': "📭 **No Active Events**\n\nThere are no active donation events at the moment. New events are regularly added, so please check back soon!\n\nYou can also contact the administration for information about upcoming fundraising campaigns.",
                'suggestions': ['Contact admin', 'Notification settings', 'Past events', 'How to suggest event?']
            }
        
        elif 'how' in message and ('donate' in message or 'contribute' in message):
            return {
                'message': "💝 **How to Make a Donation:**\n\n📋 **Step-by-Step Process:**\n1. Browse available donation events\n2. Select an event you'd like to support\n3. Choose your donation amount\n4. Provide your contact details\n5. Select payment method\n6. Complete the payment\n7. Receive confirmation & receipt\n\n💳 **Payment Methods:**\n• Credit/Debit Card\n• Bank Transfer\n• Online Banking\n• Cash (at office)\n\nReady to make a difference?",
                'suggestions': ['Show current events', 'Payment methods', 'Donation amounts', 'Tax benefits']
            }
        
        elif 'history' in message or 'my donations' in message:
            if user and user.is_authenticated:
                # Get user's donation history
                donations = Donation.objects.filter(donor_email=user.email).order_by('-created_at')[:5]
                if donations.exists():
                    response = f"📊 **Your Donation History:**\n\n"
                    total_donated = sum(d.amount for d in donations)
                    for donation in donations:
                        response += f"💰 RM {donation.amount} - {donation.event.title}\n"
                        response += f"   📅 {donation.created_at.strftime('%d %b %Y')}\n\n"
                    response += f"🎯 **Total Contributed**: RM {total_donated:,.2f}\n\nThank you for your generous support! 🙏"
                    return {
                        'message': response,
                        'suggestions': ['Download receipts', 'Current events', 'Impact report']
                    }
                else:
                    return {
                        'message': "📭 You haven't made any donations yet. Would you like to explore current donation opportunities?",
                        'suggestions': ['Show current events', 'How to donate?', 'Why donate?']
                    }
            else:
                return {
                    'message': "🔐 Please log in to view your donation history.",
                    'suggestions': ['Login', 'Show current events']
                }
        
        return {
            'message': "💰 **Donation Help**\n\nI can help you with:\n• Current donation events\n• How to make donations\n• Payment methods\n• Donation history\n• Impact reports\n\nWhat would you like to know?",
            'suggestions': ['Show current events', 'How to donate?', 'Payment methods', 'My donations']
        }

    def _handle_fees_query(self, message, user, question_type='general'):
        """Handle fee-related queries with real database integration"""
        from myapp.models import Student, FeeStatus, Payment, FeeStructure
        
        if user and user.is_authenticated:
            try:
                # Try to get student profile
                student = None
                if hasattr(user, 'myapp_profile') and user.myapp_profile.role == 'student':
                    student = user.myapp_profile.student
                elif hasattr(user, 'student'):
                    student = user.student
                
                if student:
                    if 'check' in message or 'status' in message or 'my fees' in message:
                        # Get student's fee status
                        fee_statuses = FeeStatus.objects.filter(
                            student=student, 
                            status__in=['pending', 'overdue']
                        ).select_related('fee_structure__category').order_by('-due_date')
                        
                        if fee_statuses.exists():
                            response = f"📋 **Fee Status for {student.first_name} {student.last_name}**\n\n"
                            total_due = 0
                            for status in fee_statuses[:5]:
                                status_icon = "🔴" if status.status == 'overdue' else "🟡"
                                response += f"{status_icon} **{status.fee_structure.category.name}**: RM {status.amount}\n"
                                response += f"   Due: {status.due_date} ({status.get_status_display()})\n\n"
                                total_due += status.amount
                            
                            response += f"💰 **Total Outstanding**: RM {total_due:.2f}"
                            
                            return {
                                'message': response,
                                'suggestions': ['How to make payment?', 'Payment methods', 'Apply for waiver', 'Payment history']
                            }
                        else:
                            # Check recent payments
                            recent_payments = Payment.objects.filter(
                                student=student, 
                                status='completed'
                            ).order_by('-payment_date')[:3]
                            
                            if recent_payments.exists():
                                response = f"✅ **Great news {student.first_name}!** All your fees are up to date!\n\n"
                                response += "📋 **Recent Payments:**\n"
                                for payment in recent_payments:
                                    response += f"• RM {payment.amount} - {payment.payment_date}\n"
                            else:
                                response = "✅ No outstanding fees found. You're all caught up!"
                            
                            return {
                                'message': response,
                                'suggestions': ['View payment history', 'Download receipt', 'Fee structure info']
                            }
                    
                    elif 'payment' in message and ('how' in message or 'method' in message):
                        return {
                            'message': "💳 **Payment Methods Available:**\n\n🏦 **Bank Transfer**\n💰 **Cash** (at school office)\n🌐 **Online Payment**\n\n📍 **How to Pay:**\n1. Go to School Fees section\n2. Select your outstanding fees\n3. Choose payment method\n4. Complete payment\n5. Download receipt\n\nNeed help with a specific payment method?",
                            'suggestions': ['Bank transfer details', 'Online payment guide', 'Cash payment info', 'Payment problems']
                        }
                    
                    elif 'waiver' in message or 'discount' in message:
                        return {
                            'message': "🎓 **Fee Waiver & Discount Options:**\n\n📋 **Available Types:**\n• Percentage-based discount (10-50%)\n• Fixed amount discount\n• Full fee waiver\n• Hardship assistance\n\n📝 **How to Apply:**\n1. Fill out waiver application form\n2. Provide supporting documents\n3. Submit for review\n4. Wait for approval notification\n\nWould you like to start an application?",
                            'suggestions': ['Apply for waiver', 'Required documents', 'Check application status', 'Eligibility criteria']
                        }
                    
                    elif 'history' in message or 'past' in message:
                        payments = Payment.objects.filter(student=student, status='completed').order_by('-payment_date')[:5]
                        if payments.exists():
                            response = f"📊 **Payment History for {student.first_name}**\n\n"
                            for payment in payments:
                                response += f"💰 RM {payment.amount} - {payment.payment_date}\n"
                                response += f"   Method: {payment.get_payment_method_display()}\n\n"
                            return {
                                'message': response,
                                'suggestions': ['Download receipt', 'View all payments', 'Current fee status']
                            }
                        else:
                            return {
                                'message': "No payment history found. You haven't made any payments yet.",
                                'suggestions': ['Check current fees', 'How to make payment?']
                            }
                
            except Exception as e:
                print(f"Error in fee query: {e}")
            
            # General fee information for authenticated users
            return {
                'message': "🏫 **School Fees Help**\n\nI can help you with:\n• Check your fee status\n• Payment methods and guides\n• Apply for fee waivers\n• View payment history\n• Download receipts\n\nWhat would you like to know?",
                'suggestions': ['Check my fees', 'Payment methods', 'Apply for waiver', 'Payment history']
            }
        
        # For non-authenticated users
        return {
            'message': "🔐 **Login Required**\n\nTo check your fees and make payments, please log in to your account first.\n\n📋 **General Fee Information:**\n• School fees vary by form/grade level\n• Multiple payment methods available\n• Fee waivers available for eligible students\n• Online payment system available 24/7",
            'suggestions': ['Login to account', 'Fee structure info', 'Payment methods', 'How to register?']
        }

    def _handle_events_query(self, message, user):
        """Handle event-related queries"""
        if 'upcoming' in message or 'coming' in message:
            upcoming_events = DonationEvent.objects.filter(
                start_date__gte=timezone.now().date()
            ).order_by('start_date')[:3]
            
            if upcoming_events.exists():
                response = "Here are the upcoming events:\n"
                for event in upcoming_events:
                    response += f"- {event.title} (Starts: {event.start_date})\n"
                return {
                    'message': response,
                    'suggestions': ['Tell me more about an event', 'How to participate']
                }
            
            return {
                'message': "There are no upcoming events scheduled at the moment.",
                'suggestions': ['Check current events', 'When will new events be available?']
            }
        
        return {
            'message': "I can help you find information about school events. Would you like to know about upcoming or current events?",
            'suggestions': ['Show upcoming events', 'Show current events', 'How to participate']
        }

    def _handle_waqaf_query(self, message, user):
        """Handle waqaf-related queries"""
        if 'what' in message and 'waqaf' in message:
            return {
                'message': "Waqaf is an Islamic endowment of property to be held in trust and used for charitable or religious purposes. It is a form of continuous charity that benefits the community. Would you like to know more about how to contribute to waqaf?",
                'suggestions': ['How can I contribute to waqaf?', 'What are the benefits of waqaf?', 'Show me available waqaf assets']
            }
        
        if 'contribute' in message or 'how to' in message:
            return {
                'message': "You can contribute to waqaf by:\n1. Selecting a waqaf asset\n2. Choosing the number of slots\n3. Providing your details\n4. Making the payment\nWould you like to see the available waqaf assets?",
                'suggestions': ['Show me available assets', 'What are the slot prices?', 'How are waqaf funds used?']
            }
        
        if 'benefit' in message or 'purpose' in message:
            return {
                'message': "Waqaf properties provide sustainable benefits to the community, including:\n- Education support\n- Healthcare services\n- Religious facilities\n- Community development\nYour contribution creates lasting impact for generations to come.",
                'suggestions': ['How can I contribute?', 'Show me success stories', 'What assets are available?']
            }
        
        return {
            'message': "I can help you with waqaf-related information. Would you like to know about what waqaf is, how to contribute, or see available assets?",
            'suggestions': ['What is waqaf?', 'How to contribute', 'Show available assets']
        }

    def _get_default_response(self):
        """Generate default response for unrecognized queries"""
        return {
            'message': "I'm not sure I understand. I can help you with:\n- Donations and fundraising\n- School fees and payments\n- Waqaf and endowments\n- School events and activities\n\nWhat would you like to know about?",
            'suggestions': [
                'Tell me about donations',
                'Check my fees',
                'What is waqaf?',
                'Show upcoming events'
            ]
        }

class DonorEngagementService:
    def __init__(self):
        self.openai_client = OpenAI()
        
    def generate_thank_you_message(self, donor_name, amount, event_title, impact_details):
        """Generate a personalized thank you message for donors."""
        prompt = f"""
        Generate a warm, personalized thank you message for a donor with the following details:
        - Donor Name: {donor_name}
        - Donation Amount: ${amount}
        - Event: {event_title}
        - Impact: {impact_details}
        
        The message should be:
        - Personal and heartfelt
        - Include specific impact details
        - Be concise (2-3 sentences)
        - End with a call to action
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_impact_report(self, event, donation):
        """Generate a detailed impact report for a donation."""
        prompt = f"""
        Create a detailed impact report for a donation with the following details:
        - Event: {event.title}
        - Donation Amount: ${donation.amount}
        - Event Description: {event.description}
        - Current Progress: ${event.current_amount} of ${event.target_amount}
        
        Include:
        - Specific impact of the donation
        - Progress towards the goal
        - How the donation helps
        - Future impact
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_reengagement_suggestion(self, donor, event):
        """Generate personalized re-engagement suggestions."""
        prompt = f"""
        Create a personalized re-engagement message for a donor with the following details:
        - Donor Name: {donor.username}
        - Previous Event: {event.title}
        - Event Progress: ${event.current_amount} of ${event.target_amount}
        
        The message should:
        - Acknowledge their previous support
        - Show current progress
        - Suggest ways to help
        - Be encouraging but not pushy
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_anniversary_message(self, donor, event, days_since_donation):
        """Generate a donation anniversary message."""
        prompt = f"""
        Create a warm anniversary message for a donor with the following details:
        - Donor Name: {donor.username}
        - Event: {event.title}
        - Days Since Donation: {days_since_donation}
        - Current Progress: ${event.current_amount} of ${event.target_amount}
        
        The message should:
        - Celebrate the anniversary
        - Show current impact
        - Be personal and appreciative
        - Include a gentle call to action
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip() 