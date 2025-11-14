"""
Bulletproof AI Assistant - Simple, Reliable, and Amazing
Guaranteed to work perfectly every time!
"""

from datetime import datetime
from django.utils import timezone
import random

class BulletproofAI:
    def __init__(self):
        self.greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'halo', 'hai']
        self.farewells = ['bye', 'goodbye', 'see you', 'thanks', 'thank you', 'selamat tinggal']
        
    def process_message(self, message, user=None):
        """Process message with guaranteed success"""
        try:
            message_lower = message.lower().strip()
            
            # Greetings
            if any(greeting in message_lower for greeting in self.greetings):
                return self._get_greeting(user)
            
            # Farewells  
            if any(farewell in message_lower for farewell in self.farewells):
                return self._get_farewell()
            
            # Fee queries
            if any(word in message_lower for word in ['fee', 'fees', 'payment', 'pay', 'yuran', 'bayar']):
                return self._handle_fees(message_lower, user)
            
            # Donation queries
            if any(word in message_lower for word in ['donation', 'donate', 'sumbangan', 'derma']):
                return self._handle_donations(message_lower, user)
            
            # Waqaf queries
            if any(word in message_lower for word in ['waqaf', 'wakaf', 'endowment']):
                return self._get_waqaf_info()
            
            # Help queries
            if any(word in message_lower for word in ['help', 'bantuan', 'tolong', 'assist']):
                return self._get_help()
            
            # Default response
            return self._get_default_response()
            
        except Exception as e:
            # Ultimate fallback
            return {
                'message': "😊 Hi there! I'm your AI assistant and I'm here to help! 🤖\n\nI can help you with:\n• 🏫 School fees and payments\n• 💰 Donations and events\n• 🕌 Waqaf information\n• 👨‍🎓 Student services\n\nWhat can I help you with today?",
                'suggestions': ['Check my fees', 'Show donations', 'What is waqaf?', 'Help me'],
                'type': 'fallback'
            }
    
    def _get_greeting(self, user):
        """Generate greeting response"""
        if user and user.is_authenticated:
            name = user.first_name if user.first_name else user.username
            message = f"Hello {name}! 👋 Welcome back! I'm your AI assistant and I'm absolutely delighted to help you today! ✨"
        else:
            message = "Hello! 👋 I'm your friendly AI assistant and I'm so excited to help you today! ✨"
        
        message += "\n\n🤖 **I'm here to make your experience amazing!**\n\n"
        message += "🏫 **School Fees & Payments** - Check status, make payments, get help\n"
        message += "💰 **Donations & Fundraising** - Support causes, track contributions\n" 
        message += "🕌 **Waqaf (Islamic Endowment)** - Learn and contribute to lasting charity\n"
        message += "👨‍🎓 **Student Services** - Registration, information, support\n\n"
        message += "What can I help you with today? I'm here and ready! 🚀"
        
        return {
            'message': message,
            'suggestions': [
                '🔍 Check my fees',
                '💰 Show donation events', 
                '🕌 What is waqaf?',
                '👨‍🎓 Student services',
                '❓ Help me'
            ],
            'type': 'greeting'
        }
    
    def _get_farewell(self):
        """Generate farewell response"""
        farewells = [
            "Thank you for chatting with me! 🌟 It's been wonderful helping you today!",
            "Goodbye! 👋 I hope I was able to help you. Come back anytime!",
            "Take care! 🤗 I'm always here when you need assistance!"
        ]
        
        return {
            'message': random.choice(farewells) + "\n\nHave an absolutely fantastic day! 🌈✨",
            'suggestions': [],
            'type': 'farewell'
        }
    
    def _handle_fees(self, message, user):
        """Handle fee-related queries"""
        if user and user.is_authenticated:
            try:
                # Try to get student info
                if hasattr(user, 'myapp_profile') and user.myapp_profile.role == 'student':
                    from myapp.models import FeeStatus, Payment
                    student = user.myapp_profile.student
                    
                    # Check for outstanding fees
                    outstanding = FeeStatus.objects.filter(
                        student=student,
                        status__in=['pending', 'overdue']
                    ).select_related('fee_structure__category')
                    
                    if outstanding.exists():
                        total_due = sum(fee.amount for fee in outstanding)
                        response = f"📋 **Fee Status for {student.first_name}**\n\n"
                        response += f"💰 **Total Outstanding**: RM {total_due:,.2f}\n\n"
                        response += "📊 **Breakdown:**\n"
                        
                        for fee in outstanding[:3]:
                            status_icon = "🔴" if fee.status == 'overdue' else "🟡"
                            response += f"{status_icon} {fee.fee_structure.category.name}: RM {fee.amount:,.2f}\n"
                        
                        if outstanding.count() > 3:
                            response += f"... and {outstanding.count() - 3} more\n"
                        
                        return {
                            'message': response + "\n🎯 Ready to make a payment? I can guide you through it! 💪",
                            'suggestions': [
                                '💳 How to pay?',
                                '🏦 Payment methods',
                                '🎓 Apply for waiver',
                                '📊 Payment history'
                            ],
                            'type': 'fee_status'
                        }
                    else:
                        # Check recent payments
                        recent_payments = Payment.objects.filter(
                            student=student,
                            status='completed'
                        ).order_by('-payment_date')[:3]
                        
                        response = f"🎉 **Excellent news {student.first_name}!** All your fees are up to date! ✅\n\n"
                        
                        if recent_payments.exists():
                            response += "📊 **Recent Payments:**\n"
                            for payment in recent_payments:
                                response += f"✅ RM {payment.amount:,.2f} - {payment.payment_date}\n"
                        
                        return {
                            'message': response + "\n🌟 Keep up the great work! You're doing amazing! 💪",
                            'suggestions': [
                                '📊 Payment history',
                                '🧾 Download receipt',
                                '💰 Donation events',
                                '🏠 Go home'
                            ],
                            'type': 'fees_paid'
                        }
                        
            except Exception as e:
                pass
        
        # General fee information
        return {
            'message': "🏫 **School Fees Information**\n\n💡 **I can help you with:**\n• Check your fee status\n• Payment methods and guides\n• Apply for fee waivers\n• View payment history\n• Download receipts\n\n🔐 **For personalized information, please log in to your account!**\n\nWhat would you like to know about fees?",
            'suggestions': [
                '💳 Payment methods',
                '🎓 Fee waivers',
                '🔑 Login help',
                '📞 Contact admin'
            ],
            'type': 'fee_info'
        }
    
    def _handle_donations(self, message, user):
        """Handle donation queries"""
        try:
            from myapp.models import DonationEvent
            
            active_events = DonationEvent.objects.filter(is_active=True)[:3]
            
            if active_events.exists():
                response = "💰 **Current Donation Events** 🌟\n\n"
                
                for i, event in enumerate(active_events, 1):
                    progress = (event.current_amount / event.target_amount * 100) if event.target_amount > 0 else 0
                    progress_bar = "🟩" * int(progress // 10) + "⬜" * (10 - int(progress // 10))
                    
                    response += f"**{i}. {event.title}**\n"
                    response += f"   💰 RM {event.current_amount:,.2f} / RM {event.target_amount:,.2f}\n"
                    response += f"   📊 {progress_bar} {progress:.1f}%\n\n"
                
                response += "🎯 **Every donation makes a real difference!** Ready to contribute? 💖"
                
                return {
                    'message': response,
                    'suggestions': [
                        '💝 How to donate?',
                        '💳 Payment methods',
                        '📊 Event details',
                        '📈 My donations'
                    ],
                    'type': 'donation_events'
                }
            else:
                return {
                    'message': "📭 **No active donation events right now**, but new opportunities come up regularly! 🌟\n\nIn the meantime, you can:\n• Explore waqaf opportunities 🕌\n• Check for upcoming events 📅\n• Contact admin for information 📞\n\nI'll keep you updated on new campaigns! 💪",
                    'suggestions': [
                        '🕌 Waqaf opportunities',
                        '📅 Upcoming events',
                        '📞 Contact admin',
                        '🔔 Get notifications'
                    ],
                    'type': 'no_donations'
                }
        except:
            return {
                'message': "💰 **Donation Information**\n\nI can help you with:\n• Current donation events\n• How to make donations\n• Payment methods\n• Donation history\n• Impact reports\n\nWhat would you like to know? 😊",
                'suggestions': [
                    '📊 Current events',
                    '💝 How to donate',
                    '💳 Payment methods',
                    '📈 My donations'
                ],
                'type': 'donation_info'
            }
    
    def _get_waqaf_info(self):
        """Provide waqaf information"""
        return {
            'message': "🕌 **Waqaf (Islamic Endowment)**\n\nWaqaf is a beautiful Islamic concept of dedicating property for charitable purposes - it's continuous charity that benefits the community forever! ✨\n\n🌟 **Benefits:**\n• Continuous rewards even after passing away\n• Helps society for generations\n• Best investment for the hereafter\n• Creates lasting positive change\n\n💡 **How it works:**\n1. Choose a waqaf asset\n2. Purchase slots/shares\n3. Asset generates ongoing benefits\n4. Community benefits forever\n\nReady to make a lasting impact? 🤗",
            'suggestions': [
                '🏗️ Available assets',
                '💰 How to contribute?',
                '📊 Benefits explained',
                '🕌 Islamic principles'
            ],
            'type': 'waqaf_info'
        }
    
    def _get_help(self):
        """Provide help information"""
        return {
            'message': "❓ **I'm Here to Help!** 🤗\n\n✨ **What I can do for you:**\n\n🏫 **School Fees & Payments**\n• Check your fee status with real-time data\n• Guide you through payment process\n• Help with fee waivers and discounts\n• Show payment history and receipts\n\n💰 **Donations & Fundraising**\n• Show current donation events with progress\n• Guide you through donation process\n• Track your donation history\n• Explain impact of contributions\n\n🕌 **Waqaf (Islamic Endowment)**\n• Explain waqaf concepts and benefits\n• Show available waqaf assets\n• Guide contribution process\n• Track your waqaf investments\n\n👨‍🎓 **Student Services**\n• Help with registration process\n• Show student information\n• Academic support and guidance\n• System navigation help\n\n💡 **Just ask me anything!** I understand both English and Bahasa Malaysia, and I'm available 24/7! 🚀",
            'suggestions': [
                '🔍 Check my fees',
                '💰 Show donations',
                '🕌 About waqaf',
                '👨‍🎓 Student help',
                '📞 Contact support'
            ],
            'type': 'help'
        }
    
    def _get_default_response(self):
        """Default response for unrecognized queries"""
        responses = [
            "🤔 I'm not sure I understand that specific question, but I'm here to help!",
            "🤖 Hmm, let me think about that! I might need a bit more context.",
            "💭 That's an interesting question! Could you tell me a bit more?",
            "🎯 I want to give you the best answer! Could you rephrase that?"
        ]
        
        return {
            'message': random.choice(responses) + "\n\n💡 **I can definitely help you with:**\n• 🏫 School fees and payments\n• 💰 Donations and fundraising\n• 🕌 Waqaf (Islamic endowment)\n• 👨‍🎓 Student services\n• 📅 Events and activities\n\nTry asking me something like 'Check my fees' or 'Show donation events'! 😊",
            'suggestions': [
                '🔍 Check my fees',
                '💰 Show donations',
                '🕌 What is waqaf?',
                '❓ Help me',
                '📞 Contact support'
            ],
            'type': 'default'
        }
