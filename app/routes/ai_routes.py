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


@ai_bp.route('/search_and_cite', methods=['POST'])
def search_and_cite_route():
    """Search and cite orchestration endpoint.

    Accepts JSON: {query, start_date (opt), end_date (opt), sources (opt list), max_results (opt)}
    """
    try:
        data = request.get_json() or {}
        query = data.get('query')
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400

        start_date = data.get('start_date')
        end_date = data.get('end_date')
        sources = data.get('sources', ['web', 'news'])
        max_results = int(data.get('max_results', 10))
        use_llm = bool(data.get('use_llm', False))

        logger.info(f"search_and_cite request for query: {query}")
        res = ai_service.search_and_cite(query, start_date=start_date, end_date=end_date, sources=sources, max_results=max_results, use_llm=use_llm)

        if res.get('success'):
            return jsonify(res), 200
        else:
            return jsonify(res), 500

    except Exception as e:
        logger.error(f"Error in search_and_cite endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/resummarize', methods=['POST'])
def resummarize_route():
    """Re-summarize using only selected sources provided by the client."""
    try:
        data = request.get_json() or {}
        sources = data.get('sources')
        query = data.get('query')
        use_llm = bool(data.get('use_llm', False))

        if not sources or not isinstance(sources, list):
            return jsonify({'success': False, 'error': 'sources (list) is required'}), 400

        res = ai_service.resummarize_sources(sources, query=query, use_llm=use_llm)
        if res.get('success'):
            return jsonify(res), 200
        else:
            return jsonify(res), 500

    except Exception as e:
        logger.error(f"Error in resummarize endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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