from flask import Blueprint, render_template, request
from app.services.yfinance_service import get_stock_data
from app.services.gemini_service import parse_strategy
from app.services.backtester import backtest_strategy

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        stock = request.form["stock"]
        strategy = request.form["strategy"]
        duration = request.form["duration"]

        parsed = parse_strategy(strategy)
        df = get_stock_data(stock, duration)
        if df.empty or not all(col in df.columns for col in ["c", "h", "l", "v"]):
            return render_template(
                "index.html", error="No data found or data missing required columns."
            )
        results = backtest_strategy(df, parsed)

        return render_template("results.html", stock=stock, results=results)

    # Backend page info
    backend_info = {
        "title": "Trading Strategy Backtester - Backend API",
        "version": "1.0.0",
        "description": "RESTful API for trading strategy backtesting",
        "endpoints": {
            "main": "/",
            "data": "/api/data/*",
            "strategy": "/api/strategy/*",
            "report": "/api/report/*",
            "strategies": "/strategies/*",
        },
        "status": "running",
        "port": 3000,
    }

    return render_template("index.html", backend_info=backend_info)
