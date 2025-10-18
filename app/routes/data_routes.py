from flask import Blueprint, request, jsonify, render_template
from app.services.data_service import DataService
import logging

logger = logging.getLogger(__name__)

data_bp = Blueprint("data", __name__, url_prefix="/api/data")

data_service = DataService()

@data_bp.route("/", methods=["GET"])
def data_info():
    """Data API information"""
    return jsonify({
        "module": "Data Service API",
        "description": "Handles market data gathering and management",
        "endpoints": {
            "POST /api/data/gather": "Gather market data",
            "GET /api/data/status": "Check data availability",
            "GET /api/data/preview": "Preview available data"
        },
        "supported_markets": ["US Stocks", "Indian Stocks", "Forex"],
        "supported_timeframes": ["1m", "5m", "15m", "30m", "45m", "1h", "4h", "1d", "1w", "1mo"],
        "status": "active"
    })

@data_bp.route("/gather", methods=["POST"])
def gather_data():
    """API endpoint to gather market data"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        market_type = data.get('market_type', 'US Stocks')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        timeframe = data.get('timeframe', '1d')

        if not all([symbol, start_date, end_date]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: symbol, start_date, end_date'
            }), 400

        logger.info(f"Gathering data for {symbol} ({market_type}) from {start_date} to {end_date}")

        # Gather data
        df = data_service.gather_data(symbol, market_type, start_date, end_date, timeframe)

        if df.empty:
            return jsonify({
                'success': False,
                'error': 'No data could be retrieved'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Successfully gathered {len(df)} candles for {symbol}',
            'data_points': len(df),
            'timeframe': timeframe,
            'market_type': market_type
        })

    except Exception as e:
        logger.error(f"Error in gather_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@data_bp.route("/status", methods=["GET"])
def data_status():
    """Check data availability for a symbol"""
    try:
        symbol = request.args.get('symbol')
        timeframe = request.args.get('timeframe', '1d')

        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol parameter required'
            }), 400

        # Check if processed data exists
        df = data_service.load_processed_data(symbol, timeframe)

        if df.empty:
            return jsonify({
                'success': True,
                'available': False,
                'message': f'No processed data available for {symbol}'
            })
        else:
            return jsonify({
                'success': True,
                'available': True,
                'data_points': len(df),
                'last_updated': df['timestamp'].max() if 'timestamp' in df.columns else 'Unknown',
                'timeframe': timeframe
            })

    except Exception as e:
        logger.error(f"Error in data_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@data_bp.route("/preview", methods=["GET"])
def data_preview():
    """Get preview of available data for a symbol"""
    try:
        symbol = request.args.get('symbol')
        timeframe = request.args.get('timeframe', '1d')
        limit = int(request.args.get('limit', 10))

        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol parameter required'
            }), 400

        df = data_service.load_processed_data(symbol, timeframe)

        if df.empty:
            return jsonify({
                'success': False,
                'error': f'No data available for {symbol}'
            }), 404

        # Get last N records
        preview_data = df.tail(limit).to_dict('records')

        return jsonify({
            'success': True,
            'symbol': symbol,
            'timeframe': timeframe,
            'total_records': len(df),
            'preview_records': len(preview_data),
            'data': preview_data
        })

    except Exception as e:
        logger.error(f"Error in data_preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500