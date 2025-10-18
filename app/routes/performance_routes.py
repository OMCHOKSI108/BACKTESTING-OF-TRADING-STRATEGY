from flask import Blueprint, jsonify, request
from app.services.data_service import EnhancedDataService
from app.services.backtest_service import EnhancedBacktestService
import logging

logger = logging.getLogger(__name__)

# Initialize enhanced services
data_service = EnhancedDataService()
backtest_service = EnhancedBacktestService()

performance_bp = Blueprint("performance", __name__, url_prefix="/api/performance")

@performance_bp.route("/", methods=["GET"])
def performance_info():
    """Performance API information"""
    return jsonify({
        "module": "Performance Monitoring",
        "description": "Monitor system performance and resource usage",
        "endpoints": {
            "GET /api/performance/": "Performance API information",
            "GET /api/performance/stats": "System performance statistics",
            "GET /api/performance/cache": "Cache performance metrics",
            "POST /api/performance/concurrent-test": "Test concurrent processing performance",
            "GET /api/performance/health": "System health check"
        },
        "status": "active"
    })

@performance_bp.route("/stats", methods=["GET"])
def get_performance_stats():
    """Get system performance statistics"""
    try:
        # Get data service stats
        data_stats = data_service.get_performance_statistics()
        
        # Get backtest service stats
        backtest_stats = backtest_service.get_performance_statistics()
        
        return jsonify({
            "status": "success",
            "timestamp": data_service._get_current_timestamp(),
            "data_service": data_stats,
            "backtest_service": backtest_stats,
            "system_info": {
                "enhanced_services_active": True,
                "concurrent_processing": True,
                "cache_enabled": True
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@performance_bp.route("/cache", methods=["GET"])
def get_cache_stats():
    """Get cache performance metrics"""
    try:
        cache_stats = data_service.get_cache_statistics()
        
        return jsonify({
            "status": "success",
            "timestamp": data_service._get_current_timestamp(),
            "cache": cache_stats
        })
    
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@performance_bp.route("/concurrent-test", methods=["POST"])
def test_concurrent_performance():
    """Test concurrent processing performance"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA'])
        timeframe = data.get('timeframe', '1d')
        period = data.get('period', '1mo')
        
        logger.info(f"Testing concurrent performance for {len(symbols)} symbols")
        
        # Test concurrent data fetching
        import time
        start_time = time.time()
        
        data_results = data_service.get_multiple_stocks_data(
            symbols=symbols,
            timeframe=timeframe,
            period=period
        )
        
        fetch_time = time.time() - start_time
        
        # Count successful fetches
        successful_fetches = sum(1 for df in data_results.values() if not df.empty)
        
        return jsonify({
            "status": "success",
            "test_results": {
                "symbols_requested": len(symbols),
                "symbols_fetched": successful_fetches,
                "fetch_time_seconds": round(fetch_time, 3),
                "symbols_per_second": round(len(symbols) / fetch_time, 2),
                "cache_hits": data_service.cache_hits,
                "cache_misses": data_service.cache_misses
            },
            "symbols": symbols,
            "performance_rating": "Excellent" if fetch_time < 5 else "Good" if fetch_time < 10 else "Needs Optimization"
        })
    
    except Exception as e:
        logger.error(f"Error in concurrent performance test: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@performance_bp.route("/health", methods=["GET"])
def health_check():
    """System health check"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "timestamp": data_service._get_current_timestamp(),
            "services": {
                "data_service": "active",
                "backtest_service": "active",
                "cache": "active"
            },
            "resources": {
                "cache_size": len(data_service.cache) if hasattr(data_service, 'cache') else 0,
                "max_workers": backtest_service.max_workers
            }
        }
        
        # Test cache connection
        try:
            data_service._init_cache()
            health_status["services"]["cache_connection"] = "healthy"
        except Exception as e:
            health_status["services"]["cache_connection"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        return jsonify(health_status)
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": data_service._get_current_timestamp()
        }), 500

@performance_bp.route("/clear-cache", methods=["POST"])
def clear_cache():
    """Clear cache and reset statistics"""
    try:
        data_service.clear_cache()
        
        return jsonify({
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": data_service._get_current_timestamp()
        })
    
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500