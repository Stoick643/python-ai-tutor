"""Enhanced CLI with interactive learning capabilities.

Enhanced CLI entry point that launches the rich interactive learning experience 
with visual formatting and real-time feedback using Rich library.
Provides the main learning interface with beautiful terminal UI and professional coding tools.
"""

import click
from typing import Optional

from .curriculum_engine import CurriculumEngine
from .interactive_session import InteractiveLearningSession
from .visual_formatter import VisualFormatter


DEFAULT_USER_ID = "cli_user"


@click.group()
@click.version_option()
def main():
    """Python AI Tutor - Interactive CLI with Socratic learning."""
    pass


@main.command()
def list():
    """List all available topics with beautiful formatting."""
    formatter = VisualFormatter()
    engine = CurriculumEngine()
    topics = engine.get_available_topics()
    
    if not topics:
        formatter.console.print("No topics found. Check your curriculum directory.", style="error")
        return
    
    formatter.console.print("[Books] Available Topics", style="bright_blue bold")
    formatter.console.print("=" * 40, style="dim")
    formatter.console.print()
    
    # Load user progress for status display
    user_progress = engine.load_user_progress(DEFAULT_USER_ID)
    
    for topic_id in topics:
        try:
            topic = engine.load_topic(topic_id)
            
            # Determine status icon and style
            if topic_id in user_progress.topics:
                topic_progress = user_progress.topics[topic_id]
                if topic_progress.is_completed():
                    status_icon = "✅"
                    status_style = "green"
                elif topic_progress.current_level > 0:
                    status_icon = "📖"
                    status_style = "yellow"
                else:
                    status_icon = "⬜"
                    status_style = "white"
            else:
                status_icon = "⬜"
                status_style = "white"
            
            # Check prerequisites
            if not engine.check_prerequisites(topic, user_progress):
                status_icon = "🔒"
                status_style = "red"
            
            # Display topic with rich formatting
            formatter.console.print(
                f"{status_icon} [bold]{topic.title}[/bold] ({topic_id})", 
                style=status_style
            )
            
            # Show additional info
            difficulty_stars = "★" * topic.difficulty + "☆" * (5 - topic.difficulty)
            formatter.console.print(
                f"   {difficulty_stars} | {topic.estimated_time} min", 
                style="dim"
            )
            
            if topic.prerequisites:
                formatter.console.print(
                    f"   Prerequisites: {', '.join(topic.prerequisites)}", 
                    style="dim cyan"
                )
            
            formatter.console.print()
            
        except FileNotFoundError:
            formatter.console.print(f"⚠️  {topic_id} (file not found)", style="error")
    
    formatter.console.print("Legend:", style="dim")
    formatter.console.print("✅ Completed | 📖 In Progress | ⬜ Available | 🔒 Locked", style="dim")


@main.command()
@click.argument('topic_id')
@click.option('--interactive/--basic', default=True, help="Run in interactive mode (default) or basic mode")
@click.option('--level', type=int, default=0, help="Starting level (0-3)")
def learn(topic_id: str, interactive: bool, level: int):
    """Start learning a specific topic with interactive features."""
    formatter = VisualFormatter()
    engine = CurriculumEngine()
    
    try:
        topic = engine.load_topic(topic_id)
    except FileNotFoundError:
        formatter.show_error_message(
            f"Topic '{topic_id}' not found.",
            ["Check available topics with: python-tutor list", "Make sure the topic ID is correct"]
        )
        return
    
    # Check prerequisites
    user_progress = engine.load_user_progress(DEFAULT_USER_ID)
    if not engine.check_prerequisites(topic, user_progress):
        missing_prereqs = [
            p for p in topic.prerequisites 
            if p not in user_progress.topics or not user_progress.topics[p].is_completed()
        ]
        formatter.show_error_message(
            f"Prerequisites not met for '{topic_id}'",
            [f"Complete these topics first: {', '.join(missing_prereqs)}"]
        )
        return
    
    # Start learning session
    if interactive:
        formatter.console.print("🚀 Starting Interactive Learning Session", style="bright_green bold")
        formatter.console.print("   Features: Live code execution, Socratic questioning, challenges", style="dim")
    else:
        formatter.console.print("📖 Starting Basic Learning Session", style="blue bold")
    
    formatter.console.print()
    
    # Run the session
    session = InteractiveLearningSession()
    try:
        topic_progress = session.run_topic_session(
            topic, 
            DEFAULT_USER_ID, 
            starting_level=level, 
            interactive=interactive
        )
        
        # Save progress
        engine.update_topic_progress(
            DEFAULT_USER_ID, 
            topic_id, 
            topic_progress.current_level
        )
        
        # Show session stats
        if interactive:
            stats = session.get_session_stats()
            formatter.console.print()
            formatter.console.print("📊 Session Summary:", style="bright_blue bold")
            formatter.console.print(f"   Time spent: {stats['total_time_seconds']:.1f} seconds", style="dim")
            formatter.console.print(f"   Interactions: {stats['interactions_count']}", style="dim")
            formatter.console.print(f"   Questions asked: {stats['questions_asked']}", style="dim")
            formatter.console.print(f"   Code executions: {stats['code_executed_count']}", style="dim")
            formatter.console.print(f"   Engagement score: {stats['engagement_score']:.1f}/1.0", style="dim")
        
    except KeyboardInterrupt:
        formatter.console.print("\n\n⏹️  Session interrupted by user", style="yellow")
        formatter.console.print("Your progress has been saved up to this point.", style="dim")
    except Exception as e:
        formatter.show_error_message(
            f"An error occurred during the learning session: {str(e)}",
            ["Please try again", "If the problem persists, check your curriculum files"]
        )


