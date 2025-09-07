"""Interactive challenge system for coding practice.

Interactive coding challenges with multiple validation types (exact match, code structure, 
pattern matching) and attempt tracking with progressive hints.
Provides flexible validation that recognizes different correct solutions to the same problem.
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .models import Challenge
from .code_executor import CodeExecutor, ExecutionResult


@dataclass
class ValidationResult:
    """Result of challenge solution validation."""
    
    is_correct: bool
    score: float  # 0.0 - 1.0
    feedback: str
    output_matches: bool = False
    code_quality_notes: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.code_quality_notes is None:
            self.code_quality_notes = []
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class ChallengeAttempt:
    """Track user's attempt at solving a challenge."""
    
    challenge_id: str
    user_code: str
    validation_result: ValidationResult
    attempt_number: int
    hints_used: int = 0
    time_spent: float = 0.0  # seconds


class ChallengeSystem:
    """System for managing interactive coding challenges."""
    
    def __init__(self):
        """Initialize the challenge system."""
        self.code_executor = CodeExecutor()
        self.attempts_history: List[ChallengeAttempt] = []
    
    def collect_user_code(self, prompt_text: str = "Write your solution below") -> str:
        """Collect multi-line code input from user.
        
        Args:
            prompt_text: Prompt to show user
            
        Returns:
            User's code as string
        """
        print(f"\n📝 {prompt_text}")
        print("(Type your code, then press Ctrl+D on Linux/Mac or Ctrl+Z then Enter on Windows when done)")
        print(">" + "-" * 50)
        
        lines = []
        try:
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    # User pressed Ctrl+D (Unix) or Ctrl+Z (Windows)
                    break
        except KeyboardInterrupt:
            # User pressed Ctrl+C - cancel
            return ""
        
        print("-" * 50)
        code = "\n".join(lines)
        return code.strip()
    
    def validate_solution(self, challenge: Challenge, user_code: str, attempt_number: int = 1) -> ValidationResult:
        """Validate user's solution against challenge requirements.
        
        Args:
            challenge: Challenge to validate against
            user_code: User's code solution
            attempt_number: Which attempt this is (for progressive hints)
            
        Returns:
            ValidationResult with feedback and score
        """
        if not user_code.strip():
            return ValidationResult(
                is_correct=False,
                score=0.0,
                feedback="No code provided. Please write some code to solve the challenge.",
                suggestions=["Try writing at least one line of code", "Look at the challenge prompt for guidance"]
            )
        
        # Execute user's code
        execution_result = self.code_executor.execute_code(user_code)
        
        # If code doesn't run, provide execution feedback
        if not execution_result.success:
            error_feedback = self.code_executor.format_error_message(execution_result)
            return ValidationResult(
                is_correct=False,
                score=0.0,
                feedback=f"Code execution failed: {error_feedback}",
                suggestions=self._get_error_suggestions(execution_result)
            )
        
        # Check if output matches expected (for challenges with specific output)
        output_matches = False
        if hasattr(challenge, 'expected_output') and challenge.expected_output:
            output_matches = self._compare_outputs(execution_result.stdout, challenge.expected_output)
        
        # Analyze code quality and requirements
        code_analysis = self._analyze_code_quality(user_code, challenge)
        requirements_met = self._check_requirements(user_code, challenge)
        
        # Calculate score
        score = self._calculate_score(
            output_matches, 
            requirements_met, 
            code_analysis,
            execution_result.success
        )
        
        # Generate feedback
        feedback = self._generate_feedback(
            challenge, 
            user_code, 
            execution_result,
            output_matches,
            requirements_met, 
            code_analysis,
            attempt_number
        )
        
        is_correct = score >= 0.8  # 80% threshold for correctness
        
        return ValidationResult(
            is_correct=is_correct,
            score=score,
            feedback=feedback,
            output_matches=output_matches,
            code_quality_notes=code_analysis['notes'],
            suggestions=code_analysis['suggestions']
        )
    
    def _compare_outputs(self, actual_output: str, expected_output: str) -> bool:
        """Compare actual vs expected output with some flexibility."""
        # Normalize whitespace
        actual_clean = re.sub(r'\s+', ' ', actual_output.strip())
        expected_clean = re.sub(r'\s+', ' ', expected_output.strip())
        
        return actual_clean.lower() == expected_clean.lower()
    
    def _check_requirements(self, user_code: str, challenge: Challenge) -> Dict[str, bool]:
        """Check if code meets specific challenge requirements."""
        requirements = {}
        
        # Parse code to AST for analysis
        try:
            tree = ast.parse(user_code)
        except SyntaxError:
            return {"valid_syntax": False}
        
        requirements["valid_syntax"] = True
        
        # Check for specific patterns based on challenge content
        code_lower = user_code.lower()
        
        # For variable challenges
        if "variable" in challenge.prompt.lower():
            # Should contain variable assignments
            assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
            requirements["has_variables"] = len(assignments) > 0
        
        # For print challenges  
        if "print" in challenge.prompt.lower():
            # Should contain print statements
            requirements["has_print"] = "print" in code_lower
        
        # For f-string challenges
        if "f-string" in challenge.prompt.lower() or "format" in challenge.prompt.lower():
            requirements["uses_formatting"] = "f\"" in user_code or ".format(" in user_code
        
        return requirements
    
    def _analyze_code_quality(self, user_code: str, challenge: Challenge) -> Dict[str, Any]:
        """Analyze code quality and provide suggestions."""
        notes = []
        suggestions = []
        
        try:
            tree = ast.parse(user_code)
        except SyntaxError:
            return {
                "quality_score": 0.0,
                "notes": ["Code has syntax errors"],
                "suggestions": ["Check for typos, missing quotes, or parentheses"]
            }
        
        # Check for good practices
        if "print(" in user_code and 'f"' in user_code:
            notes.append("Great use of f-strings for formatting!")
        elif "print(" in user_code and ("format(" in user_code or "%" in user_code):
            notes.append("Good formatting, but f-strings are more modern")
            suggestions.append("Try using f-strings: f\"Hello {name}\" instead of older formatting")
        
        # Check variable naming
        variable_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                variable_names.append(node.id)
        
        if variable_names:
            if all(len(name) > 1 and name.islower() for name in variable_names):
                notes.append("Excellent variable naming!")
            elif any(len(name) == 1 for name in variable_names):
                suggestions.append("Consider using more descriptive variable names than single letters")
        
        # Check for unnecessary complexity
        if user_code.count('\n') > 10:
            suggestions.append("Your solution works but could be simpler")
        
        quality_score = min(1.0, len(notes) * 0.3 + 0.4)  # Base score with bonuses
        
        return {
            "quality_score": quality_score,
            "notes": notes,
            "suggestions": suggestions
        }
    
    def _calculate_score(self, output_matches: bool, requirements_met: Dict[str, bool], 
                        code_analysis: Dict[str, Any], execution_success: bool) -> float:
        """Calculate overall score for the solution."""
        if not execution_success:
            return 0.0
        
        score = 0.0
        
        # Execution success (basic requirement)
        score += 0.3
        
        # Output matching (if applicable)
        if output_matches:
            score += 0.4
        
        # Requirements met
        req_score = sum(requirements_met.values()) / max(len(requirements_met), 1)
        score += req_score * 0.2
        
        # Code quality
        score += code_analysis['quality_score'] * 0.1
        
        return min(score, 1.0)
    
    def _generate_feedback(self, challenge: Challenge, user_code: str, execution_result: ExecutionResult,
                          output_matches: bool, requirements_met: Dict[str, bool], 
                          code_analysis: Dict[str, Any], attempt_number: int) -> str:
        """Generate comprehensive feedback for the user."""
        feedback_parts = []
        
        # Execution feedback
        if execution_result.success:
            feedback_parts.append("✅ Your code runs successfully!")
            
            if execution_result.has_output:
                feedback_parts.append(f"📤 Output: {execution_result.stdout}")
            
            # Output matching feedback
            if hasattr(challenge, 'expected_output') and challenge.expected_output:
                if output_matches:
                    feedback_parts.append("🎯 Perfect! Your output matches exactly.")
                else:
                    feedback_parts.append("🔍 Your output is close but not exactly right.")
        
        # Requirements feedback
        unmet_requirements = [req for req, met in requirements_met.items() if not met]
        if unmet_requirements:
            feedback_parts.append("📋 Requirements check:")
            for req in unmet_requirements:
                if req == "has_variables":
                    feedback_parts.append("   • Try creating some variables with the = operator")
                elif req == "has_print": 
                    feedback_parts.append("   • Don't forget to print your result")
                elif req == "uses_formatting":
                    feedback_parts.append("   • Try using f-strings to format your output")
        
        # Code quality feedback
        if code_analysis['notes']:
            feedback_parts.append("💡 Code quality notes:")
            for note in code_analysis['notes']:
                feedback_parts.append(f"   • {note}")
        
        # Suggestions
        if code_analysis['suggestions']:
            feedback_parts.append("🔧 Suggestions for improvement:")
            for suggestion in code_analysis['suggestions']:
                feedback_parts.append(f"   • {suggestion}")
        
        return "\n".join(feedback_parts)
    
    def _get_error_suggestions(self, execution_result: ExecutionResult) -> List[str]:
        """Get specific suggestions based on execution errors."""
        if execution_result.error_type == "syntax":
            return [
                "Check for matching quotes and parentheses",
                "Make sure your indentation is consistent",
                "Look for typos in keywords like 'print' or 'if'"
            ]
        elif execution_result.error_type == "runtime":
            if "nameerror" in execution_result.stderr.lower():
                return [
                    "Make sure you've defined all variables before using them",
                    "Check for typos in variable names"
                ]
            elif "zerodivisionerror" in execution_result.stderr.lower():
                return [
                    "Avoid dividing by zero",
                    "Check that denominators are not zero"
                ]
        elif execution_result.error_type == "timeout":
            return [
                "Check for infinite loops",
                "Make sure your loops have a way to end"
            ]
        
        return ["Try running your code step by step to find the issue"]
    
    def provide_hint(self, challenge: Challenge, attempt_number: int) -> str:
        """Provide progressive hints based on attempt number."""
        if attempt_number <= 1:
            # First hint - very general
            if challenge.hints:
                return f"💡 Hint: {challenge.hints[0]}"
            else:
                return "💡 Hint: Break down the problem into smaller steps"
        
        elif attempt_number <= 2:
            # Second hint - more specific
            if len(challenge.hints) > 1:
                return f"💡 Hint: {challenge.hints[1]}"
            else:
                return "💡 Hint: Look at the example code patterns from the lesson"
        
        else:
            # Final hint - very specific
            if len(challenge.hints) > 2:
                return f"💡 Hint: {challenge.hints[2]}"
            else:
                return f"💡 Strong Hint: Try something like this structure:\n{self._generate_code_template(challenge)}"
    
    def _generate_code_template(self, challenge: Challenge) -> str:
        """Generate a basic code template for the challenge."""
        # This is a simple template generator - could be made more sophisticated
        if "variable" in challenge.prompt.lower() and "print" in challenge.prompt.lower():
            return """# Create your variables here
variable_name = "your_value"
# Print your result
print(f"Your message with {variable_name}")"""
        else:
            return "# Write your code here\nprint(\"Your result\")"
    
    def record_attempt(self, challenge_id: str, user_code: str, validation_result: ValidationResult,
                      attempt_number: int, hints_used: int = 0, time_spent: float = 0.0):
        """Record user's attempt for analytics and progress tracking."""
        attempt = ChallengeAttempt(
            challenge_id=challenge_id,
            user_code=user_code,
            validation_result=validation_result,
            attempt_number=attempt_number,
            hints_used=hints_used,
            time_spent=time_spent
        )
        
        self.attempts_history.append(attempt)
        return attempt