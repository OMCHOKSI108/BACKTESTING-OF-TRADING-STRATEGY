from flask import Blueprint, request, jsonify, render_template
from app.services.data_service import DataService
from app.services.backtest_service import EnhancedBacktestService
import importlib
import logging

logger = logging.getLogger(__name__)

strategy_bp = Blueprint("strategy", __name__, url_prefix="/api/strategy")

data_service = DataService()
backtest_service = EnhancedBacktestService()

@strategy_bp.route("/", methods=["GET"])
def strategy_info():
    """Strategy API information"""
    return jsonify({
        "module": "Strategy Service API",
        "description": "Handles trading strategy execution and backtesting",
        "endpoints": {
            "POST /api/strategy/run/<id>": "Run specific strategy (1-5)",
            "POST /api/strategy/compare": "Compare all strategies",
            "GET /api/strategy/list": "List available strategies",
            "GET /api/strategy/results/<symbol>/<id>": "Get strategy results"
        },
        "available_strategies": {
            1: "SMA Crossover (9/21)",
            2: "RSI Mean Reversion",
            3: "Bollinger Bands",
            4: "MACD Crossover",
            5: "Multi-Indicator (RSI + EMA)"
        },
        "status": "active"
    })

@strategy_bp.route("/run/<int:strategy_id>", methods=["POST"])
def run_strategy(strategy_id):
    """Run a specific strategy on market data"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        market_type = data.get('market_type', 'US Stocks')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        timeframe = data.get('timeframe', '1d')
        initial_balance = data.get('initial_balance', 100000)

        if not all([symbol, start_date, end_date]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: symbol, start_date, end_date'
            }), 400

        # Load market data
        df = data_service.load_processed_data(symbol, timeframe)
        if df.empty:
            return jsonify({
                'success': False,
                'error': f'No processed data available for {symbol}. Please gather data first.'
            }), 404

        # Import strategy function
        try:
            strategy_module = importlib.import_module(f'app.strategies.strategy{strategy_id}')
            
            # Map strategy IDs to actual function names
            strategy_functions = {
                1: 'strategy_1_sma_crossover',
                2: 'strategy_2_rsi_divergence', 
                3: 'strategy_3_bollinger_bands',
                4: 'strategy_4_macd_crossover',
                5: 'strategy_5_multi_indicator'
            }
            
            func_name = strategy_functions.get(strategy_id)
            if not func_name:
                raise AttributeError(f"Strategy {strategy_id} not mapped")
                
            strategy_func = getattr(strategy_module, func_name)
        except (ImportError, AttributeError) as e:
            return jsonify({
                'success': False,
                'error': f'Strategy {strategy_id} not found or invalid: {str(e)}'
            }), 404

        # Update backtest service balance
        backtest_service.initial_balance = initial_balance

        # Run backtest
        logger.info(f"Running Strategy {strategy_id} on {symbol}")
        results = backtest_service.run_backtest(
            df, strategy_func, symbol, f"Strategy {strategy_id}",
            initial_balance=initial_balance
        )

        return jsonify({
            'success': True,
            'strategy_id': strategy_id,
            'symbol': symbol,
            'results': results
        })

    except Exception as e:
        logger.error(f"Error running strategy {strategy_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@strategy_bp.route("/compare", methods=["POST"])
def compare_strategies():
    """Compare multiple strategies on the same data"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        market_type = data.get('market_type', 'US Stocks')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        timeframe = data.get('timeframe', '1d')
        strategy_ids = data.get('strategy_ids', [1, 2, 3, 4, 5])
        initial_balance = data.get('initial_balance', 100000)

        if not all([symbol, start_date, end_date]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: symbol, start_date, end_date'
            }), 400

        # Load market data
        df = data_service.load_processed_data(symbol, timeframe)
        if df.empty:
            return jsonify({
                'success': False,
                'error': f'No processed data available for {symbol}. Please gather data first.'
            }), 404

        results_list = []

        # Run each strategy
        for strategy_id in strategy_ids:
            try:
                # Import strategy function
                strategy_module = importlib.import_module(f'app.strategies.strategy{strategy_id}')
                strategy_func = getattr(strategy_module, f'strategy_{strategy_id}')

                # Update backtest service balance
                backtest_service.initial_balance = initial_balance

                # Run backtest
                logger.info(f"Running Strategy {strategy_id} on {symbol} for comparison")
                results = backtest_service.run_backtest(
                    df, strategy_func, symbol, f"Strategy {strategy_id}",
                    initial_balance=initial_balance
                )
                results_list.append(results)

            except Exception as e:
                logger.error(f"Error running strategy {strategy_id} for comparison: {str(e)}")
                continue

        if not results_list:
            return jsonify({
                'success': False,
                'error': 'No strategies could be executed successfully'
            }), 500

        # Compare results
        comparison = backtest_service.compare_strategies(results_list)

        return jsonify({
            'success': True,
            'symbol': symbol,
            'comparison': comparison,
            'individual_results': results_list
        })

    except Exception as e:
        logger.error(f"Error in strategy comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@strategy_bp.route("/list", methods=["GET"])
def list_strategies():
    """List available strategies"""
    strategies = [
        {
            'id': 1,
            'name': 'SMA Crossover',
            'description': 'Simple Moving Average crossover strategy (9/21)',
            'parameters': ['fast_period', 'slow_period']
        },
        {
            'id': 2,
            'name': 'RSI Mean Reversion',
            'description': 'RSI-based mean reversion strategy',
            'parameters': ['rsi_period', 'overbought', 'oversold']
        },
        {
            'id': 3,
            'name': 'Bollinger Bands',
            'description': 'Bollinger Bands mean reversion strategy',
            'parameters': ['period', 'std_dev']
        },
        {
            'id': 4,
            'name': 'MACD Crossover',
            'description': 'MACD crossover strategy',
            'parameters': ['fast_period', 'slow_period', 'signal_period']
        },
        {
            'id': 5,
            'name': 'Multi-Indicator',
            'description': 'RSI + EMA combined confirmation strategy',
            'parameters': ['rsi_period', 'ema_short', 'ema_long', 'rsi_overbought', 'rsi_oversold']
        }
    ]

    return jsonify({
        'success': True,
        'strategies': strategies
    })

@strategy_bp.route("/results/<symbol>/<int:strategy_id>", methods=["GET"])
def get_strategy_results(symbol, strategy_id):
    """Get saved results for a specific strategy and symbol"""
    try:
        # This would typically load from a database or cache
        # For now, return a placeholder
        return jsonify({
            'success': True,
            'symbol': symbol,
            'strategy_id': strategy_id,
            'message': 'Results retrieval not yet implemented',
            'available': False
        })

    except Exception as e:
        logger.error(f"Error retrieving strategy results: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500