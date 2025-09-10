"""Psychological enhancement engine for the Python AI Tutor.

Implements evidence-based psychological techniques including Self-Determination Theory,
growth mindset messaging, and habit formation psychology. Provides probabilistic 
encouragement, context-aware motivation, and celebration systems to enhance learning
engagement and persistence without disrupting the core technical experience.
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class PsychologicalEngine:
    """Handles psychological aspects of learning: encouragement, growth mindset, motivation."""
    
    def __init__(self):
        """Initialize psychological engine with message pools and settings."""
        self._encouragement_messages = [
            "Great debugging practice! Every error teaches you something new.",
            "You're building real problem-solving skills right now!",
            "This challenge is helping you think like a programmer.",
            "Mistakes are data - you're learning from valuable feedback.",
            "You're developing persistence, a key programming skill!",
            "Each attempt strengthens your coding intuition.",
            "Professional programmers debug constantly - you're on the right track!",
            "You're not failing, you're finding ways that don't work yet.",
            "This struggle means your brain is forming new neural pathways!",
            "Every programmer faces these challenges - you're in good company.",
            "Breaking things is how we learn to fix them.",
            "Your persistence will pay off - keep experimenting!",
            "Code that doesn't work the first time is completely normal.",
            "You're practicing the most important programming skill: resilience.",
            "This debugging session is making you a stronger programmer."
        ]
        
        self._celebration_messages = [
            "Excellent work! You just solved a real programming challenge.",
            "Well done! Your problem-solving skills are improving.",
            "Great job! You're thinking like a programmer now.",
            "Fantastic! You persevered and found the solution.",
            "Awesome! Each success builds your programming confidence.",
            "Brilliant! You're mastering these concepts step by step.",
            "Outstanding! Your hard work is paying off.",
            "Perfect! You've earned this victory through effort.",
            "Wonderful! You're developing real coding expertise.",
            "Impressive! You solved that like a pro."
        ]
        
        self._milestone_celebrations = {
            'first_success': "🎉 Your very first successful challenge! This is the beginning of your programming journey!",
            'streak_achievement': "🔥 You're on fire! Consistent practice builds expertise.",
            'difficult_challenge': "🏆 You tackled a tough challenge and won! Your skills are advancing.",
            'error_overcome': "💪 You turned that error into success - true programmer resilience!"
        }
        
        # Track recent messages to avoid repetition
        self._recent_messages = []
        self._max_recent_messages = 5
    
    def should_show_encouragement(self, context: Optional[Dict] = None) -> bool:
        """
        Determine if encouragement should be shown based on probability and context.
        
        Args:
            context: Optional context including attempt_count, user_struggling, etc.
        
        Returns:
            True if encouragement should be shown, False otherwise
        """
        base_probability = 0.5  # 50% base chance
        
        if not context:
            return random.random() < base_probability
        
        # Adjust probability based on context
        probability = base_probability
        
        # Higher probability when user is struggling
        attempt_count = context.get('attempt_count', 1)
        if attempt_count >= 3:
            probability = 0.8  # 80% chance after 3+ failed attempts
        elif attempt_count == 1:
            probability = 0.3  # 30% chance on first attempt (let them try independently)
        
        # Lower probability if user is on a success streak
        if context.get('recent_successes', 0) >= 3:
            probability = 0.3  # They're already motivated
        
        # Higher probability if user hasn't been active recently
        if context.get('days_since_last_activity', 0) > 3:
            probability = 0.7  # Welcome back with encouragement
        
        return random.random() < probability
    
    def generate_encouragement_message(self, context: Optional[Dict] = None) -> str:
        """
        Generate a contextual encouragement message with variety.
        
        Args:
            context: Optional context for message customization
        
        Returns:
            Appropriate encouragement message
        """
        # Select message that hasn't been used recently
        available_messages = [
            msg for msg in self._encouragement_messages 
            if msg not in self._recent_messages
        ]
        
        # If all messages were used recently, reset the pool
        if not available_messages:
            available_messages = self._encouragement_messages
            self._recent_messages.clear()
        
        # Select random message
        message = random.choice(available_messages)
        
        # Track message to avoid immediate repetition
        self._recent_messages.append(message)
        if len(self._recent_messages) > self._max_recent_messages:
            self._recent_messages.pop(0)
        
        return message
    
    def get_celebration_message(self, milestone_type: Optional[str] = None) -> str:
        """
        Generate celebration message for successful completion.
        
        Args:
            milestone_type: Type of milestone (first_success, streak_achievement, etc.)
        
        Returns:
            Appropriate celebration message
        """
        if milestone_type and milestone_type in self._milestone_celebrations:
            return self._milestone_celebrations[milestone_type]
        
        return random.choice(self._celebration_messages)
    
    def analyze_struggle_context(self, attempt_count: int, success_rate: float, 
                               recent_attempts: List[bool]) -> Dict:
        """
        Analyze user's struggle pattern to provide smart encouragement timing.
        
        Args:
            attempt_count: Number of attempts on current challenge
            success_rate: Overall success rate (0.0 to 1.0)
            recent_attempts: List of recent attempt outcomes (True/False)
        
        Returns:
            Context dictionary for encouragement decisions
        """
        context = {
            'attempt_count': attempt_count,
            'success_rate': success_rate,
            'is_struggling': attempt_count >= 3,
            'recent_failures': sum(1 for result in recent_attempts[-5:] if not result),
            'recent_successes': sum(1 for result in recent_attempts[-5:] if result)
        }
        
        # Detect different struggle patterns
        if attempt_count >= 5:
            context['struggle_level'] = 'high'
        elif attempt_count >= 3:
            context['struggle_level'] = 'moderate'
        else:
            context['struggle_level'] = 'low'
        
        # Check for learning plateau (multiple recent failures)
        if context['recent_failures'] >= 4:
            context['needs_encouragement'] = True
            context['suggestion'] = 'Consider reviewing the explanation or taking a short break.'
        
        return context
    
    def should_suggest_break(self, session_duration_minutes: int, 
                           consecutive_failures: int) -> Tuple[bool, Optional[str]]:
        """
        Suggest break based on cognitive load and frustration indicators.
        
        Args:
            session_duration_minutes: How long the current session has lasted
            consecutive_failures: Number of consecutive failed attempts
        
        Returns:
            Tuple of (should_suggest_break, suggestion_message)
        """
        suggest_break = False
        message = None
        
        # Suggest break after long session with struggles
        if session_duration_minutes > 45 and consecutive_failures >= 3:
            suggest_break = True
            message = "You've been working hard! Taking a short break often helps with fresh perspective."
        
        # Suggest break after many consecutive failures
        elif consecutive_failures >= 6:
            suggest_break = True
            message = "Sometimes stepping away for a few minutes helps reset your thinking. You've got this!"
        
        return suggest_break, message
    
    def get_adaptive_hint_timing(self, attempt_count: int, user_confidence: float) -> int:
        """
        Determine optimal timing for hint disclosure based on user state.
        
        Args:
            attempt_count: Number of attempts on current challenge
            user_confidence: Estimated confidence level (0.0 to 1.0)
        
        Returns:
            Number of attempts to wait before suggesting hints
        """
        # High confidence users - let them struggle longer for deeper learning
        if user_confidence > 0.8:
            return max(4, attempt_count)
        
        # Low confidence users - offer help sooner to prevent discouragement
        elif user_confidence < 0.3:
            return max(2, attempt_count)
        
        # Medium confidence - standard timing
        else:
            return max(3, attempt_count)
    
    def generate_reframe_message(self, error_type: str, context: Optional[Dict] = None) -> str:
        """
        Generate growth mindset reframing of errors and failures.
        
        Args:
            error_type: Type of error (syntax, logic, runtime, etc.)
            context: Optional context for customization
        
        Returns:
            Reframed message that presents error as learning opportunity
        """
        reframe_templates = {
            'syntax': [
                "Syntax errors are Python's way of teaching you precise communication!",
                "Every syntax error makes you more fluent in Python's language.",
                "Think of syntax errors as friendly corrections - Python wants to understand you better."
            ],
            'logic': [
                "Logic errors reveal how you think - debugging them sharpens your reasoning!",
                "Finding logic errors is like solving puzzles - you're building problem-solving muscles.",
                "Logic bugs show you're tackling complex problems - that's real programming!"
            ],
            'runtime': [
                "Runtime errors happen to every programmer - you're learning to handle the unexpected!",
                "Runtime errors teach you defensive programming - a valuable skill!",
                "These errors show your code is running - now you're debugging like a pro!"
            ],
            'generic': [
                "Every error is data that makes your next attempt smarter!",
                "Debugging is a superpower - you're developing it right now!",
                "Errors are not failures, they're feedback on the path to success!"
            ]
        }
        
        messages = reframe_templates.get(error_type, reframe_templates['generic'])
        return random.choice(messages)