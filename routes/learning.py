"""Learning routes for Flask web application.

Main user-facing routes for the learning experience including dashboard,
lessons, and progress tracking. Integrates with existing curriculum engine.
"""

from flask import Blueprint, render_template, request, current_app, session, redirect, url_for, flash
import sys
sys.path.append('src')
from python_ai_tutor.models import ContentType

learning_bp = Blueprint('learning', __name__)


@learning_bp.route('/')
def index():
    """Render home page with available topics and call to action."""
    # Get total topics count for display
    topics = current_app.curriculum_engine.get_available_topics()
    return render_template('index.html', total_topics=len(topics))


@learning_bp.route('/dashboard')
def dashboard():
    """Display all topics with progress indicators by loading from CurriculumEngine."""
    from app import get_current_user
    
    user_id = get_current_user()
    
    # Get all available topics (returns list of topic IDs)
    topic_ids = current_app.curriculum_engine.get_available_topics()
    
    # Get user progress for each topic
    user_progress = current_app.curriculum_engine.load_user_progress(user_id)
    topics_with_progress = []
    
    for topic_id in topic_ids:
        try:
            topic_data = current_app.curriculum_engine.load_topic(topic_id)
            progress = user_progress.get_current_level(topic_id)
            completion_percentage = 0
            
            if topic_id in user_progress.topics:
                completion_percentage = user_progress.topics[topic_id].get_completion_percentage()
            
            topics_with_progress.append({
                'id': topic_id,
                'title': topic_data.title,
                'difficulty': topic_data.difficulty,
                'estimated_time': topic_data.estimated_time,
                'current_level': progress,
                'total_levels': len(topic_data.levels),
                'completion_percentage': completion_percentage * 100,
                'is_completed': completion_percentage >= 1.0
            })
        except Exception as e:
            print(f"Warning: Could not load topic {topic_id}: {e}")
            continue
    
    # Calculate overall stats
    completed_topics = len([t for t in topics_with_progress if t['is_completed']])
    
    return render_template('dashboard.html', 
                         topics=topics_with_progress,
                         completed_topics=completed_topics,
                         total_topics=len(topic_ids))


@learning_bp.route('/learn/<topic_id>')
def learn_topic(topic_id):
    """Load topic content from JSON and render lesson template with current level."""
    from app import get_current_user
    
    try:
        # Load the topic
        topic = current_app.curriculum_engine.load_topic(topic_id)
        if not topic:
            flash(f'Topic "{topic_id}" not found!', 'error')
            return redirect(url_for('learning.dashboard'))
        
        user_id = get_current_user()
        user_progress = current_app.curriculum_engine.load_user_progress(user_id)
        current_level = user_progress.get_current_level(topic_id)
        
        # Get current level content
        level_key = str(current_level)
        if level_key not in topic.levels:
            level_key = "0"  # Default to first level
        
        current_level_content = topic.levels[level_key]
        
        # Calculate progress for this topic
        completion_percentage = 0
        if topic_id in user_progress.topics:
            completion_percentage = user_progress.topics[topic_id].get_completion_percentage()
        
        # Prepare level navigation
        levels_info = []
        for level_num in range(len(topic.levels)):
            level_str = str(level_num)
            if level_str in topic.levels:
                level_info = topic.levels[level_str]
                levels_info.append({
                    'level': level_num,
                    'title': level_info.type.value.replace('_', ' ').title(),
                    'is_current': level_num == current_level,
                    'is_completed': level_num < current_level
                })
        
        return render_template('lesson.html',
                             topic=topic,
                             current_level=current_level,
                             current_level_content=current_level_content,
                             levels_info=levels_info,
                             completion_percentage=completion_percentage * 100)
    
    except Exception as e:
        flash(f'Error loading topic: {str(e)}', 'error')
        return redirect(url_for('learning.dashboard'))


@learning_bp.route('/execute', methods=['POST'])
def execute_code():
    """Accept POST request with code, call CodeExecutor, return JSON output."""
    from flask import jsonify
    
    try:
        code = request.json.get('code', '')
        if not code.strip():
            return jsonify({'success': False, 'error': 'No code provided'})
        
        # Execute the code
        result = current_app.code_executor.execute_code(code)
        
        return jsonify({
            'success': result.success,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'execution_time': result.execution_time,
            'has_output': result.has_output
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@learning_bp.route('/validate_challenge', methods=['POST'])
def validate_challenge():
    """Run challenge validation using existing InteractiveLearningSession logic."""
    from flask import jsonify
    from python_ai_tutor.interactive_session import InteractiveLearningSession
    
    try:
        data = request.json
        topic_id = data.get('topic_id')
        challenge_index = data.get('challenge_index', 0)
        user_code = data.get('code', '')
        
        if not user_code.strip():
            return jsonify({'success': False, 'message': 'No code provided'})
        
        # Load topic and challenge
        topic = current_app.curriculum_engine.load_topic(topic_id)
        if not topic or challenge_index >= len(topic.challenges):
            return jsonify({'success': False, 'message': 'Challenge not found'})
        
        challenge = topic.challenges[challenge_index]
        
        # Create session instance for validation
        session_instance = InteractiveLearningSession()
        is_valid, message = session_instance._validate_challenge_solution(user_code, challenge)
        
        return jsonify({
            'success': is_valid,
            'message': message
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Validation error: {str(e)}'})


@learning_bp.route('/update_progress', methods=['POST'])
def update_progress():
    """Save progress to database using existing ProgressPersistence methods."""
    from flask import jsonify
    from app import get_current_user
    
    try:
        data = request.json
        topic_id = data.get('topic_id')
        level = data.get('level', 0)
        
        user_id = get_current_user()
        
        # Update progress using curriculum engine
        current_app.curriculum_engine.update_topic_progress(
            user_id, topic_id, level, score=1.0  # Perfect score for completing level
        )
        
        return jsonify({'success': True, 'message': 'Progress saved'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to save progress: {str(e)}'})