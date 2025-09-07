"""Secure Python code execution engine for educational content."""

import ast
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional, Set


@dataclass
class ExecutionResult:
    """Result of code execution with comprehensive information."""
    
    success: bool
    stdout: str
    stderr: str
    execution_time: float
    exit_code: int
    error_type: Optional[str] = None  # "syntax", "runtime", "timeout", "validation"
    
    @property
    def has_output(self) -> bool:
        """Check if execution produced any output."""
        return bool(self.stdout.strip())
    
    @property
    def is_timeout(self) -> bool:
        """Check if execution timed out."""
        return self.error_type == "timeout"
    
    @property
    def is_syntax_error(self) -> bool:
        """Check if there was a syntax error."""
        return self.error_type == "syntax"
    
    @property
    def is_runtime_error(self) -> bool:
        """Check if there was a runtime error."""
        return self.error_type == "runtime"


class CodeExecutor:
    """Secure executor for educational Python code snippets."""
    
    # Modules that are restricted for security
    RESTRICTED_IMPORTS: Set[str] = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
        'http', 'ftplib', 'smtplib', 'sqlite3', 'pickle', 'shelve',
        'marshal', 'importlib', 'ctypes', 'multiprocessing', 'threading',
        'asyncio', 'concurrent', 'queue', 'atexit', 'signal', 'gc'
    }
    
    # Functions that are not allowed
    RESTRICTED_FUNCTIONS: Set[str] = {
        'open', 'exec', 'eval', 'compile', 'globals', 'locals',
        'vars', 'dir', 'getattr', 'setattr', 'delattr', 'hasattr',
        'callable', 'isinstance', 'issubclass', 'super', '__import__'
    }
    
    def __init__(self, timeout: int = 5, max_output_length: int = 1000):
        """Initialize code executor with security settings.
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_length: Maximum length of output to capture
        """
        self.timeout = timeout
        self.max_output_length = max_output_length
    
    def validate_code_safety(self, code: str) -> tuple[bool, str]:
        """Validate code for security issues before execution.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if not code.strip():
            return False, "Code is empty"
        
        # Try to parse the code
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e.msg} (line {e.lineno})"
        
        # Walk through all nodes in the AST
        for node in ast.walk(tree):
            # Check for restricted imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in self.RESTRICTED_IMPORTS:
                        return False, f"Import '{alias.name}' is not allowed for security reasons"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in self.RESTRICTED_IMPORTS:
                    return False, f"Import from '{node.module}' is not allowed for security reasons"
            
            # Check for restricted function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.RESTRICTED_FUNCTIONS:
                    return False, f"Function '{node.func.id}' is not allowed for security reasons"
            
            # Check for attribute access on restricted modules
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id in self.RESTRICTED_IMPORTS:
                    return False, f"Access to '{node.value.id}.{node.attr}' is not allowed"
        
        return True, "Code is safe to execute"
    
    def execute_code(self, code: str) -> ExecutionResult:
        """Execute Python code safely and return results.
        
        Args:
            code: Python code to execute
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = time.time()
        
        # Validate code safety first
        is_safe, error_msg = self.validate_code_safety(code)
        if not is_safe:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=error_msg,
                execution_time=0.0,
                exit_code=1,
                error_type="validation"
            )
        
        # Execute in subprocess for isolation
        try:
            process = subprocess.Popen(
                [sys.executable, '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=None,  # Don't inherit current working directory
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                # Try to get any output before timeout
                stdout, stderr = process.communicate()
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    success=False,
                    stdout=stdout[:self.max_output_length] if stdout else "",
                    stderr="Code execution timed out (taking too long to run)",
                    execution_time=execution_time,
                    exit_code=-1,
                    error_type="timeout"
                )
            
            execution_time = time.time() - start_time
            
            # Truncate output if too long
            if stdout and len(stdout) > self.max_output_length:
                stdout = stdout[:self.max_output_length] + "\n... (output truncated)"
            
            # Determine error type based on exit code and stderr content
            error_type = None
            if process.returncode != 0:
                if any(err in stderr.lower() for err in ['syntaxerror', 'invalid syntax']):
                    error_type = "syntax"
                else:
                    error_type = "runtime"
            
            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout.strip() if stdout else "",
                stderr=stderr.strip() if stderr else "",
                execution_time=execution_time,
                exit_code=process.returncode,
                error_type=error_type
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution failed: {str(e)}",
                execution_time=execution_time,
                exit_code=1,
                error_type="runtime"
            )
    
    def format_error_message(self, result: ExecutionResult) -> str:
        """Format error message in a user-friendly way for learning.
        
        Args:
            result: Execution result with error
            
        Returns:
            User-friendly error message
        """
        if result.error_type == "validation":
            return f"🚫 {result.stderr}"
        
        elif result.error_type == "syntax":
            if "invalid syntax" in result.stderr.lower():
                return "🚫 Syntax Error: Check for missing quotes, parentheses, or colons"
            elif "unexpected indent" in result.stderr.lower():
                return "🚫 Indentation Error: Make sure your indentation is consistent"
            else:
                return f"🚫 Syntax Error: {result.stderr}"
        
        elif result.error_type == "runtime":
            stderr_lower = result.stderr.lower()
            if "zerodivisionerror" in stderr_lower:
                return "🔢 Math Error: Can't divide by zero! Try a different number."
            elif "nameerror" in stderr_lower:
                return "🏷️ Name Error: Variable not defined. Check your spelling and make sure you assigned it first."
            elif "typeerror" in stderr_lower:
                return "🔀 Type Error: You might be mixing different data types (like numbers and text)."
            elif "indexerror" in stderr_lower:
                return "📋 Index Error: You're trying to access an item that doesn't exist in the list."
            else:
                return f"💥 Runtime Error: {result.stderr}"
        
        elif result.error_type == "timeout":
            return "⏱️ Timeout: Your code took too long to run. Check for infinite loops!"
        
        else:
            return f"🤖 Something unexpected happened: {result.stderr}"