@main.command()
def status():
    """Show your learning progress with rich formatting."""
    formatter = VisualFormatter()
    engine = CurriculumEngine()
    
    user_progress = engine.load_user_progress(DEFAULT_USER_ID)
    stats = engine.get_user_stats(DEFAULT_USER_ID)
    
    formatter.console.print("📊 Your Learning Progress", style="bright_blue bold")
    formatter.console.print("=" * 40, style="dim")
    formatter.console.print()
    
    if stats["total_topics"] == 0:
        formatter.console.print("No progress yet. Start with:", style="dim")
        formatter.console.print("python-tutor learn variables", style="bright_green")
        return
    
    # Overall stats with rich formatting
    completion_rate = stats["completion_rate"]
    total_time_min = stats["total_time_seconds"] // 60
    
    # Progress bar for overall completion
    progress_bar = "█" * int(completion_rate / 10) + "░" * (10 - int(completion_rate / 10))
    
    formatter.console.print(f"📈 Overall Progress: [{progress_bar}] {completion_rate:.1f}%", style="bright_green")
    formatter.console.print(f"📚 Topics completed: {stats['completed_topics']}/{stats['total_topics']}", style="bright_blue")
    formatter.console.print(f"⏱️  Time spent: {total_time_min} minutes", style="bright_yellow")
    formatter.console.print(f"📊 Average level: {stats['avg_level']:.1f}/4.0", style="bright_magenta")
    formatter.console.print()
    
    # Individual topic progress
    if user_progress.topics:
        formatter.console.print("📋 Topic Details:", style="bright_cyan bold")
        formatter.console.print()
        
        for topic_id, topic_progress in user_progress.topics.items():
            completion_pct = topic_progress.get_completion_percentage() * 100
            
            if topic_progress.is_completed():
                status_icon = "✅"
                status_style = "green"
            elif topic_progress.current_level > 0:
                status_icon = "📖"
                status_style = "yellow"
            else:
                status_icon = "⬜"
                status_style = "white"
            
            # Mini progress bar
            mini_bar = "█" * int(completion_pct / 25) + "░" * (4 - int(completion_pct / 25))
            
            formatter.console.print(
                f"   {status_icon} [bold]{topic_id}[/bold]: [{mini_bar}] {completion_pct:.0f}% (Level {topic_progress.current_level})",
                style=status_style
            )
        
        formatter.console.print()
    
    # Available next topics
    next_topics = engine.get_next_topics(user_progress)
    if next_topics:
        formatter.console.print("🎯 Ready to Learn:", style="bright_green bold")
        for topic in next_topics[:3]:  # Show max 3
            formatter.console.print(f"   • {topic.title} ({topic.id})", style="green")
        
        if len(next_topics) > 3:
            formatter.console.print(f"   ... and {len(next_topics) - 3} more", style="dim")


@main.command()
@click.confirmation_option(prompt='Are you sure you want to reset all progress?')
def reset():
    """Reset all learning progress with confirmation."""
    formatter = VisualFormatter()
    engine = CurriculumEngine()
    engine.reset_user_progress(DEFAULT_USER_ID)
    formatter.console.print("✅ All progress has been reset.", style="success")


@main.command() 
def demo():
    """Run a quick demo of the interactive features."""
    formatter = VisualFormatter()
    
    formatter.console.print("🎨 Python AI Tutor - Interactive Features Demo", style="bright_blue bold")
    formatter.console.print("=" * 50, style="dim")
    formatter.console.print()
    
    # Demo visual formatting
    formatter.show_topic_header("Demo Topic", 15, 2, 0.4)
    
    # Demo code execution
    formatter.show_code('print("Hello from the interactive tutor!")')
    formatter.show_output("Hello from the interactive tutor!")
    
    # Demo question
    formatter.console.print("❓ This is how questions look in interactive mode", style="cyan bold")
    formatter.console.print("> [User would type response here]", style="dim")
    formatter.console.print()
    
    formatter.show_feedback("Great! This is positive feedback", "positive")
    formatter.show_hint("This is how hints appear")
    
    formatter.console.print("🚀 Try: [bold]python-tutor learn variables[/bold] for the full experience!", style="bright_green")


if __name__ == "__main__":
    main()