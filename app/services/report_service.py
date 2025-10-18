import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
import io

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self):
        self.reports_path = os.path.join(os.path.dirname(__file__), '..', 'reports')
        self.charts_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'charts')
        os.makedirs(self.reports_path, exist_ok=True)
        os.makedirs(self.charts_path, exist_ok=True)

    def generate_equity_curve_chart(self, equity_curve, symbol, strategy_name):
        """Generate equity curve chart"""
        try:
            plt.figure(figsize=(10, 6))
            plt.plot(equity_curve, linewidth=2, color='blue')
            plt.title(f'Equity Curve - {symbol} ({strategy_name})')
            plt.xlabel('Trade Number')
            plt.ylabel('Portfolio Value ($)')
            plt.grid(True, alpha=0.3)
            plt.axhline(y=100000, color='red', linestyle='--', alpha=0.7, label='Initial Balance')
            plt.legend()

            filename = f"equity_curve_{symbol}_{strategy_name}_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(self.charts_path, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return filepath
        except Exception as e:
            logger.error(f"Error generating equity curve chart: {str(e)}")
            return None

    def generate_drawdown_chart(self, drawdown_curve, symbol, strategy_name):
        """Generate drawdown chart"""
        try:
            plt.figure(figsize=(10, 6))
            plt.fill_between(range(len(drawdown_curve)), drawdown_curve, 0,
                           color='red', alpha=0.3, label='Drawdown')
            plt.plot(drawdown_curve, color='red', linewidth=1)
            plt.title(f'Drawdown Chart - {symbol} ({strategy_name})')
            plt.xlabel('Trade Number')
            plt.ylabel('Drawdown ($)')
            plt.grid(True, alpha=0.3)
            plt.legend()

            filename = f"drawdown_chart_{symbol}_{strategy_name}_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(self.charts_path, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return filepath
        except Exception as e:
            logger.error(f"Error generating drawdown chart: {str(e)}")
            return None

    def generate_pnl_distribution_chart(self, trades, symbol, strategy_name):
        """Generate P&L distribution histogram"""
        try:
            if not trades:
                return None

            pnl_values = [trade.get('pnl', 0) for trade in trades]

            plt.figure(figsize=(10, 6))
            plt.hist(pnl_values, bins=20, alpha=0.7, color='green', edgecolor='black')
            plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Break-even')
            plt.title(f'P&L Distribution - {symbol} ({strategy_name})')
            plt.xlabel('Profit/Loss ($)')
            plt.ylabel('Frequency')
            plt.grid(True, alpha=0.3)
            plt.legend()

            filename = f"pnl_distribution_{symbol}_{strategy_name}_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(self.charts_path, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return filepath
        except Exception as e:
            logger.error(f"Error generating P&L distribution chart: {str(e)}")
            return None

    def generate_performance_summary_chart(self, metrics, symbol, strategy_name):
        """Generate performance summary bar chart"""
        try:
            # Key metrics for visualization
            labels = ['Net P&L', 'Gross Profit', 'Gross Loss', 'Max Drawdown']
            values = [
                metrics.get('net_profit_loss', 0),
                metrics.get('gross_profit', 0),
                metrics.get('gross_loss', 0),
                abs(metrics.get('max_drawdown', 0))
            ]

            colors_list = ['green' if v >= 0 else 'red' for v in values]

            plt.figure(figsize=(12, 6))
            bars = plt.bar(labels, values, color=colors_list, alpha=0.7, edgecolor='black')
            plt.title(f'Performance Summary - {symbol} ({strategy_name})')
            plt.ylabel('Amount ($)')
            plt.grid(True, alpha=0.3, axis='y')

            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + (0.01 * max(values) if height >= 0 else -0.05 * min(values)),
                        f'${value:,.0f}', ha='center', va='bottom' if height >= 0 else 'top')

            filename = f"performance_summary_{symbol}_{strategy_name}_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(self.charts_path, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return filepath
        except Exception as e:
            logger.error(f"Error generating performance summary chart: {str(e)}")
            return None

    def create_pdf_report(self, metrics, symbol, strategy_name):
        """
        Create comprehensive PDF report with charts and metrics

        Args:
            metrics: Backtest results dictionary
            symbol: Trading symbol
            strategy_name: Name of the strategy

        Returns:
            str: Path to generated PDF file
        """
        try:
            logger.info(f"Generating PDF report for {strategy_name} on {symbol}")

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{symbol}_{strategy_name}_{timestamp}.pdf"
            filepath = os.path.join(self.reports_path, filename)

            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            title = Paragraph(f"Trading Strategy Backtest Report<br/>{symbol} - {strategy_name}", title_style)
            story.append(title)
            story.append(Spacer(1, 12))

            # Report metadata
            meta_style = ParagraphStyle(
                'Meta',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.gray
            )
            meta_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            meta_text += f"Initial Balance: ${metrics.get('initial_balance', 100000):,}<br/>"
            meta_text += f"Total Trades: {metrics.get('total_trades', 0)}"
            story.append(Paragraph(meta_text, meta_style))
            story.append(Spacer(1, 20))

            # Key Metrics Table
            story.append(Paragraph("Key Performance Metrics", styles['Heading2']))
            story.append(Spacer(1, 12))

            key_metrics_data = [
                ['Metric', 'Value'],
                ['Net Profit/Loss', f"${metrics.get('net_profit_loss', 0):,.2f}"],
                ['Gross Profit', f"${metrics.get('gross_profit', 0):,.2f}"],
                ['Gross Loss', f"${metrics.get('gross_loss', 0):,.2f}"],
                ['Win Rate', f"{metrics.get('win_rate', 0):.1f}%"],
                ['Profit Factor', f"{metrics.get('profit_factor', 0):.2f}"],
                ['Total Trades', str(metrics.get('total_trades', 0))],
                ['Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}"],
                ['Sortino Ratio', f"{metrics.get('sortino_ratio', 0):.2f}"],
                ['Max Drawdown', f"${metrics.get('max_drawdown', 0):,.2f}"],
                ['Average Trade P&L', f"${metrics.get('average_trade_pnl', 0):,.2f}"],
                ['Largest Win', f"${metrics.get('largest_win', 0):,.2f}"],
                ['Largest Loss', f"${metrics.get('largest_loss', 0):,.2f}"],
            ]

            key_metrics_table = Table(key_metrics_data)
            key_metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(key_metrics_table)
            story.append(Spacer(1, 20))

            # Generate and add charts
            charts = []

            # Equity curve chart
            equity_curve_path = self.generate_equity_curve_chart(
                metrics.get('equity_curve', []), symbol, strategy_name
            )
            if equity_curve_path:
                charts.append(("Equity Curve", equity_curve_path))

            # Drawdown chart
            drawdown_path = self.generate_drawdown_chart(
                metrics.get('drawdown_curve', []), symbol, strategy_name
            )
            if drawdown_path:
                charts.append(("Drawdown Chart", drawdown_path))

            # P&L distribution
            pnl_dist_path = self.generate_pnl_distribution_chart(
                metrics.get('trades', []), symbol, strategy_name
            )
            if pnl_dist_path:
                charts.append(("P&L Distribution", pnl_dist_path))

            # Performance summary
            perf_summary_path = self.generate_performance_summary_chart(
                metrics, symbol, strategy_name
            )
            if perf_summary_path:
                charts.append(("Performance Summary", perf_summary_path))

            # Add charts to PDF
            for chart_title, chart_path in charts:
                story.append(Paragraph(chart_title, styles['Heading3']))
                story.append(Spacer(1, 12))

                # Add image (resize to fit page)
                img = Image(chart_path, width=6*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 20))

            # Trade History (if available)
            trades = metrics.get('trades', [])
            if trades and len(trades) > 0:
                story.append(Paragraph("Recent Trades", styles['Heading3']))
                story.append(Spacer(1, 12))

                # Show last 20 trades
                recent_trades = trades[-20:]
                trade_data = [['Entry Time', 'Entry Price', 'Exit Time', 'Exit Price', 'P&L']]

                for trade in recent_trades:
                    entry_time = trade.get('entry_time', 'N/A')
                    entry_price = f"${trade.get('entry_price', 0):,.2f}"
                    exit_time = trade.get('exit_time', 'N/A')
                    exit_price = f"${trade.get('exit_price', 0):,.2f}"
                    pnl = f"${trade.get('pnl', 0):,.2f}"
                    trade_data.append([entry_time, entry_price, exit_time, exit_price, pnl])

                trade_table = Table(trade_data[:21])  # Header + 20 trades max
                trade_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                story.append(trade_table)

            # Build PDF
            doc.build(story)

            logger.info(f"PDF report generated: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error creating PDF report: {str(e)}")
            return None

    def generate_strategy_comparison_report(self, comparison_results, symbol):
        """
        Generate PDF report comparing multiple strategies

        Args:
            comparison_results: List of backtest result dictionaries
            symbol: Trading symbol

        Returns:
            str: Path to generated comparison PDF file
        """
        try:
            logger.info(f"Generating strategy comparison report for {symbol}")

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{symbol}_strategy_comparison_{timestamp}.pdf"
            filepath = os.path.join(self.reports_path, filename)

            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1
            )
            title = Paragraph(f"Strategy Comparison Report<br/>{symbol}", title_style)
            story.append(title)
            story.append(Spacer(1, 12))

            # Comparison Table
            story.append(Paragraph("Strategy Performance Comparison", styles['Heading2']))
            story.append(Spacer(1, 12))

            # Prepare comparison data
            headers = ['Strategy', 'Net P&L', 'Win Rate', 'Sharpe Ratio', 'Max Drawdown', 'Total Trades']
            comparison_data = [headers]

            for result in comparison_results:
                row = [
                    result.get('strategy', 'Unknown'),
                    f"${result.get('net_profit_loss', 0):,.2f}",
                    f"{result.get('win_rate', 0):.1f}%",
                    f"{result.get('sharpe_ratio', 0):.2f}",
                    f"${result.get('max_drawdown', 0):,.2f}",
                    str(result.get('total_trades', 0))
                ]
                comparison_data.append(row)

            comparison_table = Table(comparison_data)
            comparison_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(comparison_table)

            # Build PDF
            doc.build(story)

            logger.info(f"Strategy comparison report generated: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error creating strategy comparison report: {str(e)}")
            return None