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
        self.greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        self.farewells = ['bye', 'goodbye', 'see you', 'farewell', 'thank you', 'thanks']
        
        # Keywords for module identification
        self.module_keywords = {
            'donation': ['donation', 'donate', 'fundraising', 'contribute', 'give', 'charity'],
            'fees': ['fee', 'fees', 'payment', 'pay', 'school fees', 'tuition', 'payment status'],
            'events': ['event', 'events', 'activity', 'activities', 'schedule', 'calendar'],
            'waqaf': ['waqaf', 'endowment', 'islamic endowment', 'religious endowment', 'charitable trust']
        }
        
        # Download required NLTK data
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        self.sia = SentimentIntensityAnalyzer()

    def process_message(self, message, user=None):
        """Process user message and return appropriate response"""
        message = message.lower().strip()
        
        # Check for greetings
        if any(greeting in message for greeting in self.greetings):
            return self._get_greeting_response()
        
        # Check for farewells
        if any(farewell in message for farewell in self.farewells):
            return self._get_farewell_response()
        
        # Identify module and handle accordingly
        module = self._identify_module(message)
        if module == 'donation':
            return self._handle_donation_query(message, user)
        elif module == 'fees':
            return self._handle_fees_query(message, user)
        elif module == 'events':
            return self._handle_events_query(message, user)
        elif module == 'waqaf':
            return self._handle_waqaf_query(message, user)
        
        return self._get_default_response()

    def _identify_module(self, message):
        """Identify which module the query belongs to"""
        for module, keywords in self.module_keywords.items():
            if any(keyword in message for keyword in keywords):
                return module
        return None

    def _get_greeting_response(self):
        """Generate greeting response"""
        return {
            'message': "Hello! I'm your AI assistant. I can help you with donations, school fees, waqaf, and events. How can I assist you today?",
            'suggestions': [
                'Tell me about current donation events',
                'How do I check my school fees?',
                'What is waqaf?',
                'What events are coming up?'
            ]
        }

    def _get_farewell_response(self):
        """Generate farewell response"""
        return {
            'message': "Thank you for chatting with me! If you need any help with donations, fees, or events, feel free to ask anytime.",
            'suggestions': []
        }

    def _handle_donation_query(self, message, user):
        """Handle donation-related queries"""
        if 'current' in message or 'active' in message:
            active_events = DonationEvent.objects.filter(is_active=True)
            if active_events.exists():
                response = "Here are the current donation events:\n"
                for event in active_events[:3]:
                    response += f"- {event.title}: ${event.current_amount} / ${event.target_amount}\n"
                return {
                    'message': response,
                    'suggestions': ['How do I make a donation?', 'What payment methods are accepted?']
                }
            return {
                'message': "There are no active donation events at the moment.",
                'suggestions': ['When will new events be available?']
            }
        
        return {
            'message': "I can help you with donations. Would you like to know about current events or how to make a donation?",
            'suggestions': ['Show current events', 'How to donate', 'Payment methods']
        }

    def _handle_fees_query(self, message, user):
        """Handle fee-related queries"""
        if user and user.is_authenticated:
            if 'check' in message or 'status' in message:
                # Get student's fee status
                try:
                    student = user.student
                    fee_statuses = FeeStatus.objects.filter(student=student).order_by('-due_date')
                    if fee_statuses.exists():
                        response = "Here's your fee status:\n"
                        for status in fee_statuses[:3]:
                            response += f"- {status.fee_structure.category.name}: ${status.amount} (Due: {status.due_date})\n"
                        return {
                            'message': response,
                            'suggestions': ['How do I make a payment?', 'View payment history', 'Apply for fee waiver']
                        }
                except:
                    pass
            
            if 'waiver' in message or 'discount' in message:
                return {
                    'message': "You can apply for a fee waiver or discount through the fee waiver form. The available types are:\n- Percentage-based discount\n- Fixed amount discount\n- Full waiver\nWould you like to apply for a waiver?",
                    'suggestions': ['Apply for waiver', 'Check eligibility', 'View waiver status']
                }
            
            return {
                'message': "I can help you check your fee status, make payments, or apply for waivers. What would you like to do?",
                'suggestions': ['Check fee status', 'Make a payment', 'Apply for waiver']
            }
        
        return {
            'message': "Please log in to check your fee status, make payments, or apply for waivers.",
            'suggestions': ['Login', 'Register']
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