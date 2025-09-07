"""Tests for the Socratic questioning engine."""

import pytest

from python_ai_tutor.models import ContentLevel, ContentType
from python_ai_tutor.socratic_engine import (
    QuestionType, Question, UserResponse, SocraticEngine
)


class TestSocraticEngine:
    """Test the Socratic questioning functionality."""
    
    def setup_method(self):
        """Set up test engine for each test."""
        self.engine = SocraticEngine()
    
    def test_generate_concept_question(self):
        """Should generate appropriate questions for concept level."""
        content = ContentLevel(
            type=ContentType.CONCEPT,
            content="Variables store values for later use"
        )
        
        question = self.engine.generate_question(content)
        
        assert isinstance(question, Question)
        assert question.question_type in [QuestionType.CONCEPT, QuestionType.REFLECTION]
        assert len(question.text) > 10  # Should be a meaningful question
        assert question.context == content.content
        assert len(question.hints) > 0
    
    def test_generate_simple_example_question(self):
        """Should generate prediction questions for simple examples."""
        content = ContentLevel(
            type=ContentType.SIMPLE_EXAMPLE,
            content="Basic variable assignment",
            code='age = 25\nprint(age)'
        )
        
        question = self.engine.generate_question(content)
        
        assert question.question_type in [QuestionType.PREDICTION, QuestionType.CONCEPT]
        # Should include relevant keywords (variable-related, output-related, or assignment-related)
        relevant_keywords = ["variable", "store", "assign", "print", "output", "data", "hold"]
        assert any(kw.lower() in relevant_keywords or any(rel in kw.lower() for rel in relevant_keywords) 
                  for kw in question.expected_keywords)
        assert len(question.hints) > 0
    
    def test_generate_complex_example_question(self):
        """Should generate reflection or application questions for complex examples."""
        content = ContentLevel(
            type=ContentType.COMPLEX_EXAMPLE,
            content="Advanced variable patterns",
            code='x, y = 10, 20\nx, y = y, x'
        )
        
        question = self.engine.generate_question(content)
        
        assert question.question_type in [QuestionType.REFLECTION, QuestionType.APPLICATION]
        assert question.text is not None
        assert len(question.text) > 5
    
    def test_analyze_confident_response(self):
        """Should analyze detailed, confident responses correctly."""
        question = Question(
            question_type=QuestionType.CONCEPT,
            text="What is a variable?",
            context="Variables store data",
            expected_keywords=["store", "data", "container"]
        )
        
        response_text = "A variable is like a container that stores data for later use"
        response = self.engine.analyze_response(response_text, question)
        
        assert isinstance(response, UserResponse)
        assert response.confidence_score > 0.5  # Should be confident
        assert "store" in response.contains_keywords
        assert "data" in response.contains_keywords
        assert response.sentiment in ["positive", "neutral"]
    
    def test_analyze_confused_response(self):
        """Should detect confused responses."""
        question = Question(
            question_type=QuestionType.CONCEPT,
            text="What is a variable?",
            context="Variables store data",
            expected_keywords=["store", "data"]
        )
        
        response_text = "I'm confused and don't understand"
        response = self.engine.analyze_response(response_text, question)
        
        assert response.sentiment == "confused"
        assert response.confidence_score < 0.5
    
    def test_analyze_empty_response(self):
        """Should handle empty or very short responses."""
        question = Question(
            question_type=QuestionType.PREDICTION,
            text="What will this output?",
            context="print('hello')",
            expected_keywords=["hello", "output"]
        )
        
        response = self.engine.analyze_response("", question)
        assert response.confidence_score < 0.3
        
        response = self.engine.analyze_response("?", question)
        assert response.confidence_score < 0.3
    
    def test_generate_positive_feedback(self):
        """Should generate encouraging feedback for good responses."""
        response = UserResponse(
            text="Variables store data like containers",
            confidence_score=0.8,
            contains_keywords=["store", "data"],
            sentiment="positive"
        )
        
        question = Question(
            question_type=QuestionType.CONCEPT,
            text="What is a variable?",
            context="Variables",
            hints=["Think of containers"]
        )
        
        feedback = self.engine.generate_feedback(response, question)
        
        assert len(feedback) > 10
        assert any(word in feedback.lower() for word in ["excellent", "great", "perfect", "outstanding"])
    
    def test_generate_confused_feedback(self):
        """Should provide helpful feedback for confused responses."""
        response = UserResponse(
            text="I don't understand this at all",
            confidence_score=0.2,
            contains_keywords=[],
            sentiment="confused"
        )
        
        question = Question(
            question_type=QuestionType.CONCEPT,
            text="What is a variable?",
            context="Variables",
            hints=["Think of containers", "Consider storage"]
        )
        
        feedback = self.engine.generate_feedback(response, question)
        
        assert "no worries" in feedback.lower() or "let's" in feedback.lower()
        assert any(hint.lower() in feedback.lower() for hint in question.hints)
    
    def test_should_ask_followup(self):
        """Should determine when follow-up questions are needed."""
        # Confused response should trigger follow-up
        confused_response = UserResponse(
            text="I'm confused",
            confidence_score=0.1,
            sentiment="confused"
        )
        assert self.engine.should_ask_followup(confused_response) is True
        
        # Confident response should not need follow-up
        confident_response = UserResponse(
            text="Variables store data in memory for later use",
            confidence_score=0.9,
            sentiment="positive"
        )
        assert self.engine.should_ask_followup(confident_response) is False
        
        # Very short response should trigger follow-up
        short_response = UserResponse(
            text="ok",
            confidence_score=0.2,
            sentiment="neutral"
        )
        assert self.engine.should_ask_followup(short_response) is True
    
    def test_generate_followup_question(self):
        """Should generate appropriate follow-up questions."""
        confused_response = UserResponse(
            text="This is confusing",
            sentiment="confused"
        )
        
        followup = self.engine.generate_followup_question(confused_response, "variables")
        
        assert len(followup) > 5
        assert followup.endswith("?")  # Should be a question
        
        # Test low-confidence response
        low_confidence_response = UserResponse(
            text="maybe",
            confidence_score=0.1,
            sentiment="neutral"
        )
        
        followup = self.engine.generate_followup_question(low_confidence_response, "variables")
        assert len(followup) > 5
    
    def test_keyword_extraction(self):
        """Should extract relevant keywords from content."""
        content = ContentLevel(
            type=ContentType.SIMPLE_EXAMPLE,
            content="Variable assignment example",
            code='name = "Alice"\nprint(f"Hello {name}")'
        )
        
        question = self.engine.generate_question(content)
        
        # Should include variable-related keywords
        assert any("variable" in kw.lower() or "store" in kw.lower() 
                  for kw in question.expected_keywords)
        
        # Should include output-related keywords since there's a print
        assert any("print" in kw.lower() or "output" in kw.lower() 
                  for kw in question.expected_keywords)
    
    def test_question_template_formatting(self):
        """Should format question templates correctly."""
        content = ContentLevel(
            type=ContentType.SIMPLE_EXAMPLE,
            content="Example with variables",
            code='age = 25\nname = "Bob"'
        )
        
        question = self.engine.generate_question(content)
        
        # Question should be properly formatted (no template placeholders)
        assert "{" not in question.text
        assert "}" not in question.text
        assert len(question.text) > 10
    
    def test_different_content_types_generate_different_questions(self):
        """Should generate different types of questions for different content types."""
        concept_content = ContentLevel(
            type=ContentType.CONCEPT,
            content="Variables are containers"
        )
        
        simple_content = ContentLevel(
            type=ContentType.SIMPLE_EXAMPLE,
            content="Simple example",
            code="x = 5"
        )
        
        complex_content = ContentLevel(
            type=ContentType.COMPLEX_EXAMPLE,
            content="Complex example",
            code="a, b = b, a"
        )
        
        concept_q = self.engine.generate_question(concept_content)
        simple_q = self.engine.generate_question(simple_content)
        complex_q = self.engine.generate_question(complex_content)
        
        # Should generate different types of questions
        question_types = {concept_q.question_type, simple_q.question_type, complex_q.question_type}
        assert len(question_types) >= 2  # At least 2 different types
        
        # Concept should not generate prediction questions
        assert concept_q.question_type != QuestionType.PREDICTION
        
        # Simple examples often generate prediction questions
        # Complex examples often generate reflection/application questions