"""Interactive learning session that orchestrates all components.

Main session orchestrator that coordinates all components (visual formatter, code executor, 
socratic engine) to deliver cohesive learning experiences with real-time feedback.
Manages the complete learning flow from content presentation through challenges and validation.
"""

import ast
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
            
            # Execute the code to get actual result
            execution_result = self._show_and_execute_code(level.code)
            
            # Compare prediction to actual result
            match_score = self._compare_prediction_to_result(prediction, execution_result)
            
            # Generate dynamic feedback
            feedback = self._generate_basic_feedback(prediction, execution_result, match_score)
            feedback_type = "positive" if match_score >= 0.7 else "neutral"
            
            self.visual_formatter.show_feedback(feedback, feedback_type)
        
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
        return result
    
    def _compare_prediction_to_result(self, prediction: str, execution_result) -> float:
        """Compare user prediction to actual execution result.
        
        Returns:
            Match score from 0.0 to 1.0
        """
        if not execution_result.success:
            return 0.0
        
        actual_output = execution_result.stdout.strip()
        prediction_clean = prediction.strip()
        
        # Simple exact match
        if prediction_clean == actual_output:
            return 1.0
        
        # Partial match (contains the key parts)
        if actual_output and prediction_clean.lower() in actual_output.lower():
            return 0.7
        
        # Contains some correct elements
        if actual_output and any(word in actual_output.lower() for word in prediction_clean.lower().split()):
            return 0.3
        
        return 0.0
    
    def _generate_basic_feedback(self, prediction: str, execution_result, match_score: float) -> str:
        """Generate contextual feedback based on prediction accuracy."""
        if match_score >= 1.0:
            return "🎉 Exactly right! Great prediction!"
        elif match_score >= 0.7:
            return "👍 Very close! You got the main idea."
        elif match_score >= 0.3:
            return "🤔 You're on the right track, but let's see what actually happens."
        else:
            if execution_result.success:
                actual = execution_result.stdout.strip()
                return f"🔍 Not quite. The actual result is: {actual}"
            else:
                return "🔍 Interesting prediction! Let's run it and see what happens."
    
    def _validate_challenge_solution(self, user_code: str, challenge: Challenge) -> tuple[bool, str]:
        """Validate user's challenge solution using appropriate validator.
        
        Args:
            user_code: User's Python code solution
            challenge: Challenge object with validation metadata
            
        Returns:
            (success, feedback_message)
        """
        # First check if code compiles and runs
        result = self.code_executor.execute_code(user_code)
        if not result.success:
            return False, f"❌ Your code has an error: {result.stderr.strip()}"
        
        # Route to appropriate validator based on challenge type
        validation_type = challenge.validation_type
        
        if validation_type == "code_structure":
            return self._validate_code_structure(user_code, challenge.requirements)
        elif validation_type == "pattern_match":
            return self._validate_pattern_match(user_code, challenge.requirements)
        elif validation_type == "custom":
            return self._validate_custom(user_code, challenge.requirements)
        else:  # "exact_match" or unknown types default to exact match
            expected_output = self._get_expected_output_from_solution(challenge.solution)
            return self._validate_exact_match(user_code, expected_output)
    
    def _get_expected_output_from_solution(self, solution_code: str) -> str:
        """Get expected output by executing the solution code."""
        result = self.code_executor.execute_code(solution_code)
        if result.success:
            return result.stdout.strip()
        return ""
    
    def _validate_exact_match(self, user_code: str, expected_output: str) -> tuple[bool, str]:
        """Validate using exact string matching (original behavior)."""
        result = self.code_executor.execute_code(user_code)
        actual_output = result.stdout.strip()
        expected_clean = expected_output.strip()
        
        if actual_output == expected_clean:
            return True, "🎉 Perfect! Your solution works correctly!"
        else:
            return False, f"❌ Expected: {expected_clean}, but got: {actual_output}"
    
    def _validate_code_structure(self, user_code: str, requirements: dict) -> tuple[bool, str]:
        """Validate code structure using AST analysis."""
        try:
            tree = ast.parse(user_code)
        except SyntaxError:
            return False, "❌ Code has syntax errors"
        
        # Extract code elements
        variables = self._extract_variables(tree)
        print_calls = self._extract_print_calls(tree)
        
        # Check variable requirements
        if "variables_required" in requirements:
            for var_name in requirements["variables_required"]:
                if var_name not in variables:
                    return False, f"❌ Missing required variable: {var_name}"
        
        # Check print usage
        if requirements.get("uses_print", False):
            if not print_calls:
                return False, "❌ Your solution should include a print statement"
        
        # Check f-string usage
        if requirements.get("uses_f_string", False):
            has_f_string = any("f-string" in call.get("type", "") for call in print_calls)
            if not has_f_string:
                return False, "❌ Try using f-string formatting in your print statement"
        
        # Check multiple assignment usage
        if requirements.get("uses_multiple_assignment", False):
            has_multiple_assignment = self._has_multiple_assignment(tree)
            if not has_multiple_assignment:
                return False, "❌ Try using multiple assignment (a, b = b, a)"
        
        # Check sorted with reverse usage
        if requirements.get("uses_sorted_with_reverse", False):
            has_sorted_reverse = self._uses_sorted_with_reverse(tree)
            if not has_sorted_reverse:
                return False, "❌ Use sorted(list, reverse=True) to sort in descending order"
        
        # Check slicing usage
        if requirements.get("uses_slicing", False):
            has_slicing = self._uses_slicing(tree)
            if not has_slicing:
                return False, "❌ Use list slicing [:3] to get the first 3 items"
        
        # Check average calculation
        if requirements.get("calculates_average", False):
            calculates_avg = self._calculates_average(tree)
            if not calculates_avg:
                return False, "❌ Calculate the average using sum() and division"
        
        # Check index finding
        if requirements.get("finds_indices", False):
            finds_indices = self._finds_indices(tree)
            if not finds_indices:
                return False, "❌ Use .index() to find positions in the original list"
        
        return True, "🎉 Excellent code structure! You've mastered the concepts!"
    
    def _validate_pattern_match(self, user_code: str, requirements: dict) -> tuple[bool, str]:
        """Validate using flexible pattern matching."""
        import re
        
        # Check for pattern in the code itself
        if "pattern" in requirements:
            pattern = requirements["pattern"]
            if not re.search(pattern, user_code):
                return False, "❌ Your code doesn't use the required swapping pattern (a, b = b, a)"
        
        # Check for minimum number of variables
        if "min_variables" in requirements:
            # Count variable assignments in the code
            import ast
            try:
                tree = ast.parse(user_code)
                variables = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                variables.add(target.id)
                            elif isinstance(target, ast.Tuple):
                                for elt in target.elts:
                                    if isinstance(elt, ast.Name):
                                        variables.add(elt.id)
                
                if len(variables) < requirements["min_variables"]:
                    return False, f"❌ You need at least {requirements['min_variables']} variables"
            except:
                pass  # Continue with other checks
        
        # Check if multiple assignment is used
        if requirements.get("uses_multiple_assignment"):
            # Check for tuple assignment pattern (a, b = ...)
            if not re.search(r'\w+\s*,\s*\w+\s*=', user_code):
                return False, "❌ Use Python's multiple assignment feature (a, b = b, a)"
        
        # Execute and check output if needed
        result = self.code_executor.execute_code(user_code)
        if not result.success:
            return False, f"❌ Code error: {result.stderr}"
        
        output = result.stdout.strip()
        
        # Check if output contains required patterns
        if "must_contain" in requirements:
            for pattern in requirements["must_contain"]:
                if pattern.lower() not in output.lower():
                    return False, f"❌ Output should contain: {pattern}"
        
        # Check if output matches regex patterns
        if "regex_patterns" in requirements:
            for pattern in requirements["regex_patterns"]:
                if not re.search(pattern, output):
                    return False, f"❌ Output doesn't match expected pattern"
        
        return True, "🎉 Perfect! You've successfully swapped the variables using Python's elegant multiple assignment!"
    
    def _validate_custom(self, user_code: str, requirements: dict) -> tuple[bool, str]:
        """Custom validation hook for special cases."""
        # This can be extended for specific challenge needs
        return True, "🎉 Custom validation passed!"
    
    def _extract_variables(self, tree: ast.AST) -> dict[str, str]:
        """Extract variable assignments from AST."""
        variables = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Try to get the value (simplified)
                        if isinstance(node.value, ast.Constant):
                            variables[target.id] = str(node.value.value)
                        else:
                            variables[target.id] = "complex_value"
        return variables
    
    def _extract_print_calls(self, tree: ast.AST) -> list[dict]:
        """Extract print function calls and analyze their structure."""
        print_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Name) and node.func.id == "print"):
                    call_info = {"type": "print"}
                    
                    # Check if using f-string
                    for arg in node.args:
                        if isinstance(arg, ast.JoinedStr):  # f-string
                            call_info["type"] = "f-string"
                            break
                    
                    print_calls.append(call_info)
        return print_calls
    
    def _has_multiple_assignment(self, tree: ast.AST) -> bool:
        """Check if code uses multiple assignment (tuple unpacking)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check if target is a tuple/list (multiple assignment)
                for target in node.targets:
                    if isinstance(target, (ast.Tuple, ast.List)):
                        if len(target.elts) > 1:
                            return True
        return False
    
    def _uses_sorted_with_reverse(self, tree: ast.AST) -> bool:
        """Check if code uses sorted() with reverse=True parameter."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's a call to 'sorted'
                if isinstance(node.func, ast.Name) and node.func.id == "sorted":
                    # Check for reverse=True keyword argument
                    for keyword in node.keywords:
                        if keyword.arg == "reverse" and isinstance(keyword.value, ast.Constant):
                            if keyword.value.value is True:
                                return True
        return False
    
    def _uses_slicing(self, tree: ast.AST) -> bool:
        """Check if code uses list slicing."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                # Check if it's slicing (has slice object)
                if isinstance(node.slice, ast.Slice):
                    return True
        return False
    
    def _calculates_average(self, tree: ast.AST) -> bool:
        """Check if code calculates average using sum() and division."""
        has_sum = False
        has_division = False
        
        for node in ast.walk(tree):
            # Check for sum() function call
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "sum":
                    has_sum = True
            
            # Check for division operation
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                has_division = True
        
        return has_sum and has_division
    
    def _finds_indices(self, tree: ast.AST) -> bool:
        """Check if code uses .index() method to find positions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's a method call to 'index'
                if isinstance(node.func, ast.Attribute) and node.func.attr == "index":
                    return True
        return False
    
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
            # Get user's code attempt
            self.visual_formatter.console.print(f"💻 Attempt {attempt_number}/{max_attempts}")
            user_code = self.visual_formatter.ask_code_input("Enter your Python code solution:")
            
            # If user enters 'skip' or empty code, show solution
            if user_code.lower().strip() in ['skip', '']:
                self.visual_formatter.show_feedback("Showing solution to learn from:", "neutral")
                self.visual_formatter.show_solution(challenge.solution)
                return True
            
            # Validate the solution
            success, feedback = self._validate_challenge_solution(user_code, challenge)
            
            if success:
                self.visual_formatter.show_feedback(feedback, "positive")
                return True
            else:
                self.visual_formatter.show_feedback(feedback, "error")
                
                # Show progressive hints
                if attempt_number < max_attempts and challenge.hints:
                    hint_index = min(attempt_number - 1, len(challenge.hints) - 1)
                    self.visual_formatter.console.print(f"💡 Hint {attempt_number}: {challenge.hints[hint_index]}")
                
                attempt_number += 1
        
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