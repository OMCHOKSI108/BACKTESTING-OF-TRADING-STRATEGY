from flask import Blueprint, render_template, request
from app.services.yfinance_service import get_stock_data
from app.services.backtester import backtest_orb_strategy

strategies_bp = Blueprint("strategies", __name__, url_prefix="/strategies")

@strategies_bp.route("/orb", methods=["GET", "POST"])
def orb_strategy():
    if request.method == "POST":
        stock = request.form["stock"]
        duration = request.form["duration"]
        df = get_stock_data(stock, duration)

        if df.empty:
            return render_template("predefined.html", error="No data found or API limit reached.")

        result = backtest_orb_strategy(df)
        return render_template("results.html", stock=stock, results=result)

    return render_template("predefined.html")
