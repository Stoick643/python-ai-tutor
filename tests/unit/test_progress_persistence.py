"""Tests for SQLite-based progress persistence."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from python_ai_tutor.models import TopicProgress, UserProgress
from python_ai_tutor.progress_persistence import ProgressPersistence


class TestProgressPersistence:
    """Test the ProgressPersistence class."""
    
    def setup_method(self):
        """Set up test database for each test."""
        # Use temporary database for each test
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.persistence = ProgressPersistence(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up test database after each test."""
        Path(self.temp_db.name).unlink(missing_ok=True)
    
    def test_database_initialization(self):
        """Should create database tables on initialization."""
        # Database should exist and be accessible
        assert Path(self.temp_db.name).exists()
        
        # Should be able to create a new persistence instance with same DB
        persistence2 = ProgressPersistence(self.temp_db.name)
        assert persistence2 is not None
    
    def test_save_and_load_user_progress(self):
        """Should save and load user progress correctly."""
        # Arrange: Create test user progress
        topic_progress = TopicProgress(
            topic_id="variables",
            current_level=2,
            completed_levels=[0, 1, 2],
            performance_scores=[0.8, 0.9, 0.7],
            total_time_spent=300
        )
        
        user_progress = UserProgress(
            user_id="test_user",
            topics={"variables": topic_progress},
            learning_path="web_dev",
            global_stats={"streak": 5}
        )
        
        # Act: Save and load
        self.persistence.save_user_progress(user_progress)
        loaded_progress = self.persistence.load_user_progress("test_user")
        
        # Assert: Data should match
        assert loaded_progress.user_id == "test_user"
        assert loaded_progress.learning_path == "web_dev"
        assert loaded_progress.global_stats == {"streak": 5}
        assert "variables" in loaded_progress.topics
        
        loaded_topic = loaded_progress.topics["variables"]
        assert loaded_topic.topic_id == "variables"
        assert loaded_topic.current_level == 2
        assert loaded_topic.completed_levels == [0, 1, 2]
        assert loaded_topic.performance_scores == [0.8, 0.9, 0.7]
        assert loaded_topic.total_time_spent == 300
    
    def test_load_nonexistent_user(self):
        """Should return empty progress for nonexistent user."""
        progress = self.persistence.load_user_progress("nonexistent")
        
        assert progress.user_id == "nonexistent"
        assert progress.learning_path is None
        assert progress.global_stats == {}
        assert progress.topics == {}
    
    def test_update_topic_progress(self):
        """Should update progress for a specific topic."""
        # Arrange: Create topic progress
        topic_progress = TopicProgress(
            topic_id="variables",
            current_level=1,
            completed_levels=[0, 1],
            performance_scores=[0.8, 0.9]
        )
        
        # Act: Update topic progress
        self.persistence.update_topic_progress("test_user", "variables", topic_progress)
        
        # Load and verify
        user_progress = self.persistence.load_user_progress("test_user")
        loaded_topic = user_progress.topics["variables"]
        
        # Assert: Topic should be updated
        assert loaded_topic.topic_id == "variables"
        assert loaded_topic.current_level == 1
        assert loaded_topic.completed_levels == [0, 1]
        assert loaded_topic.last_accessed is not None
    
    def test_get_user_stats(self):
        """Should calculate user statistics correctly."""
        # Arrange: Create user with multiple topics
        topic1 = TopicProgress(
            topic_id="variables",
            current_level=3,
            completed_levels=[0, 1, 2, 3],
            total_time_spent=300
        )
        topic2 = TopicProgress(
            topic_id="functions",
            current_level=2,
            completed_levels=[0, 1, 2],
            total_time_spent=450
        )
        
        user_progress = UserProgress(
            user_id="test_user",
            topics={"variables": topic1, "functions": topic2}
        )
        
        self.persistence.save_user_progress(user_progress)
        
        # Act: Get stats
        stats = self.persistence.get_user_stats("test_user")
        
        # Assert: Stats should be calculated correctly
        assert stats["total_topics"] == 2
        assert stats["completed_topics"] == 1  # Only variables is fully completed (level 3)
        assert stats["avg_level"] == 2.5  # (3 + 2) / 2
        assert stats["total_time_seconds"] == 750  # 300 + 450
        assert stats["completion_rate"] == 50.0  # 1/2 * 100
    
    def test_reset_user_progress(self):
        """Should reset all progress for a user."""
        # Arrange: Create user with progress
        topic_progress = TopicProgress(
            topic_id="variables",
            current_level=2,
            completed_levels=[0, 1, 2]
        )
        
        user_progress = UserProgress(
            user_id="test_user",
            topics={"variables": topic_progress}
        )
        
        self.persistence.save_user_progress(user_progress)
        
        # Verify user has progress
        loaded = self.persistence.load_user_progress("test_user")
        assert len(loaded.topics) == 1
        
        # Act: Reset progress
        self.persistence.reset_user_progress("test_user")
        
        # Assert: Progress should be cleared
        reset_progress = self.persistence.load_user_progress("test_user")
        assert len(reset_progress.topics) == 0
        assert reset_progress.learning_path is None
        assert reset_progress.global_stats == {}
    
    def test_multiple_users(self):
        """Should handle multiple users independently."""
        # Arrange: Create two users with different progress
        user1_progress = UserProgress(
            user_id="user1",
            topics={"variables": TopicProgress(topic_id="variables", current_level=1)}
        )
        user2_progress = UserProgress(
            user_id="user2", 
            topics={"functions": TopicProgress(topic_id="functions", current_level=2)}
        )
        
        # Act: Save both users
        self.persistence.save_user_progress(user1_progress)
        self.persistence.save_user_progress(user2_progress)
        
        # Assert: Each user should have independent progress
        loaded_user1 = self.persistence.load_user_progress("user1")
        loaded_user2 = self.persistence.load_user_progress("user2")
        
        assert "variables" in loaded_user1.topics
        assert "functions" not in loaded_user1.topics
        
        assert "functions" in loaded_user2.topics
        assert "variables" not in loaded_user2.topics