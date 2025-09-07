"""Flask web application for Python AI Tutor.

Simple Flask web interface that wraps existing CLI code with HTTP endpoints.
Provides browser-based learning experience while reusing all existing Python logic.
"""

import os
from flask import Flask, session
from pathlib import Path

# Import our existing code
import sys
sys.path.append('src')
from python_ai_tutor.curriculum_engine import CurriculumEngine
from python_ai_tutor.progress_persistence import ProgressPersistence
from python_ai_tutor.code_executor import CodeExecutor


def create_app():
    """Initialize Flask app with configurations, register blueprints, and set up database path."""
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Configure paths
    app.config['CURRICULUM_PATH'] = Path('curriculum')
    app.config['DATABASE_PATH'] = Path('user_data/progress.db')
    
    # Ensure user_data directory exists
    app.config['DATABASE_PATH'].parent.mkdir(exist_ok=True)
    
    # Initialize our components
    init_curriculum_engine(app)
    
    # Register blueprints
    from routes.learning import learning_bp
    from routes.api import api_bp
    
    app.register_blueprint(learning_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app


def init_curriculum_engine(app):
    """Create singleton instance of CurriculumEngine for reuse across requests."""
    # Create curriculum engine instance with content and database paths
    content_path = str(app.config['CURRICULUM_PATH'])
    db_path = str(app.config['DATABASE_PATH'])
    
    app.curriculum_engine = CurriculumEngine(content_path, db_path)
    app.code_executor = CodeExecutor()


def get_current_user():
    """Helper to get user from session or create default web_user for simplicity."""
    # For MVP, use simple session-based user identification
    if 'user_id' not in session:
        session['user_id'] = 'web_user'  # Default user for single-user setup
    return session['user_id']


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)