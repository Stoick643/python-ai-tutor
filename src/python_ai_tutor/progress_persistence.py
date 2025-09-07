"""SQLite-based progress persistence for the Python AI Tutor."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import TopicProgress, UserProgress


class ProgressPersistence:
    """Handles SQLite-based storage and retrieval of user progress."""
    
    def __init__(self, db_path: str = "user_data/progress.db"):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    learning_path TEXT,
                    global_stats TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id TEXT,
                    topic_id TEXT,
                    current_level INTEGER DEFAULT 0,
                    completed_levels TEXT,
                    performance_scores TEXT,
                    last_accessed TIMESTAMP,
                    total_time_spent INTEGER DEFAULT 0,
                    challenge_attempts TEXT,
                    PRIMARY KEY (user_id, topic_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
    
    def save_user_progress(self, user_progress: UserProgress) -> None:
        """Save complete user progress to database."""
        with sqlite3.connect(self.db_path) as conn:
            # Insert or update user record
            conn.execute("""
                INSERT OR REPLACE INTO users (id, learning_path, global_stats)
                VALUES (?, ?, ?)
            """, (
                user_progress.user_id,
                user_progress.learning_path,
                json.dumps(user_progress.global_stats)
            ))
            
            # Insert or update topic progress
            for topic_id, topic_progress in user_progress.topics.items():
                conn.execute("""
                    INSERT OR REPLACE INTO user_progress 
                    (user_id, topic_id, current_level, completed_levels, 
                     performance_scores, last_accessed, total_time_spent, challenge_attempts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_progress.user_id,
                    topic_id,
                    topic_progress.current_level,
                    json.dumps(topic_progress.completed_levels),
                    json.dumps(topic_progress.performance_scores),
                    topic_progress.last_accessed,
                    topic_progress.total_time_spent,
                    json.dumps(topic_progress.challenge_attempts)
                ))
            
            conn.commit()
    
    def load_user_progress(self, user_id: str) -> UserProgress:
        """Load user progress from database."""
        with sqlite3.connect(self.db_path) as conn:
            # Load user data
            user_row = conn.execute("""
                SELECT learning_path, global_stats FROM users WHERE id = ?
            """, (user_id,)).fetchone()
            
            if user_row:
                learning_path, global_stats = user_row
                global_stats = json.loads(global_stats) if global_stats else {}
            else:
                learning_path = None
                global_stats = {}
            
            # Load topic progress
            topic_rows = conn.execute("""
                SELECT topic_id, current_level, completed_levels, performance_scores,
                       last_accessed, total_time_spent, challenge_attempts
                FROM user_progress WHERE user_id = ?
            """, (user_id,)).fetchall()
            
            topics = {}
            for row in topic_rows:
                topic_id, current_level, completed_levels, performance_scores, \
                last_accessed, total_time_spent, challenge_attempts = row
                
                topics[topic_id] = TopicProgress(
                    topic_id=topic_id,
                    current_level=current_level,
                    completed_levels=json.loads(completed_levels) if completed_levels else [],
                    performance_scores=json.loads(performance_scores) if performance_scores else [],
                    last_accessed=last_accessed,
                    total_time_spent=total_time_spent,
                    challenge_attempts=json.loads(challenge_attempts) if challenge_attempts else {}
                )
            
            return UserProgress(
                user_id=user_id,
                topics=topics,
                learning_path=learning_path,
                global_stats=global_stats
            )
    
    def update_topic_progress(self, user_id: str, topic_id: str, topic_progress: TopicProgress) -> None:
        """Update progress for a specific topic."""
        # Set last accessed to current time
        topic_progress.last_accessed = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Ensure user exists
            conn.execute("""
                INSERT OR IGNORE INTO users (id) VALUES (?)
            """, (user_id,))
            
            # Update topic progress
            conn.execute("""
                INSERT OR REPLACE INTO user_progress 
                (user_id, topic_id, current_level, completed_levels, 
                 performance_scores, last_accessed, total_time_spent, challenge_attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                topic_id,
                topic_progress.current_level,
                json.dumps(topic_progress.completed_levels),
                json.dumps(topic_progress.performance_scores),
                topic_progress.last_accessed,
                topic_progress.total_time_spent,
                json.dumps(topic_progress.challenge_attempts)
            ))
            
            conn.commit()
    
    def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Get summary statistics for a user."""
        with sqlite3.connect(self.db_path) as conn:
            # Get basic completion stats
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_topics,
                    SUM(CASE WHEN current_level >= 3 THEN 1 ELSE 0 END) as completed_topics,
                    AVG(current_level) as avg_level,
                    SUM(total_time_spent) as total_time
                FROM user_progress 
                WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            total_topics, completed_topics, avg_level, total_time = stats
            
            return {
                "total_topics": total_topics or 0,
                "completed_topics": completed_topics or 0,
                "avg_level": round(avg_level or 0, 2),
                "total_time_seconds": total_time or 0,
                "completion_rate": (completed_topics / total_topics * 100) if total_topics > 0 else 0
            }
    
    def reset_user_progress(self, user_id: str) -> None:
        """Reset all progress for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM user_progress WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()