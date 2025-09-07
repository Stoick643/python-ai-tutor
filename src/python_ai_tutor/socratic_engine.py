"""Socratic questioning engine for interactive learning.

Intelligent questioning system that generates context-aware questions, analyzes student 
responses, and provides adaptive hints using pedagogical principles.
Implements the Socratic method to guide students toward understanding through inquiry.
"""

import random
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .models import ContentLevel, ContentType


class QuestionType(str, Enum):
    """Types of Socratic questions."""
    
    PREDICTION = "prediction"      # "What will this code output?"
    CONCEPT = "concept"           # "What is a variable used for?"
    APPLICATION = "application"   # "How would you store someone's email?"
    DEBUGGING = "debugging"       # "What's wrong with this code?"
    REFLECTION = "reflection"     # "Why do you think this works?"


@dataclass
class Question:
    """A single Socratic question with context."""
    
    question_type: QuestionType
    text: str
    context: str  # Related code or concept
    hints: List[str] = None
    expected_keywords: List[str] = None
    
    def __post_init__(self):
        if self.hints is None:
            self.hints = []
        if self.expected_keywords is None:
            self.expected_keywords = []


@dataclass
class UserResponse:
    """User's response to a question with analysis."""
    
    text: str
    confidence_score: float = 0.0  # 0-1, how confident/detailed the response is
    contains_keywords: List[str] = None
    sentiment: str = "neutral"  # positive, neutral, confused, negative
    
    def __post_init__(self):
        if self.contains_keywords is None:
            self.contains_keywords = []


