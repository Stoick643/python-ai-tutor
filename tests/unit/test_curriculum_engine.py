"""Test-driven development tests for CurriculumEngine."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from python_ai_tutor.curriculum_engine import ContentLoader, CurriculumEngine
from python_ai_tutor.models import ContentLevel, ContentType, Topic, UserProgress


class TestContentLoader:
    """Test the ContentLoader class."""

    def test_load_topic_from_valid_json(self):
        """Should load a topic from valid JSON file."""
        # Arrange: Create a temporary JSON file with topic data
        topic_data = {
            "topic_id": "variables",
            "title": "Variables and Assignment",
            "prerequisites": [],
            "difficulty": 1,
            "estimated_time": 20,
            "levels": {
                "0": {
                    "type": "concept",
                    "content": "Variables store values for later use",
                    "pseudocode": "variable_name = value",
                },
                "1": {
                    "type": "simple_example",
                    "content": "Basic variable assignment",
                    "code": "age = 25\nprint(age)",
                    "output": "25",
                    "explanation": "Assigns 25 to variable age and prints it",
                },
            },
            "challenges": [
                {
                    "prompt": "Create a variable called 'name' with your name",
                    "solution": "name = 'Alice'",
                    "hints": ["Use quotes for strings"],
                    "difficulty": 1,
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(topic_data, f)
            temp_path = f.name

        # Act: Load the topic
        loader = ContentLoader(Path(temp_path).parent)
        topic = loader.load_topic(Path(temp_path).stem)

        # Assert: Verify topic was loaded correctly
        assert topic.id == "variables"
        assert topic.title == "Variables and Assignment"
        assert topic.difficulty == 1
        assert len(topic.levels) == 2
        assert topic.levels["0"].type == ContentType.CONCEPT
        assert topic.levels["1"].code == "age = 25\nprint(age)"
        assert len(topic.challenges) == 1
        assert (
            topic.challenges[0].prompt
            == "Create a variable called 'name' with your name"
        )

        # Cleanup
        Path(temp_path).unlink()

    def test_load_topic_file_not_found(self):
        """Should raise FileNotFoundError for non-existent topic."""
        loader = ContentLoader(Path("/tmp"))

        with pytest.raises(FileNotFoundError):
            loader.load_topic("nonexistent_topic")

    def test_get_available_topics(self):
        """Should return list of available topic IDs."""
        # Arrange: Create temporary directory with topic files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some topic files
            (temp_path / "variables.json").touch()
            (temp_path / "functions.json").touch()
            (temp_path / "loops.json").touch()
            (temp_path / "not_a_topic.txt").touch()  # Should be ignored

            # Act
            loader = ContentLoader(temp_path)
            topics = loader.get_available_topics()

            # Assert
            assert set(topics) == {"variables", "functions", "loops"}
            assert "not_a_topic" not in topics


class TestCurriculumEngine:
    """Test the CurriculumEngine class using TDD."""

    def test_initialization(self):
        """Should initialize with content and progress paths."""
        engine = CurriculumEngine(
            content_path="curriculum/", progress_path="user_data/"
        )

        assert engine.content_path == Path("curriculum/")
        assert engine.progress_path == Path("user_data/")
        assert engine.content_loader is not None

    def test_load_topic_success(self):
        """Should load a topic successfully."""
        # Arrange: Mock the content loader
        mock_loader = Mock()
        mock_topic = Topic(
            id="variables",
            title="Variables",
            levels={"0": ContentLevel(ContentType.CONCEPT, "Variables store data")},
        )
        mock_loader.load_topic.return_value = mock_topic

        engine = CurriculumEngine()
        engine.content_loader = mock_loader

        # Act
        topic = engine.load_topic("variables")

        # Assert
        assert topic == mock_topic
        mock_loader.load_topic.assert_called_once_with("variables")

    def test_get_available_topics(self):
        """Should return available topics from content loader."""
        # Arrange
        mock_loader = Mock()
        mock_loader.get_available_topics.return_value = [
            "variables",
            "functions",
            "loops",
        ]

        engine = CurriculumEngine()
        engine.content_loader = mock_loader

        # Act
        topics = engine.get_available_topics()

        # Assert
        assert topics == ["variables", "functions", "loops"]
        mock_loader.get_available_topics.assert_called_once()

    def test_check_prerequisites_all_met(self):
        """Should return True when all prerequisites are completed."""
        # Arrange: User has completed required topics
        user_progress = UserProgress(user_id="test_user")
        user_progress.topics = {
            "variables": Mock(is_completed=Mock(return_value=True)),
            "conditionals": Mock(is_completed=Mock(return_value=True)),
        }

        topic = Topic(
            id="loops", title="Loops", prerequisites=["variables", "conditionals"]
        )

        engine = CurriculumEngine()

        # Act
        can_access = engine.check_prerequisites(topic, user_progress)

        # Assert
        assert can_access is True

    def test_check_prerequisites_not_met(self):
        """Should return False when prerequisites are not completed."""
        # Arrange: User missing required topics
        user_progress = UserProgress(user_id="test_user")
        user_progress.topics = {
            "variables": Mock(is_completed=Mock(return_value=True)),
            # "conditionals" is missing
        }

        topic = Topic(
            id="loops", title="Loops", prerequisites=["variables", "conditionals"]
        )

        engine = CurriculumEngine()

        # Act
        can_access = engine.check_prerequisites(topic, user_progress)

        # Assert
        assert can_access is False

    def test_get_next_topics_respects_prerequisites(self):
        """Should only return topics whose prerequisites are met."""
        # Arrange: Mock available topics and user progress
        mock_loader = Mock()
        mock_loader.get_available_topics.return_value = [
            "variables",
            "conditionals",
            "loops",
            "functions",
        ]

        # Mock topics with different prerequisites
        topics_data = {
            "variables": Topic(id="variables", title="Variables", prerequisites=[]),
            "conditionals": Topic(
                id="conditionals", title="Conditionals", prerequisites=["variables"]
            ),
            "loops": Topic(
                id="loops", title="Loops", prerequisites=["variables", "conditionals"]
            ),
            "functions": Topic(
                id="functions", title="Functions", prerequisites=["loops"]
            ),
        }
        mock_loader.load_topic.side_effect = lambda topic_id: topics_data[topic_id]

        # User has completed variables only
        user_progress = UserProgress(user_id="test_user")
        user_progress.topics = {"variables": Mock(is_completed=Mock(return_value=True))}

        engine = CurriculumEngine()
        engine.content_loader = mock_loader

        # Act
        next_topics = engine.get_next_topics(user_progress)

        # Assert: Should only return conditionals (prerequisites met)
        assert len(next_topics) == 1
        assert next_topics[0].id == "conditionals"

    def test_calculate_starting_level_new_topic(self):
        """Should return 0 for topics not yet started."""
        user_progress = UserProgress(user_id="test_user")
        topic = Topic(id="variables", title="Variables")

        engine = CurriculumEngine()
        level = engine.calculate_starting_level(topic, user_progress)

        assert level == 0

    def test_calculate_starting_level_in_progress(self):
        """Should return current level for topics in progress."""
        user_progress = UserProgress(user_id="test_user")
        user_progress.topics = {"variables": Mock(current_level=2)}
        topic = Topic(id="variables", title="Variables")

        engine = CurriculumEngine()
        level = engine.calculate_starting_level(topic, user_progress)

        assert level == 2

    def test_start_learning_session_creates_session(self):
        """Should create a learning session with proper initialization."""
        # Arrange
        mock_topic = Topic(
            id="variables",
            title="Variables",
            levels={"0": ContentLevel(ContentType.CONCEPT, "Variables store data")},
        )

        user_progress = UserProgress(user_id="test_user")

        engine = CurriculumEngine()

        # Act
        session = engine.start_learning_session(mock_topic, user_progress, "test_user")

        # Assert
        assert session["topic"] == mock_topic
        assert session["level"] == 0  # Should start at level 0 for new topic
        assert session["user_id"] == "test_user"
        assert "start_time" in session
        assert session["interactions"] == []
