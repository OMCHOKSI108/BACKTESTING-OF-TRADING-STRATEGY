from flask import Blueprint, request, jsonify
from app.services.ai_agent_service import AIAgentService
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__)
ai_service = AIAgentService()

@ai_bp.route('/research', methods=['POST'])
def perform_research():
    """Perform automated financial market research"""
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query parameter is required'
            }), 400

        query = data['query']
        max_results = data.get('max_results', 5)

        logger.info(f"Performing AI research for query: {query}")

        result = ai_service.research_financial_markets(query, max_results)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error in research endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/history', methods=['GET'])
def get_research_history():
    """Get research history"""
    try:
        history = ai_service.get_research_history()
        return jsonify({
            'success': True,
            'history': history
        }), 200

    except Exception as e:
        logger.error(f"Error getting research history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/health', methods=['GET'])
def health_check():
    """AI service health check"""
    return jsonify({
        'success': True,
        'service': 'ai_agent',
        'status': 'healthy',
        'capabilities': [
            'financial_research',
            'market_analysis',
            'web_data_gathering',
            'ai_powered_insights'
        ]
    }), 200