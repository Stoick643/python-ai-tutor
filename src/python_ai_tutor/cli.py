"""Command Line Interface for the Python AI Tutor."""

import click
from typing import Optional

from .curriculum_engine import CurriculumEngine
from .models import ContentType


DEFAULT_USER_ID = "cli_user"


class LearningSession:
    """Handles the flow of a learning session for a topic."""
    
    def __init__(self, engine: CurriculumEngine, user_id: str):
        self.engine = engine
        self.user_id = user_id
    
    def run_topic_session(self, topic_id: str) -> None:
        """Run a complete learning session for a topic."""
        try:
            topic = self.engine.load_topic(topic_id)
        except FileNotFoundError:
            click.echo(f"❌ Topic '{topic_id}' not found.")
            return
        
        # Check prerequisites
        user_progress = self.engine.load_user_progress(self.user_id)
        if not self.engine.check_prerequisites(topic, user_progress):
            missing_prereqs = [p for p in topic.prerequisites 
                             if p not in user_progress.topics or 
                             not user_progress.topics[p].is_completed()]
            click.echo(f"❌ Prerequisites not met for '{topic_id}'")
            click.echo(f"   Complete these topics first: {', '.join(missing_prereqs)}")
            return
        
        # Display topic header
        click.echo(f"\n🎯 {topic.title}")
        click.echo(f"   Estimated time: {topic.estimated_time} minutes")
        click.echo(f"   Difficulty: {topic.difficulty}/5")
        click.echo("=" * 60)
        
        # Go through all 4 levels
        current_level = self.engine.calculate_starting_level(topic, user_progress)
        
        for level_num in range(4):
            level_key = str(level_num)
            if level_key not in topic.levels:
                continue
            
            level = topic.levels[level_key]
            self._display_content_level(level, level_num)
            
            # Update progress after each level
            self.engine.update_topic_progress(self.user_id, topic_id, level_num)
            
            # Pause between levels (except last)
            if level_num < 3:
                click.echo("\nPress Enter to continue...")
                input()
        
        # Show challenges if available
        if topic.challenges:
            click.echo("\n" + "=" * 60)
            click.echo("🏆 CHALLENGES")
            click.echo("=" * 60)
            
            for i, challenge in enumerate(topic.challenges, 1):
                click.echo(f"\nChallenge {i} (Difficulty: {challenge.difficulty}/5):")
                click.echo(f"📝 {challenge.prompt}")
                
                if challenge.hints:
                    click.echo(f"\n💡 Hints:")
                    for hint in challenge.hints:
                        click.echo(f"   • {hint}")
                
                click.echo(f"\n✅ Solution:")
                click.echo(f"```python")
                click.echo(challenge.solution)
                click.echo("```")
                
                if i < len(topic.challenges):
                    click.echo("\nPress Enter for next challenge...")
                    input()
        
        click.echo(f"\n🎉 Completed topic: {topic.title}!")
        
        # Mark topic as completed (level 3 is the highest)
        self.engine.update_topic_progress(self.user_id, topic_id, 3)
    
    def _display_content_level(self, level, level_num: int) -> None:
        """Display a single content level."""
        # Level type headers
        type_headers = {
            ContentType.CONCEPT: "📖 CONCEPT",
            ContentType.SIMPLE_EXAMPLE: "💡 SIMPLE EXAMPLE", 
            ContentType.MEDIUM_EXAMPLE: "🔧 MEDIUM EXAMPLE",
            ContentType.COMPLEX_EXAMPLE: "⚡ COMPLEX EXAMPLE"
        }
        
        header = type_headers.get(level.type, f"📋 LEVEL {level_num}")
        click.echo(f"\n{header}")
        click.echo("-" * 40)
        
        # Content
        click.echo(level.content)
        
        # Pseudocode for concept level
        if level.pseudocode:
            click.echo(f"\n📋 Structure:")
            click.echo(f"   {level.pseudocode}")
        
        # Code example
        if level.code:
            click.echo(f"\n```python")
            click.echo(level.code)
            click.echo("```")
        
        # Expected output
        if level.output:
            click.echo(f"\n📤 Output:")
            click.echo(level.output)
        
        # Explanation
        if level.explanation:
            click.echo(f"\n💭 Explanation:")
            click.echo(level.explanation)
        
        # Key concepts
        if level.key_concepts:
            click.echo(f"\n🔑 Key Concepts:")
            for concept in level.key_concepts:
                click.echo(f"   • {concept}")


