"""Data models for the Python AI Tutor system.

This module defines the core data structures (Topic, Challenge, UserProgress, ContentLevel) 
using dataclasses to represent curriculum content and track student progress with type safety.
Provides a clean, type-hinted interface for all educational content and progress tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContentType(str, Enum):
    """Types of learning content levels."""

    CONCEPT = "concept"
    SIMPLE_EXAMPLE = "simple_example"
    MEDIUM_EXAMPLE = "medium_example"
    COMPLEX_EXAMPLE = "complex_example"


@dataclass
class ContentLevel:
    """Represents one level of learning content for a topic."""

    type: ContentType
    content: str
    code: str | None = None
    output: str | None = None
    explanation: str | None = None
    key_concepts: list[str] = field(default_factory=list)
    pseudocode: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContentLevel:
        """Create ContentLevel from dictionary data."""
        return cls(
            type=ContentType(data["type"]),
            content=data["content"],
            code=data.get("code"),
            output=data.get("output"),
            explanation=data.get("explanation"),
            key_concepts=data.get("key_concepts", []),
            pseudocode=data.get("pseudocode"),
        )


@dataclass
class Challenge:
    """Represents a coding challenge for a topic."""

    prompt: str
    solution: str
    test_cases: list[dict[str, Any]] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    difficulty: int = 1
    validation_type: str = "exact_match"  # exact_match, code_structure, pattern_match, custom
    requirements: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Challenge:
        """Create Challenge from dictionary data."""
        return cls(
            prompt=data["prompt"],
            solution=data["solution"],
            test_cases=data.get("test_cases", []),
            hints=data.get("hints", []),
            difficulty=data.get("difficulty", 1),
            validation_type=data.get("validation_type", "exact_match"),
            requirements=data.get("requirements", {}),
        )


@dataclass
class Topic:
    """Represents a complete learning topic with all its content."""

    id: str
    title: str
    prerequisites: list[str] = field(default_factory=list)
    difficulty: int = 1
    estimated_time: int = 30  # minutes
    levels: dict[str, ContentLevel] = field(default_factory=dict)
    challenges: list[Challenge] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Topic:
        """Create Topic from dictionary data (typically loaded from JSON)."""
        levels = {
            k: ContentLevel.from_dict(v) for k, v in data.get("levels", {}).items()
        }
        challenges = [Challenge.from_dict(c) for c in data.get("challenges", [])]

        return cls(
            id=data["topic_id"],
            title=data["title"],
            prerequisites=data.get("prerequisites", []),
            difficulty=data.get("difficulty", 1),
            estimated_time=data.get("estimated_time", 30),
            levels=levels,
            challenges=challenges,
        )


@dataclass
class UserProgress:
    """Tracks a user's progress through the curriculum."""

    user_id: str
    topics: dict[str, TopicProgress] = field(default_factory=dict)
    learning_path: str | None = None
    global_stats: dict[str, Any] = field(default_factory=dict)

    def get_current_level(self, topic_id: str) -> int:
        """Get the current level for a topic (0-3)."""
        if topic_id not in self.topics:
            return 0
        return self.topics[topic_id].current_level

    def get_completed_topics(self) -> list[str]:
        """Get list of fully completed topic IDs."""
        return [
            topic_id
            for topic_id, progress in self.topics.items()
            if progress.is_completed()
        ]


@dataclass
class TopicProgress:
    """Progress data for a specific topic."""

    topic_id: str
    current_level: int = 0
    completed_levels: list[int] = field(default_factory=list)
    performance_scores: list[float] = field(default_factory=list)
    last_accessed: str | None = None
    total_time_spent: int = 0  # seconds
    challenge_attempts: dict[str, Any] = field(default_factory=dict)

    def is_completed(self) -> bool:
        """Check if this topic is fully completed (all 4 levels)."""
        return (
            len(self.completed_levels) >= 4
            and max(self.completed_levels, default=-1) >= 3
        )

    def get_completion_percentage(self) -> float:
        """Get completion percentage (0.0 to 1.0)."""
        if not self.completed_levels:
            return 0.0
        return len(self.completed_levels) / 4.0
