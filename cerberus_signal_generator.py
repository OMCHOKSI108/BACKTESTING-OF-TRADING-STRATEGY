#!/usr/bin/env python3
"""
Cerberus Impulse Model - Standalone Trading Signal Generator

This script takes CSV historical data and generates buy/sell trading signals
with take-profit and stop-loss levels using the trained Cerberus Impulse Model.

Usage:
    python cerberus_signal_generator.py --csv path/to/data.csv --symbol SYMBOL

Requirements:
    - pandas
    - numpy
    - lightgbm
    - pandas-ta
    - scikit-learn
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import pandas_ta as ta
import argparse
import os
import pickle
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class CerberusSignalGenerator:
    def __init__(self, model_path='models/cerberus_model_relaxed.txt'):
        """Initialize the signal generator with trained model"""
        self.model_path = model_path
        self.model = None
        self.load_model()

        # Trading parameters (same as trained model)
        self.trading_params = {
            'stop_loss_pct': 0.015,     # 1.5% stop loss
            'take_profit_pct': 0.03,    # 3% take profit
            'max_holding_period': 4,    # 4 periods max hold
            'min_confluence': 0.3,      # Minimum confluence score
        }

    def load_model(self):
        """Load the trained LightGBM model"""
        try:
            self.model = lgb.Booster(model_file=self.model_path)
            print(f"✅ Model loaded from {self.model_path}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("Please ensure the model file exists at the specified path")
            self.model = None

    def load_csv_data(self, csv_path, symbol=None):
        """Load and standardize CSV data"""
        try:
            df = pd.read_csv(csv_path)

            # Standardize column names to OHLCV format
            column_mapping = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'open' in col_lower:
                    column_mapping[col] = 'o'
                elif 'high' in col_lower:
                    column_mapping[col] = 'h'
                elif 'low' in col_lower:
                    column_mapping[col] = 'l'
                elif 'close' in col_lower:
                    column_mapping[col] = 'c'
                elif 'volume' in col_lower or 'vol' in col_lower:
                    column_mapping[col] = 'v'
                elif 'date' in col_lower or 'time' in col_lower:
                    column_mapping[col] = 'datetime'

            df = df.rename(columns=column_mapping)

            # Ensure we have required columns
            required_cols = ['o', 'h', 'l', 'c', 'v']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Convert datetime if present
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.set_index('datetime')

            # Ensure numeric types
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Remove any NaN values
            df = df.dropna()

            print(f"✅ Loaded {len(df)} candles from {csv_path}")
            return df

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return None

    def create_features(self, df):
        """Create all features required by the Cerberus model"""
        df_features = df.copy()

        try:
            # ============================================================================
            # FACTOR 1: REGIME FILTER (EMA 200)
            # ============================================================================
            df_features['ema_200'] = ta.ema(df_features['c'], length=200)
            df_features['regime_filter'] = np.where(df_features['c'] > df_features['ema_200'], 1, -1)

            # ============================================================================
            # FACTOR 2: VOLATILITY COMPRESSION (Bollinger Band Width Squeeze)
            # ============================================================================
            bb_length = 20
            bb_std = 2.0

            # Calculate Bollinger Bands
            bb = ta.bbands(df_features['c'], length=bb_length, std=bb_std)
            df_features['bb_upper'] = bb[f'BBU_{bb_length}_{bb_std}_{bb_std}']
            df_features['bb_lower'] = bb[f'BBL_{bb_length}_{bb_std}_{bb_std}']
            df_features['bb_middle'] = bb[f'BBM_{bb_length}_{bb_std}_{bb_std}']

            # Bollinger Band Width (squeeze indicator)
            df_features['bb_width'] = (df_features['bb_upper'] - df_features['bb_lower']) / df_features['bb_middle']
            df_features['bb_width_sma'] = ta.sma(df_features['bb_width'], length=20)

            # Squeeze condition (width below SMA)
            df_features['volatility_compression'] = np.where(df_features['bb_width'] < df_features['bb_width_sma'], 1, -1)

            # ============================================================================
            # FACTOR 3: BREAK OF STRUCTURE (Swing Points)
            # ============================================================================
            # Calculate swing highs and lows (simplified version)
            window = 5
            df_features['swing_high'] = df_features['h'].rolling(window=window, center=True).max()
            df_features['swing_low'] = df_features['l'].rolling(window=window, center=True).min()

            # Break of structure conditions
            df_features['bos_up'] = np.where(df_features['c'] > df_features['swing_high'].shift(1), 1, 0)
            df_features['bos_down'] = np.where(df_features['c'] < df_features['swing_low'].shift(1), 1, 0)
            df_features['break_of_structure'] = np.where(df_features['bos_up'] == 1, 1,
                                                       np.where(df_features['bos_down'] == 1, -1, 0))

            # ============================================================================
            # FACTOR 4: VOLUME CONFIRMATION
            # ============================================================================
            df_features['volume_ma'] = ta.sma(df_features['v'], length=20)
            df_features['volume_ratio'] = df_features['v'] / df_features['volume_ma']

            # Volume spike detection
            df_features['volume_confirmation'] = np.where(df_features['volume_ratio'] > 1.5, 1, -1)

            # ============================================================================
            # FACTOR 5: MOMENTUM IGNITION (RSI)
            # ============================================================================
            df_features['rsi'] = ta.rsi(df_features['c'], length=14)

            # RSI momentum signals
            df_features['rsi_bullish'] = np.where(df_features['rsi'] > 70, 1, 0)
            df_features['rsi_bearish'] = np.where(df_features['rsi'] < 30, 1, 0)
            df_features['momentum_ignition'] = np.where(df_features['rsi_bullish'] == 1, 1,
                                                      np.where(df_features['rsi_bearish'] == 1, -1, 0))

            # ============================================================================
            # CONFLUENCE SCORING (RELAXED VERSION)
            # ============================================================================
            # Weights for relaxed model (reduced BOS weight, lower threshold)
            weights = {
                'regime_filter': 0.25,
                'volatility_compression': 0.25,
                'break_of_structure': 0.25,  # Reduced from 0.3
                'volume_confirmation': 0.15,
                'momentum_ignition': 0.10
            }

            # Calculate confluence score
            df_features['confluence_score'] = (
                df_features['regime_filter'] * weights['regime_filter'] +
                df_features['volatility_compression'] * weights['volatility_compression'] +
                df_features['break_of_structure'] * weights['break_of_structure'] +
                df_features['volume_confirmation'] * weights['volume_confirmation'] +
                df_features['momentum_ignition'] * weights['momentum_ignition']
            )

            # Normalize to 0-1 range
            df_features['confluence_score'] = (df_features['confluence_score'] + 1) / 2

            # Additional features for model
            df_features['price_change'] = df_features['c'].pct_change()
            df_features['high_low_ratio'] = (df_features['h'] - df_features['l']) / df_features['c']

            # Remove NaN values created by indicators
            df_features = df_features.dropna()

            print(f"✅ Created {len(df_features)} feature rows")
            return df_features

        except Exception as e:
            print(f"❌ Error creating features: {e}")
            return None

    def generate_signals(self, df_features):
        """Generate trading signals using the trained model"""
        if self.model is None:
            print("❌ Model not loaded")
            return None

        try:
            # Feature columns used by the model
            feature_columns = [
                'regime_filter', 'volatility_compression', 'break_of_structure',
                'volume_confirmation', 'momentum_ignition', 'confluence_score',
                'rsi', 'bb_width', 'bb_width_sma', 'volume_ratio',
                'price_change', 'high_low_ratio'
            ]

            # Ensure all features are present
            missing_features = [col for col in feature_columns if col not in df_features.columns]
            if missing_features:
                print(f"❌ Missing features: {missing_features}")
                return None

            # Prepare features for prediction
            X = df_features[feature_columns].copy()

            # Make predictions
            predictions = self.model.predict(X.values)
            predictions = np.round(predictions).astype(int)  # Convert to integers

            # Get prediction probabilities/confidence
            probabilities = self.model.predict(X.values, raw_score=False)
            confidence = np.max(probabilities, axis=1)

            # Create results dataframe
            results = df_features[['o', 'h', 'l', 'c', 'v']].copy()
            results['prediction'] = predictions
            results['confidence'] = confidence
            results['confluence_score'] = df_features['confluence_score']

            # Convert predictions to signals
            results['signal'] = results['prediction'].map({
                -1: 'SELL',
                0: 'HOLD',
                1: 'BUY'
            })

            print(f"✅ Generated {len(results)} signals")
            print(f"BUY signals: {len(results[results['signal'] == 'BUY'])}")
            print(f"SELL signals: {len(results[results['signal'] == 'SELL'])}")
            print(f"HOLD signals: {len(results[results['signal'] == 'HOLD'])}")

            return results

        except Exception as e:
            print(f"❌ Error generating signals: {e}")
            return None

    def simulate_trades(self, signals_df):
        """Simulate trades with TP/SL levels"""
        trades = []
        position = None
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        entry_time = None

        for idx, row in signals_df.iterrows():
            current_price = row['c']
            current_time = idx if hasattr(idx, 'hour') else datetime.now()
            prediction = row['prediction']
            confidence = row['confidence']

            # Check for exit conditions if in position
            if position is not None:
                # Check stop loss
                if position == 'long' and current_price <= stop_loss:
                    exit_reason = 'stop_loss'
                elif position == 'short' and current_price >= stop_loss:
                    exit_reason = 'stop_loss'
                # Check take profit
                elif position == 'long' and current_price >= take_profit:
                    exit_reason = 'take_profit'
                elif position == 'short' and current_price <= take_profit:
                    exit_reason = 'take_profit'
                # Check max holding period
                elif entry_time and (current_time - entry_time).total_seconds() / 3600 >= self.trading_params['max_holding_period']:
                    exit_reason = 'max_holding'
                else:
                    exit_reason = None

                # Exit position if conditions met
                if exit_reason:
                    pnl = (current_price - entry_price) / entry_price if position == 'long' else (entry_price - current_price) / entry_price
                    pnl_pct = pnl * 100

                    trade = {
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'position': position,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'exit_reason': exit_reason,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'confidence': confidence
                    }
                    trades.append(trade)

                    position = None
                    entry_price = 0
                    stop_loss = 0
                    take_profit = 0
                    entry_time = None

            # Check for entry conditions
            if position is None and confidence > 0.8:  # High confidence only
                if prediction == 1:  # Bullish signal
                    position = 'long'
                    entry_price = current_price
                    stop_loss = entry_price * (1 - self.trading_params['stop_loss_pct'])
                    take_profit = entry_price * (1 + self.trading_params['take_profit_pct'])
                    entry_time = current_time

                elif prediction == -1:  # Bearish signal
                    position = 'short'
                    entry_price = current_price
                    stop_loss = entry_price * (1 + self.trading_params['stop_loss_pct'])
                    take_profit = entry_price * (1 - self.trading_params['take_profit_pct'])
                    entry_time = current_time

        # Close any remaining position at market
        if position is not None:
            pnl = (current_price - entry_price) / entry_price if position == 'long' else (entry_price - current_price) / entry_price
            pnl_pct = pnl * 100

            trade = {
                'entry_time': entry_time,
                'exit_time': current_time,
                'position': position,
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'exit_reason': 'end_of_data',
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'confidence': confidence
            }
            trades.append(trade)

        return trades

    def generate_report(self, signals_df, trades, output_path=None):
        """Generate a comprehensive trading report"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"cerberus_signals_{timestamp}.csv"

        # Create summary statistics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0

        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

        # Create trades dataframe
        trades_df = pd.DataFrame(trades)

        # Save signals to CSV
        signals_df.to_csv(output_path)
        print(f"✅ Signals saved to {output_path}")

        # Print summary
        print("\n" + "="*60)
        print("📊 CERBERUS IMPULSE MODEL - TRADING REPORT")
        print("="*60)
        print(f"Total Signals Generated: {len(signals_df)}")
        print(f"BUY Signals: {len(signals_df[signals_df['signal'] == 'BUY'])}")
        print(f"SELL Signals: {len(signals_df[signals_df['signal'] == 'SELL'])}")
        print(f"HOLD Signals: {len(signals_df[signals_df['signal'] == 'HOLD'])}")
        print()
        print(f"Total Trades Executed: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Total P&L: {total_pnl:.4f} ({total_pnl*100:.2f}%)")
        print(f"Average P&L per Trade: {avg_pnl:.4f} ({avg_pnl*100:.2f}%)")
        print()
        print("💡 Trading Parameters:")
        print(f"   Stop Loss: {self.trading_params['stop_loss_pct']*100:.1f}%")
        print(f"   Take Profit: {self.trading_params['take_profit_pct']*100:.1f}%")
        print(f"   Max Holding Period: {self.trading_params['max_holding_period']} hours")
        print(f"   Minimum Confidence: 80%")
        print("="*60)

        return trades_df

def main():
    parser = argparse.ArgumentParser(description='Generate trading signals using Cerberus Impulse Model')
    parser.add_argument('--csv', required=True, help='Path to CSV file with historical data')
    parser.add_argument('--symbol', default='UNKNOWN', help='Trading symbol/instrument name')
    parser.add_argument('--model', default='models/cerberus_model_relaxed.txt', help='Path to trained model file')
    parser.add_argument('--output', help='Output CSV file path (optional)')

    args = parser.parse_args()

    # Initialize signal generator
    generator = CerberusSignalGenerator(args.model)

    if generator.model is None:
        return

    # Load data
    df = generator.load_csv_data(args.csv, args.symbol)
    if df is None:
        return

    # Create features
    df_features = generator.create_features(df)
    if df_features is None:
        return

    # Generate signals
    signals_df = generator.generate_signals(df_features)
    if signals_df is None:
        return

    # Simulate trades
    trades = generator.simulate_trades(signals_df)

    # Generate report
    trades_df = generator.generate_report(signals_df, trades, args.output)

    print("\n🎯 Signal generation completed!")
    print("Use the generated CSV file for further analysis or automated trading.")

if __name__ == "__main__":
    main()