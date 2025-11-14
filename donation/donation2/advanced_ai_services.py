"""
Advanced AI Services - World-Class AI Assistant
Making the most accurate and lovable AI bot in the world!
"""

import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from django.contrib.auth.models import User
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import random

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
    nltk.data.find('punkt')
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('vader_lexicon')
    nltk.download('punkt')
    nltk.download('stopwords')

class WorldClassAIAssistant:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.conversation_memory = {}  # Store conversation context
        self.user_preferences = {}     # Store user preferences
        
        # Personality traits
        self.personality = {
            'friendly': True,
            'helpful': True,
            'patient': True,
            'encouraging': True,
            'professional': True,
            'empathetic': True
        }
        
        # Enhanced multilingual support
        self.languages = {
            'en': {
                'greetings': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings'],
                'farewells': ['bye', 'goodbye', 'see you', 'farewell', 'take care', 'until next time'],
                'thanks': ['thank you', 'thanks', 'appreciate', 'grateful'],
                'help': ['help', 'assist', 'support', 'guide', 'explain']
            },
            'ms': {
                'greetings': ['halo', 'hai', 'selamat pagi', 'selamat petang', 'selamat malam'],
                'farewells': ['selamat tinggal', 'jumpa lagi', 'sampai jumpa'],
                'thanks': ['terima kasih', 'thanks', 'syukur'],
                'help': ['tolong', 'bantuan', 'bantu', 'sokongan']
            }
        }
        
        # Advanced keyword mapping with context
        self.smart_keywords = {
            'fees': {
                'primary': ['fee', 'fees', 'payment', 'pay', 'yuran', 'bayar', 'bayaran'],
                'actions': ['check', 'status', 'semak', 'lihat'],
                'problems': ['overdue', 'late', 'problem', 'issue', 'masalah', 'lewat'],
                'methods': ['how', 'method', 'cara', 'bagaimana']
            },
            'donations': {
                'primary': ['donation', 'donate', 'contribute', 'sumbangan', 'derma', 'tabung'],
                'actions': ['give', 'support', 'help', 'beri', 'sokong'],
                'events': ['event', 'campaign', 'fundraising', 'acara', 'kempen']
            },
            'waqaf': {
                'primary': ['waqaf', 'wakaf', 'endowment', 'islamic endowment'],
                'concepts': ['charity', 'religious', 'islamic', 'muslim', 'islam'],
                'actions': ['contribute', 'invest', 'support', 'sumbang']
            },
            'student': {
                'primary': ['student', 'students', 'pelajar', 'murid'],
                'actions': ['register', 'enroll', 'daftar', 'masuk'],
                'info': ['information', 'details', 'profile', 'maklumat']
            }
        }
        
        # Emotional responses for different situations
        self.emotional_responses = {
            'frustrated': {
                'detection': ['problem', 'issue', 'error', 'not working', 'broken', 'masalah'],
                'response_tone': 'empathetic_helpful'
            },
            'confused': {
                'detection': ['confused', 'don\'t understand', 'unclear', 'keliru'],
                'response_tone': 'patient_explanatory'
            },
            'happy': {
                'detection': ['great', 'awesome', 'perfect', 'excellent', 'bagus'],
                'response_tone': 'enthusiastic'
            },
            'urgent': {
                'detection': ['urgent', 'quickly', 'asap', 'emergency', 'segera', 'cepat'],
                'response_tone': 'immediate_action'
            }
        }

    def process_message(self, message, user=None, session_id=None):
        """Advanced message processing with context awareness"""
        original_message = message
        message_lower = message.lower().strip()
        
        # Initialize or get conversation context
        if session_id:
            if session_id not in self.conversation_memory:
                self.conversation_memory[session_id] = {
                    'history': [],
                    'context': {},
                    'user_mood': 'neutral',
                    'preferred_language': 'en'
                }
            context = self.conversation_memory[session_id]
            context['history'].append({'user': original_message, 'timestamp': datetime.now()})
        else:
            context = {'history': [], 'context': {}, 'user_mood': 'neutral', 'preferred_language': 'en'}
        
        # Detect language preference
        detected_lang = self._detect_language(message_lower)
        context['preferred_language'] = detected_lang
        
        # Analyze sentiment and emotion
        sentiment = self.sia.polarity_scores(message_lower)
        emotion = self._detect_emotion(message_lower)
        context['user_mood'] = emotion
        
        # Handle different types of messages
        if self._is_greeting(message_lower, detected_lang):
            response = self._generate_personalized_greeting(user, context)
        elif self._is_farewell(message_lower, detected_lang):
            response = self._generate_farewell(user, context)
        elif self._is_thanks(message_lower, detected_lang):
            response = self._generate_thanks_response(context)
        else:
            # Process complex queries with context
            response = self._process_complex_query(message_lower, user, context, sentiment)
        
        # Store response in context
        if session_id:
            context['history'].append({'bot': response, 'timestamp': datetime.now()})
        
        return response

    def _detect_language(self, message):
        """Detect user's preferred language"""
        malay_words = ['saya', 'apa', 'bagaimana', 'bila', 'mana', 'kenapa', 'tolong', 'terima kasih']
        malay_count = sum(1 for word in malay_words if word in message)
        return 'ms' if malay_count > 0 else 'en'

    def _detect_emotion(self, message):
        """Detect user's emotional state"""
        for emotion, data in self.emotional_responses.items():
            if any(keyword in message for keyword in data['detection']):
                return emotion
        return 'neutral'

    def _is_greeting(self, message, lang='en'):
        """Check if message is a greeting"""
        greetings = self.languages[lang]['greetings'] + self.languages['en']['greetings']
        return any(greeting in message for greeting in greetings)

    def _is_farewell(self, message, lang='en'):
        """Check if message is a farewell"""
        farewells = self.languages[lang]['farewells'] + self.languages['en']['farewells']
        return any(farewell in message for farewell in farewells)

    def _is_thanks(self, message, lang='en'):
        """Check if message is expressing gratitude"""
        thanks = self.languages[lang]['thanks'] + self.languages['en']['thanks']
        return any(thank in message for thank in thanks)

    def _generate_personalized_greeting(self, user, context):
        """Generate highly personalized greeting"""
        lang = context.get('preferred_language', 'en')
        
        # Time-based greetings
        current_hour = datetime.now().hour
        if current_hour < 12:
            time_greeting = "Good morning" if lang == 'en' else "Selamat pagi"
        elif current_hour < 17:
            time_greeting = "Good afternoon" if lang == 'en' else "Selamat petang"
        else:
            time_greeting = "Good evening" if lang == 'en' else "Selamat malam"
        
        if user and user.is_authenticated:
            name = user.first_name if user.first_name else user.username
            
            # Check if returning user
            if len(context.get('history', [])) > 2:
                greeting = f"{time_greeting} {name}! 👋 Welcome back! I'm so happy to see you again!"
            else:
                greeting = f"{time_greeting} {name}! 👋 I'm your personal AI assistant, and I'm absolutely delighted to meet you!"
            
            # Add personalized context based on user role
            try:
                if hasattr(user, 'myapp_profile'):
                    role = user.myapp_profile.role
                    if role == 'student':
                        greeting += f"\n\n🎓 I see you're a student! I'm here to help you with everything - from checking your fees to understanding payment methods."
                    elif role == 'parent':
                        greeting += f"\n\n👨‍👩‍👧‍👦 As a parent, I can help you manage your children's school fees, track payments, and stay updated on everything!"
                    elif 'admin' in role:
                        greeting += f"\n\n👨‍💼 Hello admin! I can help you with system management, reports, analytics, and any administrative tasks."
            except:
                pass
        else:
            greeting = f"{time_greeting}! 👋 I'm your friendly AI assistant, and I'm absolutely thrilled to help you today!"
        
        greeting += f"\n\n✨ **I'm here to make your experience amazing!** ✨\n\n🏫 **School Fees & Payments** - Check status, make payments, get help\n💰 **Donations & Fundraising** - Support causes, track contributions\n🕌 **Waqaf (Islamic Endowment)** - Learn and contribute to lasting charity\n📅 **Events & Activities** - Stay updated on school happenings\n👨‍🎓 **Student Services** - Registration, information, support\n\n💡 **Pro Tip**: I understand both English and Bahasa Malaysia, so feel free to chat in whichever language you're comfortable with!\n\n🤗 What can I help you with today? I'm excited to assist you!"
        
        suggestions = [
            '🔍 Check my fees',
            '💰 Show donation events',
            '🕌 What is waqaf?',
            '📅 Upcoming events',
            '❓ Help me',
            '🏠 Go to homepage'
        ]
        
        return {
            'message': greeting,
            'suggestions': suggestions,
            'type': 'greeting',
            'emotion': 'enthusiastic'
        }

    def _generate_farewell(self, user, context):
        """Generate warm farewell message"""
        lang = context.get('preferred_language', 'en')
        
        farewells = [
            "🌟 It's been wonderful chatting with you! Thank you for letting me help you today.",
            "✨ I hope I was able to help you! Feel free to come back anytime you need assistance.",
            "🤗 Thank you for the great conversation! I'm always here when you need me.",
            "💫 It was my pleasure helping you! Have an absolutely fantastic day ahead!"
        ]
        
        if lang == 'ms':
            farewells.extend([
                "🌟 Terima kasih kerana berbual dengan saya! Saya harap dapat membantu anda.",
                "✨ Saya harap saya dapat membantu! Jangan segan untuk kembali bila-bila masa.",
                "🤗 Terima kasih atas perbualan yang menarik! Saya sentiasa di sini untuk anda."
            ])
        
        farewell_msg = random.choice(farewells)
        
        # Add personalized touch
        if user and user.is_authenticated:
            name = user.first_name if user.first_name else user.username
            farewell_msg += f"\n\n👋 Take care, {name}! I'll be here whenever you need me. Have a wonderful day! 🌈"
        else:
            farewell_msg += "\n\n👋 Take care! Remember, I'm always here to help you 24/7. Have a beautiful day! 🌈"
        
        return {
            'message': farewell_msg,
            'suggestions': [],
            'type': 'farewell',
            'emotion': 'warm'
        }

    def _generate_thanks_response(self, context):
        """Generate response to user's thanks"""
        responses = [
            "🤗 You're absolutely welcome! It makes me so happy to help you!",
            "✨ My pleasure! That's what I'm here for - to make your life easier!",
            "💖 Aww, thank you! Helping amazing people like you is what I love most!",
            "🌟 You're so kind! I'm always delighted to assist you!",
            "😊 No need to thank me - seeing you succeed makes my day!"
        ]
        
        return {
            'message': random.choice(responses) + "\n\n💡 Is there anything else I can help you with? I'm here and ready to assist! 🚀",
            'suggestions': [
                '🔍 Check something else',
                '💰 Donation events',
                '📊 View reports',
                '❓ More help',
                '🏠 Go home'
            ],
            'type': 'gratitude',
            'emotion': 'happy'
        }

    def _process_complex_query(self, message, user, context, sentiment):
        """Process complex queries with advanced understanding"""
        # Identify intent and entities
        intent = self._identify_intent(message)
        entities = self._extract_entities(message)
        modules = self._identify_modules(message)
        
        # Handle based on primary intent
        if intent == 'check_status':
            return self._handle_status_check(message, user, entities, context)
        elif intent == 'make_payment':
            return self._handle_payment_guidance(message, user, entities, context)
        elif intent == 'get_information':
            return self._handle_information_request(message, user, entities, modules, context)
        elif intent == 'solve_problem':
            return self._handle_problem_solving(message, user, entities, context, sentiment)
        elif intent == 'navigate':
            return self._handle_navigation_help(message, user, entities, context)
        else:
            return self._handle_general_query(message, user, modules, context, sentiment)
    
    def _handle_general_query(self, message, user, modules, context, sentiment):
        """Handle general queries with intelligence"""
        # If no specific modules identified, provide general help
        if not modules:
            return self._get_intelligent_response(message, user)
        
        # Handle multiple modules
        if len(modules) > 1:
            response = "🎯 **I can help you with multiple things!**\n\n"
            response += "I noticed you're asking about:\n"
            for module in modules:
                if module == 'fees':
                    response += "• 🏫 **School Fees** - Check status, make payments, get help\n"
                elif module == 'donation':
                    response += "• 💰 **Donations** - Current events, how to donate, history\n"
                elif module == 'waqaf':
                    response += "• 🕌 **Waqaf** - Islamic endowment, assets, contributions\n"
                elif module == 'student':
                    response += "• 👨‍🎓 **Student Services** - Registration, information, support\n"
            
            response += "\nWhich one would you like to focus on first? I'm excited to help! 🚀"
            
            suggestions = []
            for module in modules:
                if module == 'fees':
                    suggestions.append('🔍 Check my fees')
                elif module == 'donation':
                    suggestions.append('💰 Show donations')
                elif module == 'waqaf':
                    suggestions.append('🕌 About waqaf')
                elif module == 'student':
                    suggestions.append('👨‍🎓 Student info')
            
            return {
                'message': response,
                'suggestions': suggestions,
                'type': 'multi_module',
                'emotion': 'enthusiastic'
            }
        
        # Single module - provide specific help
        module = modules[0]
        if module == 'fees':
            return self._handle_fees_query(message, user, 'general')
        elif module == 'donation':
            return self._handle_donation_query(message, user, 'general')
        elif module == 'waqaf':
            return self._handle_waqaf_query(message, user, 'general')
        elif module == 'student':
            return self._handle_student_query(message, user, 'general')
        
        return self._get_intelligent_response(message, user)

    def _handle_navigation_help(self, message, user, entities, context):
        """Help users navigate the system"""
        return {
            'message': "🧭 **Navigation Help**\n\nI can guide you anywhere in the system! 🚀\n\n📍 **Popular Destinations:**\n• 🏫 School Fees Dashboard\n• 💰 Donation Events\n• 🕌 Waqaf Assets\n• 👨‍🎓 Student Management\n• 📊 Reports & Analytics\n\n🎯 **Just tell me where you want to go, and I'll guide you there!**",
            'suggestions': [
                '🏫 Go to fees',
                '💰 Go to donations', 
                '🕌 Go to waqaf',
                '👨‍🎓 Student area',
                '🏠 Homepage'
            ],
            'type': 'navigation',
            'emotion': 'helpful'
        }

    def _handle_waqaf_query(self, message, user, question_type='general'):
        """Handle waqaf queries with comprehensive information"""
        return self._get_waqaf_information(message, context={'preferred_language': 'en'})

    def _handle_events_query(self, message, user, question_type='general'):
        """Handle event queries"""
        from myapp.models import DonationEvent
        
        if 'upcoming' in message or 'coming' in message:
            upcoming_events = DonationEvent.objects.filter(
                start_date__gte=timezone.now().date()
            ).order_by('start_date')[:3]
            
            if upcoming_events.exists():
                response = "📅 **Upcoming Events - Don't Miss Out!** 🎉\n\n"
                for i, event in enumerate(upcoming_events, 1):
                    days_until = (event.start_date - timezone.now().date()).days
                    response += f"**{i}. {event.title}** 🎯\n"
                    response += f"   📅 **Starts**: {event.start_date.strftime('%d %b %Y')}\n"
                    if days_until == 0:
                        response += f"   🚨 **Starting TODAY!** Don't miss it!\n"
                    elif days_until == 1:
                        response += f"   ⏰ **Starting TOMORROW!** Get ready!\n"
                    else:
                        response += f"   ⏰ **In {days_until} days** - Mark your calendar!\n"
                    response += f"   🎯 **Target**: RM {event.target_amount:,.2f}\n\n"
                
                return {
                    'message': response,
                    'suggestions': [
                        '💰 How to participate?',
                        '📊 Event details',
                        '🔔 Set reminder',
                        '📞 Contact organizer'
                    ],
                    'type': 'upcoming_events',
                    'emotion': 'exciting'
                }
        
        return {
            'message': "📅 **Events & Activities**\n\nI can help you with:\n• Upcoming events and activities\n• Current donation campaigns\n• Event details and schedules\n• How to participate\n• Event notifications\n\nWhat would you like to know? 🎉",
            'suggestions': [
                '📅 Upcoming events',
                '💰 Current campaigns',
                '🎯 How to participate',
                '🔔 Notifications'
            ],
            'type': 'events_info',
            'emotion': 'informative'
        }

    def _identify_intent(self, message):
        """Identify user's intent with high accuracy"""
        intent_patterns = {
            'check_status': [
                r'\b(check|view|see|show|status|semak|lihat|tunjuk)\b.*\b(fee|payment|balance|yuran|bayaran)\b',
                r'\b(my|saya)\b.*\b(fee|payment|status|yuran|bayaran)\b',
                r'\b(how much|berapa|amount|jumlah)\b.*\b(owe|due|perlu bayar)\b'
            ],
            'make_payment': [
                r'\b(pay|make payment|bayar|buat bayaran)\b',
                r'\b(how to pay|cara bayar|payment method|kaedah bayaran)\b',
                r'\b(want to pay|nak bayar|hendak bayar)\b'
            ],
            'get_information': [
                r'\b(what|apa|apakah)\b.*\b(is|ialah|adalah)\b',
                r'\b(tell me|beritahu|explain|terangkan)\b',
                r'\b(information|maklumat|details|butiran)\b'
            ],
            'solve_problem': [
                r'\b(problem|issue|error|masalah|ralat)\b',
                r'\b(not working|tak berfungsi|cannot|tak boleh)\b',
                r'\b(help|tolong|bantuan)\b.*\b(problem|masalah)\b'
            ],
            'navigate': [
                r'\b(where|mana|di mana)\b.*\b(find|cari|jumpa)\b',
                r'\b(how to|bagaimana|cara)\b.*\b(go|pergi|access|akses)\b',
                r'\b(take me|bawa saya|direct|arah)\b'
            ]
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return intent
        
        return 'general'

    def _extract_entities(self, message):
        """Extract important entities from the message"""
        entities = {
            'amount': None,
            'date': None,
            'student_name': None,
            'fee_type': None,
            'payment_method': None
        }
        
        # Extract amounts (RM 100, $50, 100 ringgit, etc.)
        amount_patterns = [
            r'RM\s*(\d+(?:\.\d{2})?)',
            r'\$\s*(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\s*ringgit',
            r'(\d+(?:\.\d{2})?)\s*dollar'
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities['amount'] = float(match.group(1))
                break
        
        # Extract dates
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(today|tomorrow|yesterday|hari ini|esok|semalam)',
            r'(this month|next month|bulan ini|bulan depan)'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities['date'] = match.group(1)
                break
        
        # Extract fee types
        fee_types = ['pta', 'activities', 'exams', 'dormitory', 'tuition', 'registration']
        for fee_type in fee_types:
            if fee_type in message:
                entities['fee_type'] = fee_type
                break
        
        # Extract payment methods
        payment_methods = ['cash', 'bank transfer', 'online', 'credit card', 'debit card']
        for method in payment_methods:
            if method in message:
                entities['payment_method'] = method
                break
        
        return entities

    def _handle_status_check(self, message, user, entities, context):
        """Handle status check requests with perfect accuracy"""
        from myapp.models import Student, FeeStatus, Payment
        
        if not user or not user.is_authenticated:
            return {
                'message': "🔐 **Authentication Required**\n\nTo check your personal status, I need you to log in first! Once you're logged in, I can show you:\n\n✨ **Your Personal Dashboard:**\n• 📊 Real-time fee status\n• 💰 Payment history with details\n• 🧾 Available receipts\n• 📈 Payment trends\n• 🎯 Upcoming due dates\n\nLogin now and let me give you the most accurate, up-to-date information about your account! 🚀",
                'suggestions': [
                    '🔑 Login to account',
                    '📝 Register new account',
                    '❓ General fee info',
                    '💡 How it works'
                ],
                'type': 'auth_required',
                'emotion': 'encouraging'
            }
        
        try:
            # Get student profile with multiple fallback methods
            student = None
            if hasattr(user, 'myapp_profile') and user.myapp_profile.role == 'student':
                student = user.myapp_profile.student
            elif hasattr(user, 'student'):
                student = user.student
            
            if student:
                # Get comprehensive fee status
                outstanding_fees = FeeStatus.objects.filter(
                    student=student,
                    status__in=['pending', 'overdue']
                ).select_related('fee_structure__category').order_by('due_date')
                
                completed_payments = Payment.objects.filter(
                    student=student,
                    status='completed'
                ).order_by('-payment_date')
                
                if outstanding_fees.exists():
                    # Calculate totals
                    total_outstanding = sum(fee.amount for fee in outstanding_fees)
                    overdue_count = outstanding_fees.filter(status='overdue').count()
                    
                    response = f"📊 **Fee Status for {student.first_name} {student.last_name}**\n\n"
                    
                    if overdue_count > 0:
                        response += f"🚨 **URGENT**: You have {overdue_count} overdue payment(s)!\n\n"
                    
                    response += f"💰 **Outstanding Fees**: RM {total_outstanding:,.2f}\n\n"
                    response += "📋 **Breakdown:**\n"
                    
                    for fee in outstanding_fees[:5]:
                        status_emoji = "🔴" if fee.status == 'overdue' else "🟡"
                        days_until_due = (fee.due_date - timezone.now().date()).days
                        
                        response += f"{status_emoji} **{fee.fee_structure.category.name}**: RM {fee.amount:,.2f}\n"
                        
                        if days_until_due < 0:
                            response += f"   ⏰ **{abs(days_until_due)} days overdue** - Please pay ASAP!\n"
                        elif days_until_due == 0:
                            response += f"   ⏰ **Due TODAY** - Don't miss it!\n"
                        elif days_until_due <= 7:
                            response += f"   ⏰ Due in {days_until_due} days - Pay soon!\n"
                        else:
                            response += f"   📅 Due: {fee.due_date.strftime('%d %b %Y')}\n"
                        response += "\n"
                    
                    if outstanding_fees.count() > 5:
                        response += f"... and {outstanding_fees.count() - 5} more fees\n\n"
                    
                    # Add payment encouragement
                    if overdue_count > 0:
                        response += "🎯 **Action Needed**: Please make your overdue payments as soon as possible to avoid any issues with your studies.\n\n"
                    
                    response += "💡 **Quick Actions Available:**\n• Make immediate payment\n• Set up payment plan\n• Apply for fee waiver\n• Download payment reminder"
                    
                    suggestions = [
                        '💳 How to make payment?',
                        '📋 Payment methods',
                        '🎓 Apply for waiver',
                        '📊 Payment history',
                        '🧾 Download receipt'
                    ]
                    
                    if overdue_count > 0:
                        suggestions.insert(0, '🚨 Pay overdue fees now')
                
                else:
                    # No outstanding fees - celebrate!
                    total_paid = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
                    
                    response = f"🎉 **FANTASTIC NEWS, {student.first_name}!** 🎉\n\n"
                    response += "✅ **All your fees are up to date!** You're doing amazing! 🌟\n\n"
                    
                    if completed_payments.exists():
                        response += f"💰 **Total Paid**: RM {total_paid:,.2f}\n"
                        response += f"📊 **Total Payments**: {completed_payments.count()}\n"
                        response += f"🗓️ **Last Payment**: {completed_payments.first().payment_date.strftime('%d %b %Y')}\n\n"
                        
                        response += "🏆 **You're a payment superstar!** Keep up the excellent work!\n\n"
                        response += "📋 **Recent Payments:**\n"
                        
                        for payment in completed_payments[:3]:
                            response += f"✅ RM {payment.amount:,.2f} - {payment.payment_date.strftime('%d %b %Y')}\n"
                            response += f"   Method: {payment.get_payment_method_display()}\n\n"
                    
                    suggestions = [
                        '📊 View payment history',
                        '🧾 Download receipts',
                        '💰 Donation events',
                        '📅 Upcoming events',
                        '🏠 Go to homepage'
                    ]
                
                return {
                    'message': response,
                    'suggestions': suggestions,
                    'type': 'status_check',
                    'emotion': 'informative' if outstanding_fees.exists() else 'celebratory'
                }
            
            else:
                # User is authenticated but not a student
                return {
                    'message': f"👋 Hello! I can see you're logged in, but I need to access student-specific information to check fee status.\n\n🔍 **What I can help you with:**\n• General fee information\n• Payment methods and guides\n• Donation opportunities\n• Event information\n• System navigation help\n\nWhat would you like to know about?",
                    'suggestions': [
                        '💡 General fee info',
                        '💳 Payment methods',
                        '💰 Donation events',
                        '📞 Contact admin',
                        '❓ Other help'
                    ],
                    'type': 'general_help',
                    'emotion': 'helpful'
                }
        
        except Exception as e:
            return {
                'message': f"😅 Oops! I encountered a small hiccup while checking your status, but don't worry - I'm still here to help!\n\n🔧 **What I can do right now:**\n• Provide general fee information\n• Guide you through payment processes\n• Show you donation opportunities\n• Help with navigation\n\n💪 Let's try something else! What would you like to know?",
                'suggestions': [
                    '💡 General fee info',
                    '💳 Payment guide',
                    '💰 Donations',
                    '📞 Contact support',
                    '🔄 Try again'
                ],
                'type': 'error_recovery',
                'emotion': 'apologetic_helpful'
            }

    def _handle_payment_guidance(self, message, user, entities, context):
        """Provide comprehensive payment guidance"""
        # Detect specific payment method interest
        if entities.get('payment_method'):
            method = entities['payment_method']
            return self._get_specific_payment_guide(method, user, context)
        
        # Check if user has outstanding fees
        if user and user.is_authenticated:
            try:
                if hasattr(user, 'myapp_profile') and user.myapp_profile.role == 'student':
                    from myapp.models import FeeStatus
                    student = user.myapp_profile.student
                    outstanding = FeeStatus.objects.filter(
                        student=student,
                        status__in=['pending', 'overdue']
                    ).first()
                    
                    if outstanding:
                        response = f"💳 **Perfect timing, {student.first_name}!** Let me guide you through making your payment! 🚀\n\n"
                        response += f"🎯 **Your Next Payment**: RM {outstanding.amount:,.2f}\n"
                        response += f"📋 **For**: {outstanding.fee_structure.category.name}\n"
                        response += f"📅 **Due**: {outstanding.due_date.strftime('%d %b %Y')}\n\n"
                    else:
                        response = "🎉 **Great news!** You don't have any outstanding fees right now!\n\n"
                        response += "But let me still show you how payments work for future reference! 📚\n\n"
            except:
                response = "💳 **Payment Guide** - Let me walk you through this step by step! 🚀\n\n"
        else:
            response = "💳 **Payment Guide** - I'll make this super easy for you! 🚀\n\n"
        
        response += "🌟 **Step-by-Step Payment Process:**\n\n"
        response += "**Step 1: Access Your Fees** 📊\n"
        response += "• Go to 'School Fees' section\n"
        response += "• View your outstanding fees\n"
        response += "• Select fees to pay\n\n"
        
        response += "**Step 2: Choose Payment Method** 💳\n"
        response += "• 🏦 **Bank Transfer** - Direct from your bank\n"
        response += "• 💰 **Cash** - Pay at school office\n"
        response += "• 🌐 **Online Payment** - Credit/debit card\n\n"
        
        response += "**Step 3: Complete Payment** ✅\n"
        response += "• Follow the payment instructions\n"
        response += "• Keep your reference number\n"
        response += "• Wait for confirmation\n\n"
        
        response += "**Step 4: Get Your Receipt** 🧾\n"
        response += "• Download immediately\n"
        response += "• Email to yourself\n"
        response += "• Print if needed\n\n"
        
        response += "🎯 **Pro Tips:**\n"
        response += "• Pay before due date to avoid late fees\n"
        response += "• Keep all receipts for your records\n"
        response += "• Set up payment reminders\n\n"
        
        response += "💪 **I'm here to help every step of the way!** Which payment method interests you most?"
        
        return {
            'message': response,
            'suggestions': [
                '🏦 Bank transfer guide',
                '💰 Cash payment info',
                '🌐 Online payment help',
                '🎓 Apply for waiver',
                '📞 Contact support'
            ],
            'type': 'payment_guide',
            'emotion': 'helpful_encouraging'
        }

    def _handle_information_request(self, message, user, entities, modules, context):
        """Handle information requests with comprehensive details"""
        if 'waqaf' in modules:
            return self._get_waqaf_information(message, context)
        elif 'donation' in modules:
            return self._get_donation_information(message, user, context)
        elif 'fees' in modules:
            return self._get_fee_information(message, user, context)
        elif 'student' in modules:
            return self._get_student_information(message, user, context)
        else:
            return self._get_general_information(message, context)

    def _get_waqaf_information(self, message, context):
        """Provide comprehensive waqaf information"""
        lang = context.get('preferred_language', 'en')
        
        if lang == 'ms':
            response = "🕌 **Apa itu Waqaf?**\n\n"
            response += "Waqaf adalah satu bentuk sedekah jariah dalam Islam di mana seseorang mewakafkan hartanya untuk tujuan kebajikan dan keagamaan. Harta wakaf ini akan kekal dan manfaatnya berterusan untuk masyarakat.\n\n"
            response += "🌟 **Kelebihan Waqaf:**\n"
            response += "• Pahala berterusan walaupun setelah meninggal dunia\n"
            response += "• Membantu masyarakat secara berterusan\n"
            response += "• Pelaburan akhirat yang terbaik\n"
            response += "• Membina kemudahan awam dan pendidikan\n\n"
        else:
            response = "🕌 **What is Waqaf (Islamic Endowment)?**\n\n"
            response += "Waqaf is a beautiful Islamic concept of dedicating property or assets for charitable and religious purposes. It's a form of continuous charity (sadaqah jariah) that benefits the community forever! ✨\n\n"
            response += "🌟 **Amazing Benefits of Waqaf:**\n"
            response += "• **Continuous Rewards**: Benefits continue even after you pass away\n"
            response += "• **Community Impact**: Helps society for generations\n"
            response += "• **Spiritual Investment**: Best investment for the hereafter\n"
            response += "• **Legacy Building**: Creates lasting positive change\n\n"
        
        # Get real waqaf data
        try:
            from waqaf.models import WaqafAsset
            assets = WaqafAsset.objects.filter(is_archived=False, slots_available__gt=0)[:3]
            
            if assets.exists():
                response += "🏗️ **Current Waqaf Opportunities:**\n\n"
                for asset in assets:
                    progress = ((asset.total_slots - asset.slots_available) / asset.total_slots * 100) if asset.total_slots > 0 else 0
                    response += f"🎯 **{asset.name}**\n"
                    response += f"   💰 Slot Price: RM {asset.slot_price:,.2f}\n"
                    response += f"   📊 Progress: {progress:.1f}% complete\n"
                    response += f"   🎫 Available Slots: {asset.slots_available}\n\n"
        except:
            pass
        
        response += "🤗 **Ready to make a lasting impact?** I can guide you through the contribution process!"
        
        return {
            'message': response,
            'suggestions': [
                '🎯 Show available assets',
                '💰 How to contribute?',
                '📊 Waqaf benefits',
                '🕌 Islamic principles',
                '📞 Contact waqaf admin'
            ],
            'type': 'waqaf_info',
            'emotion': 'educational_inspiring'
        }

    def _handle_problem_solving(self, message, user, entities, context, sentiment):
        """Advanced problem solving with empathy"""
        response = "🤗 **I'm here to help solve your problem!** Don't worry, we'll figure this out together! 💪\n\n"
        
        # Analyze the problem type
        if 'payment' in message and ('not working' in message or 'failed' in message or 'error' in message):
            response += "💳 **Payment Issues - Let's Fix This!**\n\n"
            response += "🔧 **Common Solutions:**\n"
            response += "1. **Check Internet Connection** - Ensure stable connection\n"
            response += "2. **Verify Payment Details** - Double-check card/bank info\n"
            response += "3. **Clear Browser Cache** - Refresh and try again\n"
            response += "4. **Try Different Browser** - Chrome, Firefox, or Safari\n"
            response += "5. **Check Bank Balance** - Ensure sufficient funds\n\n"
            response += "🏦 **Alternative Payment Methods:**\n"
            response += "• Try bank transfer instead of card\n"
            response += "• Visit school office for cash payment\n"
            response += "• Use different credit/debit card\n\n"
            
            suggestions = [
                '🏦 Bank transfer guide',
                '💰 Cash payment info',
                '🔄 Try different method',
                '📞 Contact support',
                '💡 More solutions'
            ]
        
        elif 'login' in message and ('cannot' in message or 'not working' in message):
            response += "🔐 **Login Issues - Let's Get You In!**\n\n"
            response += "🛠️ **Quick Fixes:**\n"
            response += "1. **Check Username/Email** - Make sure it's correct\n"
            response += "2. **Reset Password** - Use 'Forgot Password' link\n"
            response += "3. **Clear Browser Data** - Clear cookies and cache\n"
            response += "4. **Try Incognito Mode** - Private browsing window\n"
            response += "5. **Check Caps Lock** - Password is case-sensitive\n\n"
            response += "🔑 **Still Having Issues?**\n"
            response += "• Contact admin for account verification\n"
            response += "• Check if account is active\n"
            response += "• Try from different device\n\n"
            
            suggestions = [
                '🔑 Reset password',
                '📧 Contact admin',
                '💻 Try different browser',
                '📱 Mobile login',
                '❓ More help'
            ]
        
        else:
            # General problem solving
            response += "🔍 **Let's Identify the Issue:**\n\n"
            response += "To give you the best help, could you tell me more about:\n"
            response += "• What exactly isn't working?\n"
            response += "• What error message do you see?\n"
            response += "• When did this problem start?\n"
            response += "• What were you trying to do?\n\n"
            response += "💡 **Common Issues I Can Help With:**\n"
            response += "• Payment problems\n"
            response += "• Login difficulties\n"
            response += "• Navigation issues\n"
            response += "• Technical errors\n"
            response += "• Account problems\n\n"
            
            suggestions = [
                '💳 Payment problems',
                '🔐 Login issues',
                '🖥️ Technical errors',
                '📱 Mobile problems',
                '📞 Contact support'
            ]
        
        response += "😊 **Remember**: No problem is too small or too big for me to help with! I'm patient, and we'll solve this together! 🤝"
        
        return {
            'message': response,
            'suggestions': suggestions,
            'type': 'problem_solving',
            'emotion': 'empathetic_helpful'
        }

    def _identify_modules(self, message):
        """Enhanced module identification"""
        identified = []
        for module, keywords in self.smart_keywords.items():
            # Check primary keywords
            if any(keyword in message for keyword in keywords['primary']):
                identified.append(module)
            # Check action keywords in context
            elif module == 'fees' and any(action in message for action in keywords.get('actions', [])):
                if any(primary in message for primary in keywords['primary']):
                    identified.append(module)
        
        return identified

    def _get_specific_payment_guide(self, method, user, context):
        """Provide specific payment method guidance"""
        guides = {
            'bank transfer': {
                'title': '🏦 **Bank Transfer Guide**',
                'content': "**Step-by-Step Bank Transfer:**\n\n1. **Login to Your Online Banking** 💻\n2. **Select 'Transfer' or 'Pay Bills'** 📋\n3. **Add School as Payee** (if first time) 🏫\n4. **Enter Payment Details:**\n   • Amount: [Your fee amount]\n   • Reference: Your Student ID\n   • Description: School fees\n5. **Confirm and Submit** ✅\n6. **Save Receipt** 🧾\n7. **Upload proof in system** 📤\n\n**Bank Details:**\n• Bank: [School Bank]\n• Account: [School Account Number]\n• Name: [School Name]\n\n⏰ **Processing Time**: 1-3 business days",
                'suggestions': ['💰 Cash payment', '🌐 Online payment', '📞 Bank details', '❓ Payment problems']
            },
            'cash': {
                'title': '💰 **Cash Payment Guide**',
                'content': "**Cash Payment Process:**\n\n🏫 **Visit School Office:**\n• **Location**: Administration Building\n• **Hours**: 8:00 AM - 5:00 PM (Mon-Fri)\n• **Counter**: Fees & Payment Section\n\n📋 **What to Bring:**\n• Student ID or NRIC\n• Exact amount (or we'll provide change)\n• Payment reference (if any)\n\n✅ **Process:**\n1. Queue at payment counter\n2. Provide student details\n3. Make cash payment\n4. Receive official receipt\n5. Keep receipt safely\n\n⚡ **Instant Processing** - Payment recorded immediately!",
                'suggestions': ['🏫 Office location', '⏰ Office hours', '🏦 Bank transfer', '📞 Contact office']
            },
            'online': {
                'title': '🌐 **Online Payment Guide**',
                'content': "**Online Payment Steps:**\n\n💻 **Access Payment Portal:**\n1. Login to your account\n2. Go to 'School Fees' section\n3. Select outstanding fees\n4. Click 'Pay Online'\n\n💳 **Payment Options:**\n• Credit Card (Visa, MasterCard)\n• Debit Card\n• Online Banking (FPX)\n• E-Wallet (selected options)\n\n🔒 **Security Features:**\n• SSL encrypted transactions\n• 3D Secure verification\n• Real-time fraud detection\n• Instant confirmation\n\n⚡ **Instant Receipt** - Download immediately after payment!",
                'suggestions': ['💳 Card payment tips', '🏦 Online banking', '📱 E-wallet options', '🔒 Security info']
            }
        }
        
        guide = guides.get(method, guides['online'])  # Default to online
        
        return {
            'message': f"{guide['title']}\n\n{guide['content']}\n\n🤗 **Need more help?** I'm here to guide you through every step!",
            'suggestions': guide['suggestions'],
            'type': 'payment_guide',
            'emotion': 'helpful_detailed'
        }

    def _get_donation_information(self, message, user, context):
        """Provide comprehensive donation information"""
        from myapp.models import DonationEvent
        
        if 'current' in message or 'active' in message or 'events' in message:
            active_events = DonationEvent.objects.filter(is_active=True).order_by('-created_at')
            
            if active_events.exists():
                response = "💰 **Current Donation Events - Make a Difference Today!** 🌟\n\n"
                
                for i, event in enumerate(active_events[:4], 1):
                    progress = (event.current_amount / event.target_amount * 100) if event.target_amount > 0 else 0
                    
                    # Create visual progress bar
                    filled_blocks = int(progress // 10)
                    progress_bar = "🟩" * filled_blocks + "⬜" * (10 - filled_blocks)
                    
                    response += f"**{i}. {event.title}** 🎯\n"
                    response += f"   💰 **Raised**: RM {event.current_amount:,.2f} / RM {event.target_amount:,.2f}\n"
                    response += f"   📊 **Progress**: {progress_bar} {progress:.1f}%\n"
                    
                    if event.end_date:
                        days_left = (event.end_date - timezone.now().date()).days
                        if days_left > 0:
                            response += f"   ⏰ **{days_left} days left** - Every donation counts!\n"
                        else:
                            response += f"   🏁 **Campaign ended** - Thank you to all supporters!\n"
                    
                    response += f"   📝 **Description**: {event.description[:100]}...\n\n"
                
                response += "🎯 **Every donation makes a real difference!** Which cause speaks to your heart? 💖"
                
                return {
                    'message': response,
                    'suggestions': [
                        '💝 How to donate?',
                        '💳 Payment methods',
                        '📊 Event details',
                        '🏆 Impact stories',
                        '📞 Contact organizer'
                    ],
                    'type': 'donation_events',
                    'emotion': 'inspiring'
                }
            else:
                return {
                    'message': "📭 **No Active Events Right Now**\n\nDon't worry! New donation events are regularly organized. 🌟\n\n📅 **What's Coming:**\n• Seasonal fundraising campaigns\n• Emergency relief funds\n• Educational support programs\n• Community development projects\n\n🔔 **Stay Updated:**\n• Check back regularly\n• Follow our announcements\n• Contact admin for upcoming events\n\n💡 **In the meantime**, you can still contribute to our ongoing waqaf programs! 🕌",
                    'suggestions': [
                        '🕌 Waqaf opportunities',
                        '📧 Get notifications',
                        '📞 Contact admin',
                        '🏠 Back to homepage'
                    ],
                    'type': 'no_events',
                    'emotion': 'encouraging'
                }
        
        # General donation information
        return {
            'message': "💰 **Donation Information**\n\nI can help you with everything about donations! 🌟\n\n🎯 **What I Can Show You:**\n• Current active donation events\n• How to make donations step-by-step\n• Payment methods and security\n• Your donation history\n• Impact of your contributions\n• Tax benefits and receipts\n\nWhat specific information would you like? 😊",
            'suggestions': [
                '📊 Current events',
                '💝 How to donate',
                '📈 My donations',
                '🧾 Tax benefits',
                '🏆 Impact stories'
            ],
            'type': 'donation_info',
            'emotion': 'informative'
        }

    def _get_general_information(self, message, context):
        """Provide general system information"""
        return {
            'message': "🌟 **Welcome to Our Comprehensive System!**\n\nI'm your all-in-one AI assistant, and I absolutely love helping people like you! 💖\n\n🏫 **What Makes Our System Special:**\n\n**📊 School Fee Management**\n• Real-time fee tracking\n• Multiple payment methods\n• Instant receipts\n• Fee waiver applications\n\n**💰 Donation Platform**\n• Transparent fundraising\n• Progress tracking\n• Impact reporting\n• Secure payments\n\n**🕌 Waqaf Management**\n• Islamic endowment system\n• Asset tracking\n• Community benefits\n• Shariah compliance\n\n**👨‍🎓 Student Services**\n• Easy registration\n• Profile management\n• Academic support\n• Communication tools\n\n🚀 **Everything is designed to make your life easier and more meaningful!**\n\nWhat would you like to explore first? I'm excited to show you around! 🎉",
            'suggestions': [
                '🏫 School fees',
                '💰 Donations',
                '🕌 Waqaf',
                '👨‍🎓 Student services',
                '📞 Contact support'
            ],
            'type': 'system_overview',
            'emotion': 'enthusiastic'
        }

class ConversationMemory:
    """Advanced conversation memory system"""
    
    def __init__(self):
        self.sessions = {}
    
    def get_or_create_session(self, session_id):
        """Get or create conversation session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'messages': [],
                'context': {},
                'user_preferences': {},
                'mood_history': [],
                'topics_discussed': [],
                'created_at': datetime.now()
            }
        return self.sessions[session_id]
    
    def add_message(self, session_id, message, response, user=None):
        """Add message to conversation history"""
        session = self.get_or_create_session(session_id)
        session['messages'].append({
            'user_message': message,
            'bot_response': response,
            'timestamp': datetime.now(),
            'user': user.username if user else None
        })
        
        # Keep only last 50 messages to manage memory
        if len(session['messages']) > 50:
            session['messages'] = session['messages'][-50:]

# Global conversation memory instance
conversation_memory = ConversationMemory()
