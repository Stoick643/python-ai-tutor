"""Integration tests for curriculum engine with real files."""

from python_ai_tutor.curriculum_engine import CurriculumEngine
from python_ai_tutor.models import UserProgress


class TestCurriculumIntegration:
    """Test curriculum engine with real curriculum files."""

    def test_load_variables_topic(self):
        """Should load the variables topic from JSON file."""
        engine = CurriculumEngine(content_path="curriculum/")

        # Load the variables topic
        topic = engine.load_topic("variables")

        # Verify topic loaded correctly
        assert topic.id == "variables"
        assert topic.title == "Variables and Assignment"
        assert len(topic.levels) == 4
        assert len(topic.challenges) == 2

        # Check level content
        assert "Variables store values" in topic.levels["0"].content
        assert topic.levels["1"].code is not None
        assert "age = 25" in topic.levels["1"].code

    def test_new_user_can_access_variables(self):
        """Should allow new user to access variables topic (no prerequisites)."""
        engine = CurriculumEngine(content_path="curriculum/")
        user_progress = UserProgress(user_id="new_user")

        # Check that variables topic is available
        next_topics = engine.get_next_topics(user_progress)
        topic_ids = [t.id for t in next_topics]

        assert "variables" in topic_ids

    def test_start_learning_session_variables(self):
        """Should create a learning session for variables topic."""
        engine = CurriculumEngine(content_path="curriculum/")
        user_progress = UserProgress(user_id="test_user")

        # Load topic and start session
        topic = engine.load_topic("variables")
        session = engine.start_learning_session(topic, user_progress, "test_user")

        # Verify session structure
        assert session["topic"].id == "variables"
        assert session["level"] == 0  # Should start at concept level
        assert session["user_id"] == "test_user"
        assert "start_time" in session
