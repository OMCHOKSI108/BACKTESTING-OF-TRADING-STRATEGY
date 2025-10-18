import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os
import concurrent.futures
from typing import List, Dict, Any
import multiprocessing
from functools import partial
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedBacktestService:
    def __init__(self, initial_balance=100000, max_workers=None):
        self.initial_balance = initial_balance
        self.trade_history_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'trade_history')
        os.makedirs(self.trade_history_path, exist_ok=True)
        
        # Performance optimizations
        self.max_workers = max_workers or min(32, multiprocessing.cpu_count() + 4)
        logger.info(f"Enhanced BacktestService initialized with {self.max_workers} workers")

    def calculate_returns(self, pnl_series):
        """Calculate returns from PnL series"""
        if len(pnl_series) == 0:
            return pd.Series()

        # Calculate cumulative returns
        cumulative_pnl = pnl_series.cumsum()
        returns = cumulative_pnl.pct_change().fillna(0)
        return returns

    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """Calculate Sharpe Ratio"""
        if len(returns) < 2:
            return 0

        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        if excess_returns.std() == 0:
            return 0

        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)  # Annualized
        return round(sharpe_ratio, 2)

    def calculate_sortino_ratio(self, returns, risk_free_rate=0.02):
        """Calculate Sortino Ratio"""
        if len(returns) < 2:
            return 0

        excess_returns = returns - risk_free_rate/252
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0

        sortino_ratio = excess_returns.mean() / downside_returns.std() * np.sqrt(252)
        return round(sortino_ratio, 2)

    def calculate_max_drawdown(self, pnl_series):
        """Calculate Maximum Drawdown"""
        if len(pnl_series) == 0:
            return 0

        cumulative = pnl_series.cumsum()
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        max_drawdown = drawdown.min()

        return round(max_drawdown, 2)

    def calculate_win_rate(self, pnl_series):
        """Calculate Win Rate"""
        if len(pnl_series) == 0:
            return 0

        winning_trades = (pnl_series > 0).sum()
        total_trades = len(pnl_series)

        return round((winning_trades / total_trades) * 100, 2)

    def calculate_profit_factor(self, pnl_series):
        """Calculate Profit Factor"""
        if len(pnl_series) == 0:
            return 0

        gross_profit = pnl_series[pnl_series > 0].sum()
        gross_loss = abs(pnl_series[pnl_series < 0].sum())

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0

        return round(gross_profit / gross_loss, 2)

    def calculate_average_trade_duration(self, trade_durations):
        """Calculate average trade duration in days"""
        if len(trade_durations) == 0:
            return 0

        return round(np.mean(trade_durations), 2)

    def generate_equity_curve(self, pnl_series):
        """Generate equity curve data"""
        if len(pnl_series) == 0:
            return []

        equity = self.initial_balance + pnl_series.cumsum()
        return equity.tolist()

    def generate_drawdown_curve(self, pnl_series):
        """Generate drawdown curve data"""
        if len(pnl_series) == 0:
            return []

        cumulative = pnl_series.cumsum()
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max

        return drawdown.tolist()

    def save_trade_history(self, trades, symbol, strategy_name):
        """Save trade history to CSV"""
        if not trades:
            return False

        filename = f"{symbol}_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.trade_history_path, filename)

        try:
            # Convert trades to DataFrame
            trade_df = pd.DataFrame(trades, columns=['entry_time', 'entry_price', 'exit_time', 'exit_price', 'pnl'])
            trade_df.to_csv(filepath, index=False)
            logger.info(f"Saved trade history to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving trade history: {str(e)}")
            return False

    def run_backtest(self, df, strategy_func, symbol, strategy_name, **kwargs):
        """
        Run backtest with comprehensive metrics calculation

        Args:
            df: DataFrame with OHLCV data
            strategy_func: Function that implements the trading strategy
            symbol: Trading symbol
            strategy_name: Name of the strategy
            **kwargs: Additional parameters for the strategy

        Returns:
            dict: Comprehensive backtest results
        """
        logger.info(f"Running backtest for {strategy_name} on {symbol}")

        try:
            # Run the strategy
            result = strategy_func(df, **kwargs)

            # Extract trade data
            trades = result.get('trades', [])
            pnl_series = pd.Series([trade.get('pnl', 0) for trade in trades])

            # Calculate comprehensive metrics
            total_trades = len(trades)
            gross_profit = pnl_series[pnl_series > 0].sum() if len(pnl_series) > 0 else 0
            gross_loss = abs(pnl_series[pnl_series < 0].sum()) if len(pnl_series) > 0 else 0
            net_profit = pnl_series.sum() if len(pnl_series) > 0 else 0
            final_balance = self.initial_balance + net_profit

            # Calculate returns for risk metrics
            returns = self.calculate_returns(pnl_series)

            # Calculate all metrics
            metrics = {
                'symbol': symbol,
                'strategy': strategy_name,
                'initial_balance': self.initial_balance,
                'final_balance': round(final_balance, 2),
                'net_profit_loss': round(net_profit, 2),
                'gross_profit': round(gross_profit, 2),
                'gross_loss': round(gross_loss, 2),
                'total_trades': total_trades,
                'win_rate': self.calculate_win_rate(pnl_series),
                'profit_factor': self.calculate_profit_factor(pnl_series),
                'max_drawdown': self.calculate_max_drawdown(pnl_series),
                'sharpe_ratio': self.calculate_sharpe_ratio(returns),
                'sortino_ratio': self.calculate_sortino_ratio(returns),
                'average_trade_pnl': round(pnl_series.mean(), 2) if len(pnl_series) > 0 else 0,
                'largest_win': round(pnl_series.max(), 2) if len(pnl_series) > 0 else 0,
                'largest_loss': round(pnl_series.min(), 2) if len(pnl_series) > 0 else 0,
            }

            # Add trade statistics if available
            if 'trade_durations' in result:
                metrics['average_trade_duration'] = self.calculate_average_trade_duration(result['trade_durations'])

            # Generate curves
            metrics['equity_curve'] = self.generate_equity_curve(pnl_series)
            metrics['drawdown_curve'] = self.generate_drawdown_curve(pnl_series)

            # Save trade history
            if trades:
                self.save_trade_history(trades, symbol, strategy_name)

            # Add original trade data
            metrics['trades'] = trades

            # Add any additional data from strategy result
            for key, value in result.items():
                if key not in metrics:
                    metrics[key] = value

            logger.info(f"Backtest completed for {strategy_name}: {total_trades} trades, P&L: {net_profit:.2f}")
            return metrics

        except Exception as e:
            logger.error(f"Error running backtest for {strategy_name}: {str(e)}")
            return {
                'symbol': symbol,
                'strategy': strategy_name,
                'error': str(e),
                'total_trades': 0,
                'net_profit_loss': 0
            }

    def compare_strategies(self, results_list):
        """
        Compare multiple strategy results

        Args:
            results_list: List of backtest result dictionaries

        Returns:
            dict: Comparison metrics
        """
        if not results_list:
            return {}

        comparison = {
            'strategies': [r['strategy'] for r in results_list],
            'net_profits': [r.get('net_profit_loss', 0) for r in results_list],
            'win_rates': [r.get('win_rate', 0) for r in results_list],
            'sharpe_ratios': [r.get('sharpe_ratio', 0) for r in results_list],
            'max_drawdowns': [r.get('max_drawdown', 0) for r in results_list],
            'total_trades': [r.get('total_trades', 0) for r in results_list],
        }

        # Find best performing strategy
        best_idx = np.argmax(comparison['net_profits'])
        comparison['best_strategy'] = comparison['strategies'][best_idx]
        comparison['best_net_profit'] = comparison['net_profits'][best_idx]

        return comparison

    def run_concurrent_backtests(self, data_dict: Dict[str, pd.DataFrame], 
                                strategy_configs: List[Dict]) -> Dict[str, Dict]:
        """
        Run multiple backtests concurrently for different symbols and strategies
        
        Args:
            data_dict: Dictionary of {symbol: dataframe}
            strategy_configs: List of strategy configurations
            
        Returns:
            Dict: Results organized by symbol and strategy
        """
        logger.info(f"Starting concurrent backtests for {len(data_dict)} symbols and {len(strategy_configs)} strategies")
        
        results = {}
        tasks = []
        
        # Prepare all tasks
        for symbol, df in data_dict.items():
            results[symbol] = {}
            for config in strategy_configs:
                tasks.append((symbol, df, config))
        
        def run_single_backtest(task_data):
            symbol, df, config = task_data
            strategy_name = config['name']
            strategy_func = config['function']
            
            try:
                start_time = time.time()
                result = strategy_func(df)
                
                # Add performance metrics
                result['execution_time'] = time.time() - start_time
                result['symbol'] = symbol
                result['strategy'] = strategy_name
                
                logger.info(f"✅ {symbol} - {strategy_name}: {result.get('total_trades', 0)} trades, "
                          f"{result.get('net_profit_loss', 0):.2f} P&L ({result['execution_time']:.2f}s)")
                
                return symbol, strategy_name, result
                
            except Exception as e:
                logger.error(f"❌ Error in {symbol} - {strategy_name}: {e}")
                return symbol, strategy_name, {
                    'error': str(e),
                    'total_trades': 0,
                    'net_profit_loss': 0,
                    'execution_time': 0
                }
        
        # Execute all tasks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(run_single_backtest, task) for task in tasks]
            
            for future in concurrent.futures.as_completed(futures):
                symbol, strategy_name, result = future.result()
                results[symbol][strategy_name] = result
        
        logger.info(f"Completed concurrent backtests for {len(data_dict)} symbols")
        return results

    def batch_optimize_strategies(self, data_dict: Dict[str, pd.DataFrame], 
                                 parameter_grid: Dict[str, List]) -> Dict:
        """
        Batch optimization of strategy parameters across multiple symbols
        
        Args:
            data_dict: Dictionary of {symbol: dataframe}
            parameter_grid: Grid of parameters to test
            
        Returns:
            Dict: Optimization results
        """
        logger.info(f"Starting batch optimization for {len(data_dict)} symbols")
        
        optimization_results = {}
        
        def optimize_single_symbol(symbol_data):
            symbol, df = symbol_data
            best_result = None
            best_score = float('-inf')
            
            # Test all parameter combinations
            for params in self._generate_parameter_combinations(parameter_grid):
                try:
                    # Run strategy with these parameters
                    result = self._run_strategy_with_params(df, params)
                    
                    # Score based on risk-adjusted returns
                    score = self._calculate_optimization_score(result)
                    
                    if score > best_score:
                        best_score = score
                        best_result = {**result, 'parameters': params, 'score': score}
                
                except Exception as e:
                    logger.error(f"Error optimizing {symbol} with params {params}: {e}")
                    continue
            
            return symbol, best_result
        
        # Run optimization concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(optimize_single_symbol, (symbol, df))
                for symbol, df in data_dict.items()
            ]
            
            for future in concurrent.futures.as_completed(futures):
                symbol, result = future.result()
                if result:
                    optimization_results[symbol] = result
                    logger.info(f"✅ Optimized {symbol}: Score {result['score']:.4f}")
        
        return optimization_results

    def _generate_parameter_combinations(self, parameter_grid: Dict[str, List]) -> List[Dict]:
        """Generate all combinations of parameters"""
        import itertools
        
        keys = parameter_grid.keys()
        values = parameter_grid.values()
        
        combinations = []
        for combination in itertools.product(*values):
            combinations.append(dict(zip(keys, combination)))
        
        return combinations

    def _run_strategy_with_params(self, df: pd.DataFrame, params: Dict) -> Dict:
        """Run a strategy with specific parameters"""
        # This is a placeholder - implement based on your strategy functions
        # For now, return mock results
        return {
            'total_trades': np.random.randint(10, 100),
            'net_profit_loss': np.random.uniform(-1000, 5000),
            'win_rate': np.random.uniform(0.3, 0.7),
            'sharpe_ratio': np.random.uniform(0.5, 2.0)
        }

    def _calculate_optimization_score(self, result: Dict) -> float:
        """Calculate optimization score (risk-adjusted return)"""
        net_profit = result.get('net_profit_loss', 0)
        sharpe_ratio = result.get('sharpe_ratio', 0)
        win_rate = result.get('win_rate', 0)
        
        # Weighted score combining multiple metrics
        score = (0.4 * net_profit / 10000) + (0.3 * sharpe_ratio) + (0.3 * win_rate)
        return score

    def get_performance_statistics(self) -> Dict:
        """Get performance statistics of the backtest service"""
        return {
            'max_workers': self.max_workers,
            'cpu_count': multiprocessing.cpu_count(),
            'initial_balance': self.initial_balance,
            'trade_history_path': self.trade_history_path
        }

# Maintain backward compatibility
BacktestService = EnhancedBacktestService