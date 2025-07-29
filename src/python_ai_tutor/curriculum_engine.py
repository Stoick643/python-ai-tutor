"""Core curriculum engine for managing learning content and user progress."""

import json
import time
from pathlib import Path
from typing import Any

from .models import Topic, UserProgress


class ContentLoader:
    """Loads curriculum content from JSON files."""

    def __init__(self, content_path: Path):
        """Initialize with path to content directory."""
        self.content_path = Path(content_path)

    def load_topic(self, topic_id: str) -> Topic:
        """Load a topic from JSON file."""
        topic_file = self.content_path / f"{topic_id}.json"

        if not topic_file.exists():
            raise FileNotFoundError(f"Topic file not found: {topic_file}")

        with open(topic_file, encoding="utf-8") as f:
            topic_data = json.load(f)

        return Topic.from_dict(topic_data)

    def get_available_topics(self) -> list[str]:
        """Get list of available topic IDs."""
        if not self.content_path.exists():
            return []

        return [f.stem for f in self.content_path.glob("*.json") if f.is_file()]


class CurriculumEngine:
    """Core engine for managing curriculum and learning sessions."""

    def __init__(
        self, content_path: str = "curriculum/", progress_path: str = "user_data/"
    ):
        """Initialize the curriculum engine."""
        self.content_path = Path(content_path)
        self.progress_path = Path(progress_path)
        self.content_loader = ContentLoader(self.content_path)

    def load_topic(self, topic_id: str) -> Topic:
        """Load a specific topic."""
        return self.content_loader.load_topic(topic_id)

    def get_available_topics(self) -> list[str]:
        """Get list of all available topics."""
        return self.content_loader.get_available_topics()

    def check_prerequisites(self, topic: Topic, user_progress: UserProgress) -> bool:
        """Check if user has completed all prerequisites for a topic."""
        if not topic.prerequisites:
            return True

        for prereq in topic.prerequisites:
            if prereq not in user_progress.topics:
                return False
            if not user_progress.topics[prereq].is_completed():
                return False

        return True

    def get_next_topics(self, user_progress: UserProgress) -> list[Topic]:
        """Get list of topics user can access based on completed prerequisites."""
        available_topics = self.get_available_topics()
        next_topics = []

        for topic_id in available_topics:
            # Skip if already completed
            if (
                topic_id in user_progress.topics
                and user_progress.topics[topic_id].is_completed()
            ):
                continue

            topic = self.load_topic(topic_id)
            if self.check_prerequisites(topic, user_progress):
                next_topics.append(topic)

        return next_topics

    def calculate_starting_level(
        self, topic: Topic, user_progress: UserProgress
    ) -> int:
        """Calculate which level to start at for a topic."""
        if topic.id not in user_progress.topics:
            return 0

        return user_progress.topics[topic.id].current_level

    def start_learning_session(
        self, topic: Topic, user_progress: UserProgress, user_id: str
    ) -> dict[str, Any]:
        """Start a new learning session for a topic."""
        starting_level = self.calculate_starting_level(topic, user_progress)

        session = {
            "topic": topic,
            "level": starting_level,
            "user_id": user_id,
            "start_time": time.time(),
            "interactions": [],
        }

        return session
