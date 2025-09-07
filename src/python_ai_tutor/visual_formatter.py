"""Rich console formatting for beautiful CLI learning experience."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
from rich.syntax import Syntax
from rich.text import Text
from rich.prompt import Prompt
from rich.theme import Theme

from .models import ContentType


class VisualFormatter:
    """Rich console formatter for educational content."""
    
    def __init__(self):
        """Initialize the visual formatter with custom theme."""
        # Define color theme for different content types
        custom_theme = Theme({
            "concept": "blue bold",
            "simple": "green",
            "medium": "yellow",
            "complex": "red bold",
            "success": "bold green",
            "warning": "bold yellow", 
            "error": "bold red",
            "question": "cyan bold",
            "code": "white on grey23",
            "output": "bright_green",
            "hint": "dim cyan"
        })
        
        self.console = Console(theme=custom_theme)
        
        # Content type styling
        self.content_styles = {
            ContentType.CONCEPT: {
                "icon": "📖",
                "title": "CONCEPT",
                "style": "concept",
                "border_style": "blue"
            },
            ContentType.SIMPLE_EXAMPLE: {
                "icon": "💡", 
                "title": "SIMPLE EXAMPLE",
                "style": "simple",
                "border_style": "green"
            },
            ContentType.MEDIUM_EXAMPLE: {
                "icon": "🔧",
                "title": "MEDIUM EXAMPLE", 
                "style": "medium",
                "border_style": "yellow"
            },
            ContentType.COMPLEX_EXAMPLE: {
                "icon": "⚡",
                "title": "COMPLEX EXAMPLE",
                "style": "complex", 
                "border_style": "red"
            }
        }
    
    def show_topic_header(self, title: str, estimated_time: int, difficulty: int, progress: float = 0.0):
        """Display the topic header with progress bar."""
        # Create progress bar
        progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
        
        header_text = f"""🎯 {title}
   Estimated time: {estimated_time} minutes | Difficulty: {"★" * difficulty}{"☆" * (5-difficulty)}"""
        
        if progress > 0:
            header_text += f"\n   Progress: [{progress_bar}] {progress*100:.0f}%"
        
        panel = Panel(
            header_text,
            title="Learning Session",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def show_content_level_header(self, content_type: ContentType, level_progress: float = 0.0):
        """Display header for a content level."""
        style_info = self.content_styles[content_type]
        
        header = f"{style_info['icon']} {style_info['title']}"
        if level_progress > 0:
            progress_bar = "█" * int(level_progress * 9) + "░" * (9 - int(level_progress * 9))
            header += f"                    [{progress_bar}] {level_progress*100:.0f}%"
        
        self.console.print()
        self.console.print(header, style=style_info['style'])
        self.console.print("─" * 60, style="dim")
    
    def show_content(self, content: str):
        """Display educational content with proper formatting."""
        self.console.print(content)
        self.console.print()
    
    def show_code(self, code: str, title: Optional[str] = None):
        """Display code with syntax highlighting."""
        if title:
            self.console.print(f"💻 {title}:", style="bold")
        
        # Create syntax highlighted code
        syntax = Syntax(
            code,
            "python",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
            background_color="default"
        )
        
        self.console.print(syntax)
        self.console.print()
    
    def show_output(self, output: str, title: str = "Output"):
        """Display code execution output."""
        self.console.print(f"📤 {title}:", style="bold")
        
        # Format output in a subtle panel
        output_panel = Panel(
            output,
            border_style="dim green",
            padding=(0, 1)
        )
        self.console.print(output_panel)
        self.console.print()
    
    def show_explanation(self, explanation: str):
        """Display explanation text."""
        self.console.print("💭 Explanation:", style="bold")
        self.console.print(explanation)
        self.console.print()
    
    def show_key_concepts(self, concepts: list[str]):
        """Display key concepts as a bulleted list."""
        if not concepts:
            return
            
        self.console.print("🔑 Key Concepts:", style="bold")
        for concept in concepts:
            self.console.print(f"   • {concept}")
        self.console.print()
    
    def show_pseudocode(self, pseudocode: str):
        """Display pseudocode structure."""
        self.console.print("📋 Structure:", style="bold")
        self.console.print(f"   {pseudocode}", style="dim italic")
        self.console.print()
    
    def ask_question(self, question: str, style: str = "question") -> str:
        """Display a question and get user input."""
        self.console.print()
        self.console.print(f"❓ {question}", style=style)
        
        # Use Rich prompt for better UX
        response = Prompt.ask("> ", console=self.console)
        return response
    
    def ask_code_input(self, prompt_text: str = "Enter your Python code") -> str:
        """Get multi-line code input from user."""
        self.console.print()
        self.console.print(f"📝 {prompt_text}")
        self.console.print("   [dim]Type your code below, press Enter after each line.[/dim]")
        self.console.print("   [dim]When finished, type 'END' on a new line and press Enter.[/dim]")
        self.console.print()
        
        lines = []
        while True:
            try:
                line = input("> ")
                if line.strip() == "END":
                    break
                lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break
        
        code = "\n".join(lines)
        
        # Show the code back to user with syntax highlighting
        if code.strip():
            self.console.print()
            self.console.print("🔍 Your code:", style="dim")
            self.show_code(code)
        
        return code
    
    def show_feedback(self, feedback: str, feedback_type: str = "neutral"):
        """Display feedback with appropriate styling."""
        if feedback_type == "positive":
            icon = "✅"
            style = "success"
        elif feedback_type == "confused":
            icon = "💡"
            style = "warning"
        elif feedback_type == "error":
            icon = "❌"
            style = "error"
        else:
            icon = "💬"
            style = "white"
        
        self.console.print(f"{icon} {feedback}", style=style)
        self.console.print()
    
    def show_hint(self, hint: str):
        """Display a hint in a subtle way."""
        self.console.print(f"💡 Hint: {hint}", style="hint")
        self.console.print()
    
    def show_challenge_header(self, challenge_num: int, total_challenges: int, difficulty: int):
        """Display challenge header."""
        self.console.print()
        self.console.print("=" * 60, style="bright_yellow")
        self.console.print("🏆 CHALLENGES", style="bright_yellow bold")
        self.console.print("=" * 60, style="bright_yellow")
        self.console.print()
        
        header = f"Challenge {challenge_num}/{total_challenges} (Difficulty: {'★' * difficulty}{'☆' * (5-difficulty)})"
        self.console.print(header, style="yellow bold")
    
    def show_challenge_prompt(self, prompt: str):
        """Display challenge prompt."""
        self.console.print(f"📝 {prompt}", style="bold")
        self.console.print()
    
    def show_hints(self, hints: list[str]):
        """Display hints for a challenge."""
        if not hints:
            return
            
        self.console.print("💡 Hints:", style="bold")
        for hint in hints:
            self.console.print(f"   • {hint}", style="hint")
        self.console.print()
    
    def show_solution(self, solution: str):
        """Display challenge solution."""
        self.console.print("✅ Solution:", style="success")
        self.show_code(solution)
    
    def show_completion_message(self, topic_title: str):
        """Display topic completion celebration."""
        message = f"🎉 Completed topic: {topic_title}!"
        
        panel = Panel(
            message,
            style="bright_green bold",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def show_progress_indicator(self, current: int, total: int, description: str = ""):
        """Show a simple progress indicator."""
        progress_text = f"[{current}/{total}]"
        if description:
            progress_text += f" {description}"
        
        self.console.print(progress_text, style="dim")
    
    def show_execution_status(self, status: str):
        """Show code execution status."""
        if status == "running":
            self.console.print("🔍 Running code...", style="dim")
        elif status == "success": 
            self.console.print("✅ Code executed successfully", style="success")
        elif status == "error":
            self.console.print("❌ Code execution failed", style="error")
    
    def wait_for_input(self, message: str = "Press Enter to continue..."):
        """Wait for user input to continue."""
        self.console.print()
        Prompt.ask(message, console=self.console, default="")
    
    def clear_screen(self):
        """Clear the screen (optional for better UX)."""
        import os
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/MacOS
            os.system('clear')
    
    def show_error_message(self, error: str, suggestions: list[str] = None):
        """Display error messages with suggestions."""
        panel = Panel(
            error,
            title="❌ Error",
            border_style="red",
            title_align="left"
        )
        self.console.print(panel)
        
        if suggestions:
            self.console.print("💡 Suggestions:", style="warning")
            for suggestion in suggestions:
                self.console.print(f"   • {suggestion}", style="dim")
        
        self.console.print()
    
    def show_typing_animation(self, text: str, delay: float = 0.03):
        """Show text with typing animation effect (optional)."""
        import time
        for char in text:
            self.console.print(char, end='')
            time.sleep(delay)
        self.console.print()  # New line at end