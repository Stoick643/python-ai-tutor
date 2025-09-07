"""Tests for the secure code execution engine."""

import pytest
import time

from python_ai_tutor.code_executor import CodeExecutor, ExecutionResult


class TestCodeExecutor:
    """Test the secure code execution functionality."""
    
    def setup_method(self):
        """Set up test executor for each test."""
        self.executor = CodeExecutor(timeout=2)  # Short timeout for tests
    
    def test_basic_code_execution(self):
        """Should execute basic Python code successfully."""
        code = 'print("Hello, World!")'
        result = self.executor.execute_code(code)
        
        assert result.success is True
        assert result.stdout == "Hello, World!"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.error_type is None
        assert result.has_output is True
    
    def test_variable_assignment_and_output(self):
        """Should handle variable assignment and output correctly."""
        code = """
age = 25
name = "Alice"
print(f"Hello {name}, you are {age} years old")
"""
        result = self.executor.execute_code(code)
        
        assert result.success is True
        assert result.stdout == "Hello Alice, you are 25 years old"
        assert result.error_type is None
    
    def test_mathematical_operations(self):
        """Should handle mathematical operations correctly."""
        code = """
x = 10
y = 5
print(x + y)
print(x - y)
print(x * y)
print(x // y)
"""
        result = self.executor.execute_code(code)
        
        assert result.success is True
        expected_output = "15\n5\n50\n2"
        assert result.stdout == expected_output
    
    def test_empty_code(self):
        """Should handle empty code gracefully."""
        result = self.executor.execute_code("")
        
        assert result.success is False
        assert result.error_type == "validation"
        assert "empty" in result.stderr.lower()
    
    def test_syntax_error_handling(self):
        """Should detect and handle syntax errors gracefully."""
        code = 'print("unclosed string'
        result = self.executor.execute_code(code)
        
        assert result.success is False
        assert result.error_type == "validation"  # Caught by AST parsing
        assert "syntax error" in result.stderr.lower()
    
    def test_runtime_error_zero_division(self):
        """Should handle runtime errors like division by zero."""
        code = "print(10 / 0)"
        result = self.executor.execute_code(code)
        
        assert result.success is False
        assert result.error_type == "runtime"
        assert result.exit_code != 0
    
    def test_runtime_error_undefined_variable(self):
        """Should handle undefined variable errors."""
        code = "print(undefined_variable)"
        result = self.executor.execute_code(code)
        
        assert result.success is False
        assert result.error_type == "runtime"
        assert "nameerror" in result.stderr.lower()
    
    def test_timeout_protection(self):
        """Should timeout infinite loops and long-running code."""
        code = "while True: pass"
        start_time = time.time()
        result = self.executor.execute_code(code)
        execution_time = time.time() - start_time
        
        assert result.success is False
        assert result.is_timeout is True
        assert result.error_type == "timeout"
        assert execution_time >= self.executor.timeout
        assert "timed out" in result.stderr.lower()
    
    def test_restricted_import_os(self):
        """Should block dangerous imports like os module."""
        code = "import os; os.system('echo dangerous')"
        result = self.executor.execute_code(code)
        
        assert result.success is False
        assert result.error_type == "validation"
        assert "not allowed" in result.stderr.lower()
        assert "os" in result.stderr
    
    def test_restricted_import_subprocess(self):
        """Should block subprocess imports."""
        code = "import subprocess; subprocess.run(['ls'])"
        result = self.executor.execute_code(code)
        
        assert result.success is False
        assert result.error_type == "validation"
        assert "subprocess" in result.stderr
    
    def test_restricted_function_open(self):
        """Should block file operations."""
        code = "open('/etc/passwd', 'r')"
        result = self.executor.execute_code(code)
        
        assert result.success is False
        assert result.error_type == "validation"
        assert "open" in result.stderr
    
    def test_restricted_function_exec(self):
        """Should block exec function."""
        code = "exec('print(\"dangerous\")')"
        result = self.executor.execute_code(code)
        
        assert result.success is False
        assert result.error_type == "validation"
        assert "exec" in result.stderr
    
    def test_allowed_imports(self):
        """Should allow safe imports like math."""
        code = """
import math
print(math.pi)
"""
        result = self.executor.execute_code(code)
        
        assert result.success is True
        assert "3.14159" in result.stdout
    
    def test_allowed_random_import(self):
        """Should allow random module for educational purposes."""
        code = """
import random
random.seed(42)  # Make it deterministic for testing
print(random.randint(1, 10))
"""
        result = self.executor.execute_code(code)
        
        assert result.success is True
        assert result.stdout.isdigit()
    
    def test_complex_variable_operations(self):
        """Should handle complex variable operations from curriculum."""
        code = """
# Multiple assignment
x, y, z = 1, 2, 3
print(f"x={x}, y={y}, z={z}")

# Variable swapping
a, b = 10, 20
a, b = b, a
print(f"a={a}, b={b}")

# Chain assignment
first = second = third = 0
print(f"All equal: {first}, {second}, {third}")
"""
        result = self.executor.execute_code(code)
        
        assert result.success is True
        expected_lines = [
            "x=1, y=2, z=3",
            "a=20, b=10", 
            "All equal: 0, 0, 0"
        ]
        assert all(line in result.stdout for line in expected_lines)
    
    def test_output_length_limiting(self):
        """Should limit very long output."""
        executor = CodeExecutor(max_output_length=50)
        code = 'print("x" * 1000)'
        result = executor.execute_code(code)
        
        assert result.success is True
        assert len(result.stdout) <= 100  # Includes truncation message
        assert "truncated" in result.stdout
    
    def test_error_message_formatting(self):
        """Should provide user-friendly error messages."""
        # Test zero division error formatting
        result = self.executor.execute_code("print(1/0)")
        formatted = self.executor.format_error_message(result)
        assert "🔢" in formatted
        assert "divide by zero" in formatted.lower()
        
        # Test name error formatting  
        result = self.executor.execute_code("print(unknown)")
        formatted = self.executor.format_error_message(result)
        assert "🏷️" in formatted
        assert "not defined" in formatted.lower()
        
        # Test timeout formatting
        result = self.executor.execute_code("while True: pass")
        formatted = self.executor.format_error_message(result)
        assert "⏱️" in formatted
        assert "timeout" in formatted.lower()
    
    def test_execution_result_properties(self):
        """Should provide useful properties on ExecutionResult."""
        # Test successful execution
        result = self.executor.execute_code('print("test")')
        assert result.has_output is True
        assert result.is_timeout is False
        assert result.is_syntax_error is False
        assert result.is_runtime_error is False
        
        # Test no output
        result = self.executor.execute_code('x = 5')
        assert result.success is True
        assert result.has_output is False
        
        # Test timeout
        result = self.executor.execute_code('while True: pass')
        assert result.is_timeout is True
    
    def test_variables_curriculum_examples(self):
        """Should handle all examples from variables.json successfully."""
        # Test simple example from curriculum
        simple_code = """
age = 25
name = "Alice"
print(f"Hello {name}, you are {age} years old")
"""
        result = self.executor.execute_code(simple_code)
        assert result.success is True
        assert "Hello Alice, you are 25 years old" in result.stdout
        
        # Test medium example from curriculum
        medium_code = """
score = 85
print(f"Original score: {score}")

score = score + 10
print(f"Bonus applied: {score}")

final_grade = "A" if score >= 90 else "B"
print(f"Final grade: {final_grade}")
"""
        result = self.executor.execute_code(medium_code)
        assert result.success is True
        assert "Original score: 85" in result.stdout
        assert "Bonus applied: 95" in result.stdout
        assert "Final grade: A" in result.stdout