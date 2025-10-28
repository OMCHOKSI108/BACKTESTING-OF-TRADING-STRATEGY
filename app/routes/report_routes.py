from flask import Blueprint, request, jsonify, send_file
from app.services.report_service import ReportService
from app.services.backtest_service import EnhancedBacktestService
import os
import logging

logger = logging.getLogger(__name__)

report_bp = Blueprint("report", __name__, url_prefix="/api/report")

report_service = ReportService()
backtest_service = EnhancedBacktestService()


@report_bp.route("/", methods=["GET"])
def report_info():
    """Report API information"""
    return jsonify(
        {
            "module": "Report Service API",
            "description": "Handles PDF report generation and management",
            "endpoints": {
                "POST /api/report/generate": "Generate PDF report",
                "POST /api/report/compare": "Generate comparison report",
                "GET /api/report/download/<filename>": "Download PDF report",
                "GET /api/report/list/<symbol>": "List reports for symbol",
                "DELETE /api/report/delete/<filename>": "Delete report",
                "GET /api/report/charts/<filename>": "Get report charts",
            },
            "supported_formats": ["PDF"],
            "features": [
                "Equity curves",
                "Performance metrics",
                "Trade history",
                "Risk analysis",
            ],
            "status": "active",
        }
    )


@report_bp.route("/generate", methods=["POST"])
def generate_report():
    """Generate PDF report for backtest results"""
    try:
        data = request.get_json()

        symbol = data.get("symbol")
        strategy_name = data.get("strategy_name")
        results = data.get("results")

        if not all([symbol, strategy_name, results]):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing required parameters: symbol, strategy_name, results",
                    }
                ),
                400,
            )

        logger.info(f"Generating PDF report for {strategy_name} on {symbol}")

        # Generate PDF report
        pdf_path = report_service.create_pdf_report(results, symbol, strategy_name)

        if pdf_path and os.path.exists(pdf_path):
            filename = os.path.basename(pdf_path)
            return jsonify(
                {
                    "success": True,
                    "message": "PDF report generated successfully",
                    "filename": filename,
                    "download_url": f"/api/report/download/{filename}",
                }
            )
        else:
            return (
                jsonify({"success": False, "error": "Failed to generate PDF report"}),
                500,
            )

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route("/generate_ai", methods=["POST"])
def generate_ai_report():
    """Generate PDF report for AI research result"""
    try:
        data = request.get_json() or {}

        research = data.get("research")
        title = data.get("title")

        if not research:
            return (
                jsonify({"success": False, "error": "Missing required parameter: research"}),
                400,
            )

        logger.info(f"Generating AI research PDF report for query: {research.get('query')}")

        pdf_path = report_service.create_ai_research_report(research, title=title)

        if pdf_path and os.path.exists(pdf_path):
            filename = os.path.basename(pdf_path)
            return jsonify(
                {
                    "success": True,
                    "message": "AI PDF report generated successfully",
                    "filename": filename,
                    "download_url": f"/api/report/download/{filename}",
                }
            )
        else:
            return (
                jsonify({"success": False, "error": "Failed to generate AI PDF report"}),
                500,
            )

    except Exception as e:
        logger.error(f"Error generating AI report: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route("/compare", methods=["POST"])
def generate_comparison_report():
    """Generate PDF comparison report for multiple strategies"""
    try:
        data = request.get_json()

        symbol = data.get("symbol")
        results_list = data.get("results_list")

        if not all([symbol, results_list]):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing required parameters: symbol, results_list",
                    }
                ),
                400,
            )

        logger.info(f"Generating comparison report for {symbol}")

        # Generate comparison PDF report
        pdf_path = report_service.generate_strategy_comparison_report(
            results_list, symbol
        )

        if pdf_path and os.path.exists(pdf_path):
            filename = os.path.basename(pdf_path)
            return jsonify(
                {
                    "success": True,
                    "message": "Comparison report generated successfully",
                    "filename": filename,
                    "download_url": f"/api/report/download/{filename}",
                }
            )
        else:
            return (
                jsonify(
                    {"success": False, "error": "Failed to generate comparison report"}
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Error generating comparison report: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route("/download/<filename>", methods=["GET"])
def download_report(filename):
    """Download a generated PDF report"""
    try:
        filepath = os.path.join(report_service.reports_path, filename)

        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Report file not found"}), 404

        return send_file(filepath, as_attachment=True, download_name=filename)

    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route("/list/<symbol>", methods=["GET"])
def list_reports(symbol):
    """List available reports for a symbol"""
    try:
        if not os.path.exists(report_service.reports_path):
            return jsonify({"success": True, "reports": []})

        # Find all reports for this symbol
        reports = []
        for filename in os.listdir(report_service.reports_path):
            if filename.startswith(symbol) and filename.endswith(".pdf"):
                filepath = os.path.join(report_service.reports_path, filename)
                file_stats = os.stat(filepath)

                reports.append(
                    {
                        "filename": filename,
                        "size": file_stats.st_size,
                        "created": file_stats.st_ctime,
                        "download_url": f"/api/report/download/{filename}",
                    }
                )

        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x["created"], reverse=True)

        return jsonify({"success": True, "symbol": symbol, "reports": reports})

    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route("/delete/<filename>", methods=["DELETE"])
def delete_report(filename):
    """Delete a report file"""
    try:
        filepath = os.path.join(report_service.reports_path, filename)

        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Report file not found"}), 404

        os.remove(filepath)

        return jsonify(
            {"success": True, "message": f"Report {filename} deleted successfully"}
        )

    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route("/charts/<filename>", methods=["GET"])
def get_chart(filename):
    """Serve chart images"""
    try:
        filepath = os.path.join(report_service.charts_path, filename)

        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Chart file not found"}), 404

        return send_file(filepath, mimetype="image/png")

    except Exception as e:
        logger.error(f"Error serving chart: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