@click.group()
@click.version_option()
def main():
    """Python AI Tutor - An intelligent, adaptive Python learning system."""
    pass


@main.command()
def list():
    """List all available topics."""
    engine = CurriculumEngine()
    topics = engine.get_available_topics()
    
    if not topics:
        click.echo("No topics found. Check your curriculum directory.")
        return
    
    click.echo("📚 Available Topics:")
    click.echo("=" * 40)
    
    # Load user progress to show completion status
    user_progress = engine.load_user_progress(DEFAULT_USER_ID)
    
    for topic_id in topics:
        try:
            topic = engine.load_topic(topic_id)
            
            # Check completion status
            if topic_id in user_progress.topics:
                topic_progress = user_progress.topics[topic_id]
                if topic_progress.is_completed():
                    status = "✅"
                elif topic_progress.current_level > 0:
                    status = "📖"
                else:
                    status = "⬜"
            else:
                status = "⬜"
            
            # Check if prerequisites are met
            can_access = engine.check_prerequisites(topic, user_progress)
            if not can_access:
                status = "🔒"
            
            click.echo(f"{status} {topic.title} ({topic_id})")
            
            if topic.prerequisites:
                click.echo(f"   Prerequisites: {', '.join(topic.prerequisites)}")
            
        except FileNotFoundError:
            click.echo(f"⚠️  {topic_id} (file not found)")
    
    click.echo("\nLegend: ✅ Completed | 📖 In Progress | ⬜ Available | 🔒 Locked")


@main.command()
@click.argument('topic_id')
def learn(topic_id: str):
    """Start learning a specific topic."""
    engine = CurriculumEngine()
    session = LearningSession(engine, DEFAULT_USER_ID)
    session.run_topic_session(topic_id)


@main.command()
def status():
    """Show your learning progress and statistics."""
    engine = CurriculumEngine()
    user_progress = engine.load_user_progress(DEFAULT_USER_ID)
    stats = engine.get_user_stats(DEFAULT_USER_ID)
    
    click.echo("📊 Your Learning Progress")
    click.echo("=" * 40)
    
    if stats["total_topics"] == 0:
        click.echo("No progress yet. Start with: python-tutor learn variables")
        return
    
    # Overall stats
    completion_rate = stats["completion_rate"]
    total_time_min = stats["total_time_seconds"] // 60
    
    click.echo(f"Topics completed: {stats['completed_topics']}/{stats['total_topics']}")
    click.echo(f"Overall progress: {completion_rate:.1f}%")
    click.echo(f"Time spent: {total_time_min} minutes")
    click.echo(f"Average level: {stats['avg_level']}")
    
    # Individual topic progress
    if user_progress.topics:
        click.echo(f"\n📋 Topic Details:")
        for topic_id, topic_progress in user_progress.topics.items():
            completion_pct = topic_progress.get_completion_percentage() * 100
            status_icon = "✅" if topic_progress.is_completed() else "📖"
            click.echo(f"   {status_icon} {topic_id}: {completion_pct:.0f}% (Level {topic_progress.current_level})")
    
    # Next available topics
    next_topics = engine.get_next_topics(user_progress)
    if next_topics:
        click.echo(f"\n🎯 Available Next:")
        for topic in next_topics[:3]:  # Show max 3
            click.echo(f"   • {topic.title} ({topic.id})")


@main.command()
@click.confirmation_option(prompt='Are you sure you want to reset all progress?')
def reset():
    """Reset all learning progress."""
    engine = CurriculumEngine()
    engine.reset_user_progress(DEFAULT_USER_ID)
    click.echo("✅ All progress has been reset.")


if __name__ == "__main__":
    main()