class SocraticEngine:
    """Engine for generating and analyzing Socratic questions."""
    
    def __init__(self):
        """Initialize the Socratic questioning engine."""
        self.question_templates = self._initialize_question_templates()
        self.concept_keywords = self._initialize_concept_keywords()
    
    def _initialize_question_templates(self) -> Dict[ContentType, List[Dict]]:
        """Initialize question templates for each content level."""
        return {
            ContentType.CONCEPT: [
                {
                    "type": QuestionType.CONCEPT,
                    "templates": [
                        "Before we dive in, what do you think {concept} means in programming?",
                        "Can you think of a real-world analogy for {concept}?",
                        "Why might we need {concept} when writing programs?",
                        "What's your understanding of {concept} before we learn more?"
                    ]
                },
                {
                    "type": QuestionType.REFLECTION,
                    "templates": [
                        "How do you think {concept} might be useful in everyday programming?",
                        "What questions do you have about {concept} so far?"
                    ]
                }
            ],
            ContentType.SIMPLE_EXAMPLE: [
                {
                    "type": QuestionType.PREDICTION,
                    "templates": [
                        "What do you think this code will output?",
                        "Before we run this, what do you expect to see?",
                        "Can you predict what happens when we execute this code?",
                        "What result would you expect from this code?"
                    ]
                },
                {
                    "type": QuestionType.CONCEPT,
                    "templates": [
                        "What's happening in this line: {code_line}?",
                        "Can you explain what {variable} represents here?",
                        "Why do you think we used {technique} in this example?"
                    ]
                }
            ],
            ContentType.MEDIUM_EXAMPLE: [
                {
                    "type": QuestionType.PREDICTION,
                    "templates": [
                        "This is more complex - what do you think the output will be?",
                        "Can you trace through this code and predict each line's output?",
                        "What do you expect the final result to be?"
                    ]
                },
                {
                    "type": QuestionType.DEBUGGING,
                    "templates": [
                        "If you saw an error here, what might be the first thing to check?",
                        "What could go wrong with this type of code?",
                        "How would you modify this code to {modification}?"
                    ]
                }
            ],
            ContentType.COMPLEX_EXAMPLE: [
                {
                    "type": QuestionType.REFLECTION,
                    "templates": [
                        "This example uses several concepts together - which parts do you recognize?",
                        "What makes this example more complex than the previous ones?",
                        "Which technique here seems most useful for real programming?"
                    ]
                },
                {
                    "type": QuestionType.APPLICATION,
                    "templates": [
                        "Where might you use this pattern in a real program?",
                        "Can you think of a scenario where this approach would be helpful?",
                        "How could you adapt this technique for {application}?"
                    ]
                }
            ]
        }
    
    def _initialize_concept_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for concept understanding."""
        return {
            "variables": [
                "store", "hold", "container", "box", "label", "name", "value",
                "assign", "memory", "data", "information", "reference"
            ],
            "assignment": [
                "equals", "set", "give", "assign", "store", "put", "save"
            ],
            "output": [
                "print", "display", "show", "output", "result", "screen"
            ],
            "string": [
                "text", "words", "characters", "letters", "quote", "message"
            ],
            "number": [
                "integer", "digit", "math", "calculate", "numeric", "value"
            ]
        }
    
    def generate_question(self, content_level: ContentLevel, context: str = "") -> Question:
        """Generate a Socratic question for a content level.
        
        Args:
            content_level: The content level being taught
            context: Additional context (like specific code line)
            
        Returns:
            Generated Question object
        """
        templates = self.question_templates.get(content_level.type, [])
        if not templates:
            # Fallback generic question
            return Question(
                question_type=QuestionType.REFLECTION,
                text="What do you think about this concept?",
                context=content_level.content
            )
        
        # Choose random template category
        template_category = random.choice(templates)
        question_type = template_category["type"]
        template = random.choice(template_category["templates"])
        
        # Fill in template with context
        question_text = self._format_question_template(
            template, content_level, context
        )
        
        # Generate hints and expected keywords
        hints = self._generate_hints(question_type, content_level)
        keywords = self._get_expected_keywords(content_level)
        
        return Question(
            question_type=question_type,
            text=question_text,
            context=context or content_level.content,
            hints=hints,
            expected_keywords=keywords
        )
    
    def _format_question_template(
        self, template: str, content_level: ContentLevel, context: str
    ) -> str:
        """Format a question template with appropriate context."""
        # Extract concept name from content type
        concept_map = {
            ContentType.CONCEPT: "variables",
            ContentType.SIMPLE_EXAMPLE: "variable assignment",
            ContentType.MEDIUM_EXAMPLE: "variable operations",
            ContentType.COMPLEX_EXAMPLE: "advanced variable techniques"
        }
        
        concept = concept_map.get(content_level.type, "this concept")
        
        # Try to extract variable names or code lines from content
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*=', content_level.code or "")
        variable = variables[0].replace("=", "").strip() if variables else "variable"
        
        code_lines = (content_level.code or "").split('\n')
        code_line = code_lines[0] if code_lines else "this line"
        
        # Format template
        return template.format(
            concept=concept,
            variable=variable,
            code_line=code_line,
            technique="assignment",
            modification="handle different data types",
            application="a user profile system"
        )
    
    def _generate_hints(self, question_type: QuestionType, content_level: ContentLevel) -> List[str]:
        """Generate helpful hints for a question."""
        hint_map = {
            QuestionType.PREDICTION: [
                "Look at each line step by step",
                "Think about what values are being stored",
                "Consider how the print statement will display the data"
            ],
            QuestionType.CONCEPT: [
                "Think about what this accomplishes",
                "Consider why a programmer would need this",
                "What problem does this solve?"
            ],
            QuestionType.APPLICATION: [
                "Think about apps or websites you use",
                "Consider what data needs to be stored",
                "What information changes during program execution?"
            ],
            QuestionType.DEBUGGING: [
                "Check for typos in variable names",
                "Make sure quotes match",
                "Look at the order of operations"
            ],
            QuestionType.REFLECTION: [
                "Think about what you've learned so far",
                "Consider how this builds on previous concepts"
            ]
        }
        
        return hint_map.get(question_type, ["Take your time to think through this"])
    
    def _get_expected_keywords(self, content_level: ContentLevel) -> List[str]:
        """Get expected keywords for evaluating responses."""
        # Combine keywords based on content type
        keywords = []
        keywords.extend(self.concept_keywords.get("variables", []))
        
        if content_level.code:
            if "print" in content_level.code:
                keywords.extend(self.concept_keywords.get("output", []))
            if '"' in content_level.code or "'" in content_level.code:
                keywords.extend(self.concept_keywords.get("string", []))
            if any(char.isdigit() for char in content_level.code):
                keywords.extend(self.concept_keywords.get("number", []))
        
        return list(set(keywords))  # Remove duplicates
    
    def analyze_response(self, response_text: str, question: Question) -> UserResponse:
        """Analyze user's response to a Socratic question.
        
        Args:
            response_text: User's text response
            question: The question that was asked
            
        Returns:
            UserResponse with analysis
        """
        response_lower = response_text.lower()
        
        # Calculate confidence score based on length and detail
        confidence = min(len(response_text.split()) / 12.0, 1.0)  # More words = more confidence
        
        # Check for expected keywords
        found_keywords = []
        for keyword in question.expected_keywords:
            if keyword.lower() in response_lower:
                found_keywords.append(keyword)
                confidence += 0.1  # Boost confidence for relevant keywords
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(response_lower)
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return UserResponse(
            text=response_text,
            confidence_score=confidence,
            contains_keywords=found_keywords,
            sentiment=sentiment
        )
    
    def _analyze_sentiment(self, response_lower: str) -> str:
        """Simple sentiment analysis of user response."""
        # Check confused words first (more specific)
        confused_words = ["confused", "don't understand", "unclear", "difficult", "hard",
                         "don't know", "not sure", "maybe"]
        negative_words = ["boring", "stupid", "don't care", "hate", "annoying"]
        positive_words = ["good", "great", "cool", "awesome", "understand", "makes sense", 
                         "clear", "easy", "got it", "yes", "right"]
        
        if any(word in response_lower for word in confused_words):
            return "confused"
        elif any(word in response_lower for word in negative_words):
            return "negative"
        elif any(word in response_lower for word in positive_words):
            return "positive"
        else:
            return "neutral"
    
    def generate_feedback(self, response: UserResponse, question: Question) -> str:
        """Generate encouraging feedback based on user response.
        
        Args:
            response: Analyzed user response
            question: Original question
            
        Returns:
            Feedback message for the user
        """
        if response.sentiment == "confused":
            return f"No worries! {random.choice(question.hints)} Let's continue and see if it becomes clearer."
        
        elif response.confidence_score > 0.7 and response.contains_keywords:
            encouragements = [
                "Excellent thinking! You're really getting this.",
                "Great insight! You mentioned some key concepts.",
                "Perfect! You're connecting the dots well.",
                "Outstanding! That shows good understanding."
            ]
            return random.choice(encouragements)
        
        elif response.confidence_score > 0.3:
            return "Good start! Let's see this in action to build on your understanding."
        
        elif response.text.strip() == "" or len(response.text.strip()) < 3:
            return "Take your time! Even a guess helps with learning. Let's move forward and see what happens."
        
        else:
            return "Interesting perspective! Let's explore this together."
    
    def should_ask_followup(self, response: UserResponse) -> bool:
        """Determine if a follow-up question would be beneficial.
        
        Args:
            response: User's response to analyze
            
        Returns:
            True if a follow-up question would help
        """
        # Ask follow-up if response shows confusion or very low confidence
        return (response.sentiment == "confused" or 
                response.confidence_score < 0.3 or
                len(response.text.strip()) < 5)
    
    def generate_followup_question(self, original_response: UserResponse, context: str) -> str:
        """Generate a follow-up question to help confused users.
        
        Args:
            original_response: User's original response
            context: Context for the follow-up
            
        Returns:
            Follow-up question text
        """
        if original_response.sentiment == "confused":
            followups = [
                "What specific part seems unclear?",
                "Would it help to break this down into smaller pieces?",
                "Let's start simpler - what do you think a variable does?",
            ]
        else:
            followups = [
                "Can you elaborate on that?",
                "What makes you think that?",
                "Can you give me an example?"
            ]
        
        return random.choice(followups)