"""Interactive learning session that orchestrates all components."""

import time
from typing import Optional

from .models import ContentLevel, ContentType, Topic, TopicProgress, Challenge
from .code_executor import CodeExecutor
from .socratic_engine import SocraticEngine, QuestionType
from .visual_formatter import VisualFormatter
from .challenge_system import ChallengeSystem


class InteractiveLearningSession:
    """Orchestrates an interactive learning session using all components."""
    
    def __init__(self):
        """Initialize the interactive learning session."""
        self.code_executor = CodeExecutor()
        self.socratic_engine = SocraticEngine()
        self.visual_formatter = VisualFormatter()
        self.challenge_system = ChallengeSystem()
        
        # Session tracking
        self.start_time = time.time()
        self.interactions_count = 0
        self.questions_asked = 0
        self.code_executed_count = 0
    
    def run_topic_session(self, topic: Topic, user_id: str, 
                         starting_level: int = 0, interactive: bool = True) -> TopicProgress:
        """Run a complete interactive learning session for a topic.
        
        Args:
            topic: Topic to learn
            user_id: User identifier
            starting_level: Which level to start from (0-3)
            interactive: Whether to run in interactive mode
            
        Returns:
            TopicProgress object with session results
        """
        # Show topic header
        progress = starting_level / 4.0  # Convert level to progress percentage
        self.visual_formatter.show_topic_header(
            topic.title, 
            topic.estimated_time, 
            topic.difficulty, 
            progress
        )
        
        # Run through content levels
        current_level = starting_level
        for level_num in range(starting_level, 4):
            level_key = str(level_num)
            if level_key not in topic.levels:
                continue
            
            level = topic.levels[level_key]
            level_progress = (level_num + 1) / 4.0
            
            # Run interactive level session
            if interactive:
                self._run_interactive_level(level, level_num, level_progress)
            else:
                self._run_basic_level(level, level_num, level_progress)
            
            current_level = level_num
            self.interactions_count += 1
            
            # Brief pause between levels (except last)
            if level_num < 3 and interactive:
                self.visual_formatter.wait_for_input()
        
        # Run challenges if available
        if topic.challenges and interactive:
            self._run_challenges(topic.challenges)
        
        # Show completion
        self.visual_formatter.show_completion_message(topic.title)
        
        # Calculate session stats
        session_time = time.time() - self.start_time
        
        # Create topic progress
        progress = TopicProgress(
            topic_id=topic.id,
            current_level=current_level,
            completed_levels=list(range(current_level + 1)),
            performance_scores=[1.0] * (current_level + 1),  # Assume successful completion
            last_accessed=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_time_spent=int(session_time)
        )
        
        return progress
    
    def _run_interactive_level(self, level: ContentLevel, level_num: int, progress: float):
        """Run an interactive session for a single content level."""
        # Show level header
        self.visual_formatter.show_content_level_header(level.type, progress)
        
        # For concept levels, ask pre-questions
        if level.type == ContentType.CONCEPT:
            self._handle_concept_interaction(level)
        
        # For example levels, ask prediction questions
        elif level.type in [ContentType.SIMPLE_EXAMPLE, ContentType.MEDIUM_EXAMPLE, ContentType.COMPLEX_EXAMPLE]:
            self._handle_example_interaction(level, level_num)
        
        # Show main content
        self.visual_formatter.show_content(level.content)
        
        # Show pseudocode if available
        if level.pseudocode:
            self.visual_formatter.show_pseudocode(level.pseudocode)
        
        # Show and execute code if available
        if level.code:
            self._show_and_execute_code(level.code)
        
        # Show explanation
        if level.explanation:
            self.visual_formatter.show_explanation(level.explanation)
        
        # Show key concepts
        if level.key_concepts:
            self.visual_formatter.show_key_concepts(level.key_concepts)
    
    def _run_basic_level(self, level: ContentLevel, level_num: int, progress: float):
        """Run a basic (non-interactive) session for a content level."""
        # Show level header
        self.visual_formatter.show_content_level_header(level.type, progress)
        
        # Show content
        self.visual_formatter.show_content(level.content)
        
        # Show pseudocode
        if level.pseudocode:
            self.visual_formatter.show_pseudocode(level.pseudocode)
        
        # Show code with syntax highlighting
        if level.code:
            self.visual_formatter.show_code(level.code)
            if level.output:
                self.visual_formatter.show_output(level.output)
        
        # Show explanation
        if level.explanation:
            self.visual_formatter.show_explanation(level.explanation)
        
        # Show key concepts
        if level.key_concepts:
            self.visual_formatter.show_key_concepts(level.key_concepts)
    
    def _handle_concept_interaction(self, level: ContentLevel):
        """Handle Socratic interaction for concept levels."""
        # Generate and ask concept question
        question = self.socratic_engine.generate_question(level)
        response_text = self.visual_formatter.ask_question(question.text)
        
        # Analyze response
        response = self.socratic_engine.analyze_response(response_text, question)
        
        # Provide feedback
        feedback = self.socratic_engine.generate_feedback(response, question)
        feedback_type = "positive" if response.confidence_score > 0.6 else "neutral"
        self.visual_formatter.show_feedback(feedback, feedback_type)
        
        # Optional follow-up question
        if self.socratic_engine.should_ask_followup(response):
            followup = self.socratic_engine.generate_followup_question(response, level.content)
            followup_response = self.visual_formatter.ask_question(followup)
            self.visual_formatter.show_feedback("Great! Let's see this in action.", "positive")
        
        self.questions_asked += 1
    
    def _handle_example_interaction(self, level: ContentLevel, level_num: int):
        """Handle Socratic interaction for example levels."""
        if not level.code:
            return
        
        # Ask prediction question before showing output
        question = self.socratic_engine.generate_question(level)
        
        # Show the code first
        self.visual_formatter.show_code(level.code, "Let's look at this code:")
        
        # Ask for prediction
        if question.question_type == QuestionType.PREDICTION:
            prediction = self.visual_formatter.ask_question(question.text)
            
            # Analyze prediction
            response = self.socratic_engine.analyze_response(prediction, question)
            
            # Show encouraging feedback
            feedback = "Interesting prediction! Let's run it and see what happens."
            if response.confidence_score > 0.5:
                feedback = "Good thinking! Let's verify your prediction."
            
            self.visual_formatter.show_feedback(feedback, "neutral")
        
        self.questions_asked += 1
    
    def _show_and_execute_code(self, code: str):
        """Show code and execute it with live output."""
        self.visual_formatter.show_execution_status("running")
        
        # Execute the code
        result = self.code_executor.execute_code(code)
        self.code_executed_count += 1
        
        if result.success:
            self.visual_formatter.show_execution_status("success")
            if result.has_output:
                self.visual_formatter.show_output(result.stdout)
        else:
            self.visual_formatter.show_execution_status("error")
            error_msg = self.code_executor.format_error_message(result)
            self.visual_formatter.show_error_message(error_msg)
    
    def _run_challenges(self, challenges: list[Challenge]):
        """Run interactive coding challenges."""
        self.visual_formatter.show_challenge_header(1, len(challenges), challenges[0].difficulty)
        
        for i, challenge in enumerate(challenges, 1):
            success = self._run_single_challenge(challenge, i, len(challenges))
            if success:
                # Move to next challenge
                if i < len(challenges):
                    self.visual_formatter.wait_for_input("Press Enter for next challenge...")
                    self.visual_formatter.show_challenge_header(i + 1, len(challenges), challenges[i].difficulty)
    
    def _run_single_challenge(self, challenge: Challenge, challenge_num: int, total_challenges: int) -> bool:
        """Run a single interactive challenge."""
        # Show challenge
        self.visual_formatter.show_challenge_prompt(challenge.prompt)
        
        if challenge.hints:
            self.visual_formatter.show_hints(challenge.hints)
        
        attempt_number = 1
        max_attempts = 3
        
        while attempt_number <= max_attempts:
            # Get user's code (in a real implementation, this would be interactive)
            # For now, we'll show the solution and simulate success
            self.visual_formatter.console.print("📝 [Simulated: In a full interactive version, you would write code here]")
            self.visual_formatter.console.print()
            
            # Show solution for demonstration
            self.visual_formatter.show_solution(challenge.solution)
            
            # Simulate successful completion
            self.visual_formatter.show_feedback("🎉 Great job! You solved the challenge!", "positive")
            return True
        
        # If we got here, user didn't succeed in max attempts
        self.visual_formatter.show_feedback("Don't worry! Here's the solution to learn from:", "neutral")
        self.visual_formatter.show_solution(challenge.solution)
        return False
    
    def get_session_stats(self) -> dict:
        """Get statistics about the learning session."""
        session_time = time.time() - self.start_time
        return {
            "total_time_seconds": session_time,
            "interactions_count": self.interactions_count,
            "questions_asked": self.questions_asked,
            "code_executed_count": self.code_executed_count,
            "engagement_score": min(1.0, (self.interactions_count + self.questions_asked) / 10.0)
        }