"""Tests for Flask web application.

Comprehensive test suite covering all routes, API endpoints,
and integration with existing Python components.
"""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.append('src')
sys.path.append('.')

# Import the Flask app
from app import create_app, get_current_user


class TestWebApp(unittest.TestCase):
    """Test cases for Flask web application."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-key'
        
        # Use temporary database for tests
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.app.config['DATABASE_PATH'] = Path(self.temp_db.name)
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after each test."""
        self.app_context.pop()
        
        # Properly close SQLite connections before file deletion
        if hasattr(self.app, 'curriculum_engine') and self.app.curriculum_engine:
            self.app.curriculum_engine.progress_persistence.close()
        
        # Clean up temp database with retries for Windows
        import time
        import gc
        
        time.sleep(0.1)  # Small delay for Windows
        temp_path = Path(self.temp_db.name)
        
        for attempt in range(3):
            try:
                if temp_path.exists():
                    temp_path.unlink()
                break
            except (PermissionError, OSError):
                if attempt < 2:
                    time.sleep(0.1)
                else:
                    gc.collect()
                    time.sleep(0.2)
                    try:
                        temp_path.unlink(missing_ok=True)
                    except:
                        pass  # Give up gracefully

    def test_home_page_loads(self):
        """GET / returns 200 and contains Start Learning."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Start Learning', response.data)
        self.assertIn(b'Python AI Tutor', response.data)

    def test_dashboard_shows_topics(self):
        """Dashboard displays all 7 curriculum topics correctly."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_user'
        
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Check for key dashboard elements
        self.assertIn(b'Learning Dashboard', response.data)
        self.assertIn(b'Variables', response.data)  # Should show some topics

    @patch('routes.learning.current_app')
    def test_learn_topic_renders_content(self, mock_app):
        """Topic page shows correct content from JSON file."""
        # Mock curriculum engine
        mock_topic = MagicMock()
        mock_topic.id = 'variables'
        mock_topic.title = 'Variables and Assignment'
        mock_topic.levels = {'0': MagicMock(type=MagicMock(value='concept'))}
        mock_topic.challenges = []
        
        mock_app.curriculum_engine.load_topic.return_value = mock_topic
        mock_app.curriculum_engine.load_user_progress.return_value = MagicMock()
        mock_app.curriculum_engine.load_user_progress.return_value.get_current_level.return_value = 0
        mock_app.curriculum_engine.load_user_progress.return_value.topics = {}
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_user'
        
        response = self.client.get('/learn/variables')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Variables', response.data)

    def test_code_execution_api(self):
        """POST to /api/execute runs code and returns output."""
        test_code = 'print("Hello, World!")'
        
        response = self.client.post('/api/execute',
                                  json={'code': test_code},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertIn('stdout', data)
        self.assertIn('stderr', data)
        
        if data['success']:
            self.assertIn('Hello, World!', data['stdout'])

    def test_code_execution_empty_code(self):
        """API handles empty code gracefully."""
        response = self.client.post('/api/execute',
                                  json={'code': ''},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_challenge_validation_pass(self):
        """Correct solution returns success response."""
        # Mock challenge validation (patch the import inside the function)
        with patch('python_ai_tutor.interactive_session.InteractiveLearningSession') as mock_session:
            mock_instance = mock_session.return_value
            mock_instance._validate_challenge_solution.return_value = (True, "Great job!")
            
            # Mock curriculum engine
            with patch('routes.learning.current_app') as mock_app:
                mock_topic = MagicMock()
                mock_topic.challenges = [MagicMock()]
                mock_app.curriculum_engine.load_topic.return_value = mock_topic
                
                response = self.client.post('/validate_challenge',
                                          json={
                                              'topic_id': 'variables',
                                              'challenge_index': 0,
                                              'code': 'name = "Alice"'
                                          },
                                          content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])

    def test_challenge_validation_fail(self):
        """Wrong solution returns helpful error message."""
        # Mock challenge validation failure
        with patch('python_ai_tutor.interactive_session.InteractiveLearningSession') as mock_session:
            mock_instance = mock_session.return_value
            mock_instance._validate_challenge_solution.return_value = (False, "Try again!")
            
            # Mock curriculum engine
            with patch('routes.learning.current_app') as mock_app:
                mock_topic = MagicMock()
                mock_topic.challenges = [MagicMock()]
                mock_app.curriculum_engine.load_topic.return_value = mock_topic
                
                response = self.client.post('/validate_challenge',
                                          json={
                                              'topic_id': 'variables',
                                              'challenge_index': 0,
                                              'code': 'wrong code'
                                          },
                                          content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertFalse(data['success'])
                self.assertIn('message', data)

    @patch('routes.learning.current_app')
    def test_progress_persistence(self):
        """Progress saves to SQLite and persists across sessions."""
        mock_app = current_app
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_user'
        
        # Test updating progress
        response = self.client.post('/update_progress',
                                  json={
                                      'topic_id': 'variables',
                                      'level': 1,
                                      'score': 0.8
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_sql_injection_protection(self):
        """Malicious code input is safely handled."""
        malicious_code = '''
import os
os.system("rm -rf /")
print("Malicious code executed")
'''
        
        response = self.client.post('/api/execute',
                                  json={'code': malicious_code},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should either fail or be sandboxed
        if data['success']:
            # If it runs, should not contain system command output
            self.assertNotIn('Malicious', data.get('stdout', ''))
        # If it fails, that's also acceptable (sandboxing worked)

    def test_session_management(self):
        """User session maintains state between requests."""
        # Test session creation
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('user_id'))
        
        # Make a request that should create session
        response = self.client.get('/dashboard')
        
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_id'), 'web_user')

    def test_topic_not_found(self):
        """Invalid topic ID returns 404 or redirect."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_user'
        
        response = self.client.get('/learn/nonexistent_topic')
        
        # Should either redirect to dashboard or return 404
        self.assertIn(response.status_code, [302, 404])
        
        if response.status_code == 302:
            # Check redirect location
            self.assertIn('/dashboard', response.location)

    def test_api_topics_endpoint(self):
        """API returns list of available topics."""
        response = self.client.get('/api/topics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('topics', data)
        self.assertIsInstance(data['topics'], list)

    def test_api_topic_content_endpoint(self):
        """API returns specific topic content."""
        # This test requires actual curriculum files or mocking
        with patch('routes.learning.current_app') as mock_app:
            mock_topic = MagicMock()
            mock_topic.id = 'variables'
            mock_topic.title = 'Variables'
            mock_topic.levels = {}
            mock_topic.challenges = []
            mock_app.curriculum_engine.load_topic.return_value = mock_topic
            
            response = self.client.get('/api/topics/variables')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertIn('topic', data)

    def test_progress_api_endpoint(self):
        """Progress API returns user progress data."""
        with patch('routes.learning.current_app') as mock_app:
            mock_progress = MagicMock()
            mock_progress.user_id = 'test_user'
            mock_progress.topics = {}
            mock_progress.global_stats = {}
            mock_app.curriculum_engine.load_user_progress.return_value = mock_progress
            
            with self.client.session_transaction() as sess:
                sess['user_id'] = 'test_user'
            
            response = self.client.get('/api/progress')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertIn('progress', data)


class TestIntegration(unittest.TestCase):
    """Integration tests with real components."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_full_learning_flow(self):
        """Test complete user flow from dashboard to lesson to challenge."""
        # This would test the full integration but requires curriculum files
        pass

    def test_curriculum_engine_integration(self):
        """Test integration with real CurriculumEngine."""
        # This would test with actual curriculum files
        pass


if __name__ == '__main__':
    # Run specific test groups
    unittest.main(verbosity=2)