"""Real code editor integration for professional coding experience.

External editor integration supporting VS Code, Notepad, nano, vim with cross-platform 
detection, temporary file management, and graceful fallbacks.
Prioritizes simple, fast editors for optimal learning flow over heavy IDEs.
"""

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict


class CodeEditorError(Exception):
    """Custom exception for code editor related errors."""
    pass


class CodeEditor:
    """Manages external code editor integration for student code input."""
    
    def __init__(self):
        """Initialize the code editor manager."""
        self.system = platform.system().lower()
        self.available_editors = []
        self.preferred_editor = None
        self._detect_editors()
    
    def _detect_editors(self) -> None:
        """Detect and rank available editors on the system."""
        self.available_editors = self.detect_available_editors()
        if self.available_editors:
            self.preferred_editor = self.available_editors[0]
    
    def detect_available_editors(self) -> List[Dict[str, str]]:
        """Scan system for installed editors and return prioritized list.
        
        Returns:
            List of editor dictionaries with 'name', 'path', 'args' keys
        """
        editors = []
        
        # Define editor preferences by platform - LEARNING-FIRST PRIORITY
        editor_configs = {
            'windows': [
                {'name': 'Notepad', 'command': 'notepad', 'args': [], 'priority': 1},  # Always available, instant
                {'name': 'Notepad++', 'command': 'notepad++', 'args': ['-multiInst'], 'priority': 2},  # Fast with syntax highlighting
                {'name': 'VS Code', 'command': 'code', 'args': ['--wait'], 'priority': 3},  # Professional option
                {'name': 'Sublime Text', 'command': 'subl', 'args': ['--wait'], 'priority': 4},  # Fallback
            ],
            'darwin': [  # macOS
                {'name': 'nano', 'command': 'nano', 'args': [], 'priority': 1},  # Simple, beginner-friendly
                {'name': 'VS Code', 'command': 'code', 'args': ['--wait'], 'priority': 2},  # Professional option
                {'name': 'vim', 'command': 'vim', 'args': [], 'priority': 3},  # Advanced users
                {'name': 'Sublime Text', 'command': 'subl', 'args': ['--wait'], 'priority': 4},  # Fallback
            ],
            'linux': [
                {'name': 'nano', 'command': 'nano', 'args': [], 'priority': 1},  # Simple, beginner-friendly
                {'name': 'VS Code', 'command': 'code', 'args': ['--wait'], 'priority': 2},  # Professional option
                {'name': 'vim', 'command': 'vim', 'args': [], 'priority': 3},  # Advanced users
                {'name': 'gedit', 'command': 'gedit', 'args': [], 'priority': 4},  # Simple GUI option
                {'name': 'Sublime Text', 'command': 'subl', 'args': ['--wait'], 'priority': 5},  # Fallback
            ]
        }
        
        # Get editors for current platform
        platform_editors = editor_configs.get(self.system, editor_configs['linux'])
        
        # Check which editors are actually available
        for editor_config in platform_editors:
            if self._is_command_available(editor_config['command']):
                editors.append({
                    'name': editor_config['name'],
                    'path': editor_config['command'],
                    'args': editor_config['args'],
                    'priority': editor_config['priority']
                })
        
        # Sort by priority (lower number = higher priority)
        return sorted(editors, key=lambda x: x['priority'])
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available in the system PATH."""
        return shutil.which(command) is not None
    
    def get_best_editor(self, preference_order: Optional[List[str]] = None) -> Optional[Dict[str, str]]:
        """Select the best available editor based on preferences.
        
        Args:
            preference_order: Optional list of preferred editor names
            
        Returns:
            Editor dictionary or None if no editors available
        """
        if not self.available_editors:
            return None
        
        if preference_order:
            # Try to find preferred editors first
            for preferred in preference_order:
                for editor in self.available_editors:
                    if editor['name'].lower() == preferred.lower():
                        return editor
        
        # Return highest priority editor
        return self.available_editors[0]
    
    def create_temp_code_file(self, initial_content: str = "") -> str:
        """Create temporary .py file with optional starter content.
        
        Args:
            initial_content: Optional code to pre-populate the file
            
        Returns:
            Path to the temporary file
        """
        # Create temp file with .py extension for syntax highlighting
        fd, temp_path = tempfile.mkstemp(suffix='.py', prefix='python_tutor_')
        
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as temp_file:
                if initial_content:
                    temp_file.write(initial_content)
                else:
                    # Add helpful comment for students
                    temp_file.write("# Enter your Python code here\n")
                    temp_file.write("# Save and close this file when you're done\n\n")
        except Exception as e:
            # Clean up on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise CodeEditorError(f"Failed to create temporary file: {e}")
        
        return temp_path
    
    def launch_editor_and_wait(self, editor_info: Dict[str, str], file_path: str) -> bool:
        """Launch specified editor with temp file and wait for completion.
        
        Args:
            editor_info: Dictionary with editor 'path', 'args'
            file_path: Path to file to edit
            
        Returns:
            True if editor launched and closed successfully
        """
        try:
            # Build command
            cmd = [editor_info['path']] + editor_info['args'] + [file_path]
            
            # On Windows, use shell=True for better command resolution
            use_shell = (self.system == 'windows')
            
            # Launch editor and wait for it to close
            result = subprocess.run(cmd, check=False, shell=use_shell)
            
            # Return True if editor exited normally (even with non-zero exit codes)
            return True
            
        except subprocess.SubprocessError as e:
            raise CodeEditorError(f"Failed to launch editor {editor_info['name']}: {e}")
        except Exception as e:
            raise CodeEditorError(f"Unexpected error launching editor: {e}")
    
    def read_and_validate_code(self, file_path: str) -> Tuple[str, bool]:
        """Read edited code from temp file and perform basic validation.
        
        Args:
            file_path: Path to the temporary file
            
        Returns:
            Tuple of (code_content, is_valid)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Remove our helper comments
            lines = code.split('\n')
            filtered_lines = []
            for line in lines:
                if not (line.strip().startswith('# Enter your Python code here') or
                       line.strip().startswith('# Save and close this file')):
                    filtered_lines.append(line)
            
            code = '\n'.join(filtered_lines).strip()
            
            # Basic validation - check if it's not empty
            is_valid = bool(code and not code.isspace())
            
            return code, is_valid
            
        except Exception as e:
            raise CodeEditorError(f"Failed to read code from file: {e}")
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Safely remove temporary file after code extraction.
        
        Args:
            file_path: Path to temporary file to remove
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            # Silently ignore cleanup errors - not critical
            pass
    
    def ask_code_with_editor(self, prompt: str, initial_code: str = "") -> str:
        """Main function to get code input using external editor.
        
        Args:
            prompt: Description of what code is needed
            initial_code: Optional code to pre-populate editor
            
        Returns:
            User's code as string
            
        Raises:
            CodeEditorError: If editor integration fails
        """
        # Check if we have any available editors
        if not self.available_editors:
            raise CodeEditorError("No suitable code editors found on system")
        
        editor = self.get_best_editor()
        if not editor:
            raise CodeEditorError("No suitable code editors available")
        
        # Create temporary file
        temp_path = self.create_temp_code_file(initial_code)
        
        try:
            print(f"\n📝 {prompt}")
            print(f"🚀 Opening {editor['name']} for code editing...")
            print("💾 Save and close the editor when you're finished.")
            
            # Launch editor
            success = self.launch_editor_and_wait(editor, temp_path)
            
            if not success:
                raise CodeEditorError(f"Editor {editor['name']} did not complete successfully")
            
            # Read the code back
            code, is_valid = self.read_and_validate_code(temp_path)
            
            if not is_valid:
                print("⚠️  No code found in editor. Please try again.")
                return ""
            
            return code
            
        finally:
            # Always clean up temp file
            self.cleanup_temp_file(temp_path)


# Global instance for easy access
_code_editor = CodeEditor()


def ask_code_with_editor(prompt: str, initial_code: str = "") -> str:
    """Convenience function to get code input using external editor.
    
    Args:
        prompt: Description of what code is needed
        initial_code: Optional code to pre-populate editor
        
    Returns:
        User's code as string
    """
    return _code_editor.ask_code_with_editor(prompt, initial_code)


def get_available_editors() -> List[str]:
    """Get list of available editor names.
    
    Returns:
        List of editor names available on system
    """
    return [editor['name'] for editor in _code_editor.available_editors]


def has_editor_support() -> bool:
    """Check if any code editors are available.
    
    Returns:
        True if at least one editor is available
    """
    return len(_code_editor.available_editors) > 0