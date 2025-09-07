"""Tests for code editor integration functionality."""

import os
import tempfile
import unittest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

from src.python_ai_tutor.code_editor import (
    CodeEditor, 
    CodeEditorError, 
    ask_code_with_editor, 
    get_available_editors,
    has_editor_support
)


class TestCodeEditor(unittest.TestCase):
    """Test cases for CodeEditor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.editor = CodeEditor()

    def test_init_detects_system(self):
        """Test that CodeEditor initializes and detects system."""
        self.assertIn(self.editor.system, ['windows', 'darwin', 'linux'])
        self.assertIsInstance(self.editor.available_editors, list)

    @patch('shutil.which')
    def test_detect_available_editors_windows(self, mock_which):
        """Test editor detection on Windows."""
        # Mock Notepad and VS Code available
        def mock_which_windows(cmd):
            if cmd == 'notepad':
                return 'C:\\Windows\\System32\\notepad.exe'
            elif cmd == 'code':
                return 'C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd'
            return None
        
        mock_which.side_effect = mock_which_windows
        
        # Create new editor instance to trigger detection
        with patch('platform.system', return_value='Windows'):
            editor = CodeEditor()
            
        self.assertTrue(len(editor.available_editors) >= 2)
        self.assertEqual(editor.available_editors[0]['name'], 'Notepad')  # Should be first priority
        self.assertEqual(editor.available_editors[0]['path'], 'notepad')

    @patch('shutil.which')
    def test_detect_available_editors_macos(self, mock_which):
        """Test editor detection on macOS."""
        # Mock multiple editors available
        def mock_which_macos(cmd):
            if cmd == 'nano':
                return '/usr/bin/nano'
            elif cmd == 'code':
                return '/usr/local/bin/code'
            return None
        
        mock_which.side_effect = mock_which_macos
        
        with patch('platform.system', return_value='Darwin'):
            editor = CodeEditor()
            
        self.assertTrue(len(editor.available_editors) >= 2)
        # Should be sorted by priority - nano first, then VS Code
        self.assertEqual(editor.available_editors[0]['name'], 'nano')
        self.assertEqual(editor.available_editors[1]['name'], 'VS Code')

    @patch('shutil.which')
    def test_detect_available_editors_linux(self, mock_which):
        """Test editor detection on Linux."""
        # Mock nano and VS Code available
        def mock_which_linux(cmd):
            if cmd == 'nano':
                return '/bin/nano'
            elif cmd == 'code':
                return '/usr/bin/code'
            return None
        
        mock_which.side_effect = mock_which_linux
        
        with patch('platform.system', return_value='Linux'):
            editor = CodeEditor()
            
        self.assertTrue(len(editor.available_editors) >= 2)
        # Should be sorted by priority - nano first, then VS Code
        self.assertEqual(editor.available_editors[0]['name'], 'nano')
        self.assertEqual(editor.available_editors[1]['name'], 'VS Code')

    @patch('shutil.which', return_value=None)
    def test_no_editors_available(self, mock_which):
        """Test behavior when no editors are available."""
        editor = CodeEditor()
        self.assertEqual(len(editor.available_editors), 0)
        self.assertIsNone(editor.preferred_editor)

    def test_get_best_editor_with_preference(self):
        """Test getting best editor with preferences."""
        # Mock available editors (already sorted by priority in real implementation)
        self.editor.available_editors = [
            {'name': 'VS Code', 'priority': 1},  # First in list (highest priority)
            {'name': 'nano', 'priority': 3},
            {'name': 'vim', 'priority': 4}
        ]
        
        # Test with preference
        result = self.editor.get_best_editor(['vim', 'nano'])
        self.assertEqual(result['name'], 'vim')
        
        # Test with no preference (should return first editor in list)
        result = self.editor.get_best_editor()
        self.assertEqual(result['name'], 'VS Code')

    def test_get_best_editor_no_editors(self):
        """Test get_best_editor when no editors available."""
        self.editor.available_editors = []
        result = self.editor.get_best_editor()
        self.assertIsNone(result)

    def test_create_temp_code_file_with_content(self):
        """Test creating temporary file with initial content."""
        initial_code = "print('Hello, World!')\n"
        temp_path = self.editor.create_temp_code_file(initial_code)
        
        try:
            self.assertTrue(os.path.exists(temp_path))
            self.assertTrue(temp_path.endswith('.py'))
            self.assertIn('python_tutor_', temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertEqual(content, initial_code)
        finally:
            self.editor.cleanup_temp_file(temp_path)

    def test_create_temp_code_file_empty(self):
        """Test creating temporary file without initial content."""
        temp_path = self.editor.create_temp_code_file()
        
        try:
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn('# Enter your Python code here', content)
            self.assertIn('# Save and close this file', content)
        finally:
            self.editor.cleanup_temp_file(temp_path)

    def test_create_temp_file_error_handling(self):
        """Test error handling in temp file creation."""
        # Mock os.fdopen to raise an exception after tempfile.mkstemp succeeds
        with patch('os.fdopen', side_effect=OSError("Permission denied")):
            with self.assertRaises(CodeEditorError) as context:
                self.editor.create_temp_code_file()
            
            self.assertIn("Failed to create temporary file", str(context.exception))

    @patch('subprocess.run')
    def test_launch_editor_success(self, mock_run):
        """Test successful editor launch."""
        mock_run.return_value = Mock(returncode=0)
        
        editor_info = {
            'name': 'VS Code',
            'path': 'code',
            'args': ['--wait']
        }
        
        result = self.editor.launch_editor_and_wait(editor_info, '/tmp/test.py')
        self.assertTrue(result)
        
        # Verify subprocess was called with correct arguments (including shell=True on Windows)
        expected_shell = (self.editor.system == 'windows')
        mock_run.assert_called_once_with(['code', '--wait', '/tmp/test.py'], check=False, shell=expected_shell)

    @patch('subprocess.run')
    def test_launch_editor_subprocess_error(self, mock_run):
        """Test editor launch with subprocess error."""
        mock_run.side_effect = Exception("Command failed")
        
        editor_info = {
            'name': 'VS Code',
            'path': 'code',
            'args': ['--wait']
        }
        
        with self.assertRaises(CodeEditorError) as context:
            self.editor.launch_editor_and_wait(editor_info, '/tmp/test.py')
        
        self.assertIn("Unexpected error launching editor", str(context.exception))

    def test_read_and_validate_code_success(self):
        """Test reading and validating code from file."""
        # Create temporary file with test code
        test_code = "x = 10\ny = 20\nprint(x + y)"
        temp_path = self.editor.create_temp_code_file(test_code)
        
        try:
            code, is_valid = self.editor.read_and_validate_code(temp_path)
            self.assertEqual(code, test_code)
            self.assertTrue(is_valid)
        finally:
            self.editor.cleanup_temp_file(temp_path)

    def test_read_and_validate_code_with_helper_comments(self):
        """Test reading code and filtering helper comments."""
        # Create file with helper comments
        content = """# Enter your Python code here
