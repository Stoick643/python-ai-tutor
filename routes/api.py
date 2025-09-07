"""API endpoints for Flask web application.

JSON API routes for AJAX interactions including code execution,
content loading, and progress tracking. Used by frontend JavaScript.
"""

from flask import Blueprint, jsonify, request, current_app
import sys
sys.path.append('src')

api_bp = Blueprint('api', __name__)


@api_bp.route('/topics')
def get_topics():
    """Return JSON list of all available topics from curriculum folder."""
    try:
        topic_ids = current_app.curriculum_engine.get_available_topics()
        
        # Format for frontend consumption
        topics_formatted = []
        for topic_id in topic_ids:
            try:
                topic_data = current_app.curriculum_engine.load_topic(topic_id)
                topics_formatted.append({
                    'id': topic_id,
                    'title': topic_data.title,
                    'difficulty': topic_data.difficulty,
                    'estimated_time': topic_data.estimated_time,
                    'prerequisites': topic_data.prerequisites
                })
            except Exception as e:
                print(f"Warning: Could not load topic {topic_id}: {e}")
                continue
        
        return jsonify({'topics': topics_formatted})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/topics/<topic_id>')
def get_topic_content(topic_id):
    """Return specific topic's JSON content for dynamic loading."""
    try:
        topic = current_app.curriculum_engine.load_topic(topic_id)
        
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
        
        # Convert to dictionary format
        topic_data = {
            'id': topic.id,
            'title': topic.title,
            'difficulty': topic.difficulty,
            'estimated_time': topic.estimated_time,
            'prerequisites': topic.prerequisites,
            'levels': {},
            'challenges': []
        }
        
        # Add levels
        for level_key, level_content in topic.levels.items():
            topic_data['levels'][level_key] = {
                'type': level_content.type.value,
                'content': level_content.content,
                'code': level_content.code,
                'output': level_content.output,
                'explanation': level_content.explanation,
                'key_concepts': level_content.key_concepts,
                'pseudocode': level_content.pseudocode
            }
        
        # Add challenges
        for challenge in topic.challenges:
            topic_data['challenges'].append({
                'prompt': challenge.prompt,
                'hints': challenge.hints,
                'difficulty': challenge.difficulty,
                'validation_type': challenge.validation_type
            })
        
        return jsonify({'topic': topic_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/execute', methods=['POST'])
def run_code():
    """Execute Python code safely and return stdout/stderr as JSON."""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code.strip():
            return jsonify({
                'success': False,
                'error': 'No code provided',
                'stdout': '',
                'stderr': ''
            })
        
        # Execute the code using our existing executor
        result = current_app.code_executor.execute_code(code)
        
        response_data = {
            'success': result.success,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'execution_time': result.execution_time,
            'has_output': result.has_output,
            'exit_code': result.exit_code
        }
        
        # Add error type if execution failed
        if not result.success:
            response_data['error_type'] = result.error_type
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Execution failed: {str(e)}',
            'stdout': '',
            'stderr': str(e)
        }), 500


@api_bp.route('/progress')
def get_progress():
    """Get user's progress data for all topics."""
    from app import get_current_user
    
    try:
        user_id = get_current_user()
        user_progress = current_app.curriculum_engine.load_user_progress(user_id)
        
        # Format progress data
        progress_data = {
            'user_id': user_progress.user_id,
            'topics': {},
            'global_stats': user_progress.global_stats
        }
        
        for topic_id, topic_progress in user_progress.topics.items():
            progress_data['topics'][topic_id] = {
                'current_level': topic_progress.current_level,
                'completed_levels': topic_progress.completed_levels,
                'performance_scores': topic_progress.performance_scores,
                'completion_percentage': topic_progress.get_completion_percentage(),
                'is_completed': topic_progress.is_completed(),
                'total_time_spent': topic_progress.total_time_spent,
                'last_accessed': topic_progress.last_accessed
            }
        
        return jsonify({'progress': progress_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/progress/<topic_id>', methods=['POST'])
def update_topic_progress(topic_id):
    """Update progress for a specific topic."""
    from app import get_current_user
    
    try:
        data = request.get_json()
        user_id = get_current_user()
        
        level = data.get('level', 0)
        score = data.get('score', 1.0)
        time_spent = data.get('time_spent', 0)
        
        # Update progress using curriculum engine
        current_app.curriculum_engine.update_topic_progress(
            user_id, topic_id, level, score, time_spent
        )
        
        # Get updated progress to return
        user_progress = current_app.curriculum_engine.load_user_progress(user_id)
        topic_progress = user_progress.topics.get(topic_id)
        
        if topic_progress:
            return jsonify({
                'success': True,
                'progress': {
                    'current_level': topic_progress.current_level,
                    'completion_percentage': topic_progress.get_completion_percentage(),
                    'is_completed': topic_progress.is_completed()
                }
            })
        else:
            return jsonify({'success': True, 'message': 'Progress updated'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/stats')
def get_user_stats():
    """Get overall user statistics."""
    from app import get_current_user
    
    try:
        user_id = get_current_user()
        stats = current_app.curriculum_engine.get_user_stats(user_id)
        
        return jsonify({'stats': stats})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500