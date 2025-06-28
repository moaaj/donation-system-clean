from textblob import TextBlob
import re
from django.db.models import Q
from myapp.models import DonationEvent, DonationCategory
from datetime import datetime, timedelta

class DonationChatbot:
    def __init__(self):
        self.greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        self.farewells = ['bye', 'goodbye', 'see you', 'thank you', 'thanks']
        
    def process_message(self, message, user=None):
        """Process user message and return appropriate response"""
        message = message.lower().strip()
        
        # Check for greetings
        if any(greeting in message for greeting in self.greetings):
            return self._get_greeting_response()
            
        # Check for farewells
        if any(farewell in message for farewell in self.farewells):
            return self._get_farewell_response()
            
        # Process donation-related queries
        if 'donation' in message or 'donate' in message:
            return self._handle_donation_query(message)
            
        # Process event-related queries
        if 'event' in message or 'campaign' in message:
            return self._handle_event_query(message)
            
        # Process payment-related queries
        if 'payment' in message or 'pay' in message or 'how to pay' in message:
            return self._handle_payment_query(message)
            
        # Process category-related queries
        if 'category' in message or 'type' in message:
            return self._handle_category_query(message)
            
        # Default response for unrecognized queries
        return self._get_default_response()
        
    def _get_greeting_response(self):
        """Return a greeting response"""
        responses = [
            "Hello! I'm your donation assistant. How can I help you today?",
            "Hi there! I can help you with donations, events, and payments. What would you like to know?",
            "Welcome! I'm here to assist you with any donation-related questions."
        ]
        return {
            'type': 'greeting',
            'message': responses[0],
            'suggestions': [
                'Tell me about current events',
                'How can I make a donation?',
                'What payment methods do you accept?'
            ]
        }
        
    def _get_farewell_response(self):
        """Return a farewell response"""
        responses = [
            "Thank you for chatting! Feel free to return if you have more questions.",
            "Goodbye! Have a great day!",
            "Thanks for your time! Come back anytime you need help."
        ]
        return {
            'type': 'farewell',
            'message': responses[0]
        }
        
    def _handle_donation_query(self, message):
        """Handle donation-related queries"""
        if 'how' in message and 'donate' in message:
            return {
                'type': 'donation_info',
                'message': "You can make a donation by:\n1. Selecting an event\n2. Choosing your donation amount\n3. Providing your details\n4. Selecting a payment method\nWould you like me to show you current events?",
                'suggestions': ['Show me current events', 'What payment methods do you accept?']
            }
        return {
            'type': 'donation_info',
            'message': "I can help you with donations. Would you like to know how to donate or see current events?",
            'suggestions': ['How do I donate?', 'Show me current events']
        }
        
    def _handle_event_query(self, message):
        """Handle event-related queries"""
        # Get active events
        active_events = DonationEvent.objects.filter(
            is_active=True,
            end_date__gte=datetime.now().date()
        ).order_by('-created_at')[:5]
        
        if not active_events:
            return {
                'type': 'event_info',
                'message': "There are no active events at the moment. Please check back later!",
                'suggestions': ['How do I donate?', 'Tell me about categories']
            }
            
        event_list = "\n".join([f"- {event.title}: ${event.current_amount} / ${event.target_amount}" for event in active_events])
        
        return {
            'type': 'event_info',
            'message': f"Here are the current active events:\n{event_list}\nWould you like to know more about any specific event?",
            'suggestions': [event.title for event in active_events[:3]]
        }
        
    def _handle_payment_query(self, message):
        """Handle payment-related queries"""
        payment_methods = ['Cash', 'Bank Transfer', 'Online Payment']
        return {
            'type': 'payment_info',
            'message': f"We accept the following payment methods:\n" + "\n".join([f"- {method}" for method in payment_methods]),
            'suggestions': ['How do I donate?', 'Show me current events']
        }
        
    def _handle_category_query(self, message):
        """Handle category-related queries"""
        categories = DonationCategory.objects.filter(is_active=True)
        if not categories:
            return {
                'type': 'category_info',
                'message': "There are no active donation categories at the moment.",
                'suggestions': ['Show me current events', 'How do I donate?']
            }
            
        category_list = "\n".join([f"- {category.name}: {category.description[:100]}..." for category in categories])
        
        return {
            'type': 'category_info',
            'message': f"Here are our donation categories:\n{category_list}",
            'suggestions': [category.name for category in categories[:3]]
        }
        
    def _get_default_response(self):
        """Return a default response for unrecognized queries"""
        return {
            'type': 'default',
            'message': "I'm not sure I understand. I can help you with:\n- Making donations\n- Current events\n- Payment methods\n- Donation categories\nWhat would you like to know?",
            'suggestions': [
                'How do I donate?',
                'Show me current events',
                'What payment methods do you accept?'
            ]
        } 