# Save and close this file when you're done

x = 10
print(x)"""
        
        temp_path = self.editor.create_temp_code_file(content)
        
        try:
            code, is_valid = self.editor.read_and_validate_code(temp_path)
            self.assertEqual(code, "x = 10\nprint(x)")
            self.assertTrue(is_valid)
        finally:
            self.editor.cleanup_temp_file(temp_path)

    def test_read_and_validate_code_empty(self):
        """Test reading empty file."""
        temp_path = self.editor.create_temp_code_file("")
        
        try:
            code, is_valid = self.editor.read_and_validate_code(temp_path)
            self.assertEqual(code, "")
            self.assertFalse(is_valid)
        finally:
            self.editor.cleanup_temp_file(temp_path)

    def test_read_and_validate_code_file_error(self):
        """Test error handling when reading non-existent file."""
        with self.assertRaises(CodeEditorError) as context:
            self.editor.read_and_validate_code('/nonexistent/file.py')
        
        self.assertIn("Failed to read code from file", str(context.exception))

    def test_cleanup_temp_file_success(self):
        """Test successful temp file cleanup."""
        temp_path = self.editor.create_temp_code_file("test")
        self.assertTrue(os.path.exists(temp_path))
        
        self.editor.cleanup_temp_file(temp_path)
        self.assertFalse(os.path.exists(temp_path))

    def test_cleanup_temp_file_nonexistent(self):
        """Test cleanup of non-existent file (should not raise error)."""
        # Should not raise any exception
        self.editor.cleanup_temp_file('/nonexistent/file.py')

    @patch.object(CodeEditor, 'get_best_editor')
    @patch.object(CodeEditor, 'create_temp_code_file')
    @patch.object(CodeEditor, 'launch_editor_and_wait')
    @patch.object(CodeEditor, 'read_and_validate_code')
    @patch.object(CodeEditor, 'cleanup_temp_file')
    def test_ask_code_with_editor_success(self, mock_cleanup, mock_read, mock_launch, mock_create, mock_get_editor):
        """Test complete ask_code_with_editor workflow."""
        # Mock all the dependencies
        mock_get_editor.return_value = {'name': 'VS Code', 'path': 'code', 'args': ['--wait']}
        mock_create.return_value = '/tmp/test.py'
        mock_launch.return_value = True
        mock_read.return_value = ('print("Hello!")', True)
        
        self.editor.available_editors = [{'name': 'VS Code'}]
        
        result = self.editor.ask_code_with_editor("Write a greeting", "# Initial code")
        
        self.assertEqual(result, 'print("Hello!")')
        mock_create.assert_called_once_with("# Initial code")
        mock_launch.assert_called_once()
        mock_read.assert_called_once()
        mock_cleanup.assert_called_once()

    def test_ask_code_with_editor_no_editors(self):
        """Test ask_code_with_editor when no editors available."""
        self.editor.available_editors = []
        
        with self.assertRaises(CodeEditorError) as context:
            self.editor.ask_code_with_editor("Write code")
        
        self.assertIn("No suitable code editors found", str(context.exception))

    @patch.object(CodeEditor, 'read_and_validate_code')
    @patch.object(CodeEditor, 'launch_editor_and_wait')
    @patch.object(CodeEditor, 'create_temp_code_file')
    @patch.object(CodeEditor, 'get_best_editor')
    def test_ask_code_with_editor_invalid_code(self, mock_get_editor, mock_create, mock_launch, mock_read):
        """Test ask_code_with_editor when user provides no code."""
        mock_get_editor.return_value = {'name': 'VS Code', 'path': 'code', 'args': ['--wait']}
        mock_create.return_value = '/tmp/test.py'
        mock_launch.return_value = True
        mock_read.return_value = ('', False)  # Empty code
        
        self.editor.available_editors = [{'name': 'VS Code'}]
        
        with patch('builtins.print') as mock_print:
            result = self.editor.ask_code_with_editor("Write code")
        
        self.assertEqual(result, "")
        mock_print.assert_called_with("⚠️  No code found in editor. Please try again.")


class TestModuleFunctions(unittest.TestCase):
    """Test module-level convenience functions."""

    @patch('src.python_ai_tutor.code_editor._code_editor')
    def test_ask_code_with_editor_function(self, mock_editor_instance):
        """Test the module-level ask_code_with_editor function."""
        mock_editor_instance.ask_code_with_editor.return_value = "test code"
        
        result = ask_code_with_editor("Test prompt", "initial")
        
        self.assertEqual(result, "test code")
        mock_editor_instance.ask_code_with_editor.assert_called_once_with("Test prompt", "initial")

    @patch('src.python_ai_tutor.code_editor._code_editor')
    def test_get_available_editors_function(self, mock_editor_instance):
        """Test the get_available_editors function."""
        mock_editor_instance.available_editors = [
            {'name': 'VS Code'}, 
            {'name': 'nano'}
        ]
        
        result = get_available_editors()
        
        self.assertEqual(result, ['VS Code', 'nano'])

    @patch('src.python_ai_tutor.code_editor._code_editor')
    def test_has_editor_support_function(self, mock_editor_instance):
        """Test the has_editor_support function."""
        mock_editor_instance.available_editors = [{'name': 'VS Code'}]
        self.assertTrue(has_editor_support())
        
        mock_editor_instance.available_editors = []
        self.assertFalse(has_editor_support())


if __name__ == '__main__':
    unittest.main()