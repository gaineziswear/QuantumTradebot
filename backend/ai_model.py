import asyncio
import os
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import ta
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from loguru import logger
import json

from config import settings
from database import async_session, AIModelMetrics, TradingLog

class TradingDataset(Dataset):
    """Custom PyTorch dataset for trading data"""
    
    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

class LSTMTradingModel(nn.Module):
    """LSTM-based neural network for trading predictions"""
    
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 2, dropout: float = 0.2):
        super(LSTMTradingModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        # Fully connected layers
        self.fc_layers = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, 1)  # Predict price movement
        )
        
        # Risk prediction head
        self.risk_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()  # Risk score between 0 and 1
        )
    
    def forward(self, x):
        batch_size = x.size(0)
        
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Use the last output
        last_output = attn_out[:, -1, :]
        
        # Predictions
        price_pred = self.fc_layers(last_output)
        risk_pred = self.risk_head(last_output)
        
        return price_pred, risk_pred

class AITradingModel:
    """Advanced AI trading model with ensemble methods and risk management"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.training_logs = []
        self.is_training = False
        self.model_version = "v1.0.0"
        
        # Model configuration
        self.sequence_length = 24  # 24 hours of data
        self.feature_columns = []
        self.target_column = 'price_change_pct'
        
        # Performance tracking
        self.training_metrics = {
            'loss_history': [],
            'val_loss_history': [],
            'accuracy_history': [],
            'current_epoch': 0,
            'total_epochs': 1000,
            'best_val_loss': float('inf'),
            'training_start_time': None,
            'last_update': None
        }
    
    async def prepare_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Prepare features for training/prediction"""
        try:
            # Basic price features
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            df['price_change_pct'] = df['close'].pct_change()
            
            # Technical indicators
            df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
            df['macd'] = ta.trend.MACD(df['close']).macd()
            df['macd_signal'] = ta.trend.MACD(df['close']).macd_signal()
            df['macd_histogram'] = ta.trend.MACD(df['close']).macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'])
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Moving averages
            for window in [5, 10, 20, 50]:
                df[f'sma_{window}'] = ta.trend.SMAIndicator(df['close'], window=window).sma_indicator()
                df[f'ema_{window}'] = ta.trend.EMAIndicator(df['close'], window=window).ema_indicator()
                df[f'price_sma_{window}_ratio'] = df['close'] / df[f'sma_{window}']
            
            # Volume indicators
            df['volume_sma'] = ta.volume.VolumeSMAIndicator(df['close'], df['volume']).volume_sma()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Volatility indicators
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            df['volatility'] = df['returns'].rolling(window=20).std()
            
            # Price position features
            df['high_low_pct'] = (df['high'] - df['low']) / df['close']
            df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
            
            # Lag features
            for lag in [1, 2, 3, 6, 12]:
                df[f'price_lag_{lag}'] = df['close'].shift(lag)
                df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
                df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            
            # Rolling statistics
            for window in [5, 10, 20]:
                df[f'returns_mean_{window}'] = df['returns'].rolling(window=window).mean()
                df[f'returns_std_{window}'] = df['returns'].rolling(window=window).std()
                df[f'volume_mean_{window}'] = df['volume'].rolling(window=window).mean()
                df[f'volume_std_{window}'] = df['volume'].rolling(window=window).std()
            
            # Time-based features
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # Target: future price movement
            df['target'] = df['close'].shift(-1) / df['close'] - 1  # Next period return
            
            # Drop rows with NaN values
            df = df.dropna()
            
            self.feature_columns = [col for col in df.columns if col not in ['timestamp', 'target', 'open', 'high', 'low', 'close', 'volume']]
            
            return df
        
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            raise
    
    def create_sequences(self, data: np.ndarray, targets: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []
        
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(targets[i])
        
        return np.array(X), np.array(y)
    
    async def train_model(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Train the AI model with market data"""
        try:
            self.is_training = True
            self.training_metrics['training_start_time'] = datetime.utcnow()
            
            logger.info("Starting AI model training...")
            await self._log_training_event("INFO", "Starting model training", {"symbols": list(market_data.keys())})
            
            # Combine data from all symbols
            all_features = []
            all_targets = []
            
            for symbol, df in market_data.items():
                logger.info(f"Processing data for {symbol}")
                
                # Prepare features
                processed_df = await self.prepare_features(df, symbol)
                
                if len(processed_df) < self.sequence_length + 10:
                    logger.warning(f"Insufficient data for {symbol}, skipping")
                    continue
                
                # Scale features
                if symbol not in self.scalers:
                    self.scalers[symbol] = StandardScaler()
                
                features = processed_df[self.feature_columns].values
                targets = processed_df['target'].values
                
                # Fit scaler and transform
                features_scaled = self.scalers[symbol].fit_transform(features)
                
                # Create sequences
                X_seq, y_seq = self.create_sequences(features_scaled, targets)
                
                if len(X_seq) > 0:
                    all_features.append(X_seq)
                    all_targets.append(y_seq)
            
            if not all_features:
                raise ValueError("No valid training data available")
            
            # Combine all data
            X_combined = np.vstack(all_features)
            y_combined = np.hstack(all_targets)
            
            logger.info(f"Training with {len(X_combined)} sequences, {X_combined.shape[2]} features")
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X_combined, y_combined, test_size=0.2, random_state=42
            )
            
            # Create datasets
            train_dataset = TradingDataset(X_train, y_train)
            val_dataset = TradingDataset(X_val, y_val)
            
            train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
            
            # Initialize model
            input_size = X_combined.shape[2]
            self.models['lstm'] = LSTMTradingModel(input_size=input_size).to(self.device)
            
            # Loss function and optimizer
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.models['lstm'].parameters(), lr=0.001, weight_decay=1e-5)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=10, factor=0.5)
            
            # Training loop
            for epoch in range(self.training_metrics['total_epochs']):
                self.training_metrics['current_epoch'] = epoch
                
                # Training phase
                self.models['lstm'].train()
                train_loss = 0.0
                train_predictions = []
                train_actuals = []
                
                for batch_features, batch_targets in train_loader:
                    batch_features = batch_features.to(self.device)
                    batch_targets = batch_targets.to(self.device)
                    
                    optimizer.zero_grad()
                    
                    price_pred, risk_pred = self.models['lstm'](batch_features)
                    loss = criterion(price_pred.squeeze(), batch_targets)
                    
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.models['lstm'].parameters(), max_norm=1.0)
                    optimizer.step()
                    
                    train_loss += loss.item()
                    train_predictions.extend(price_pred.squeeze().detach().cpu().numpy())
                    train_actuals.extend(batch_targets.detach().cpu().numpy())
                
                train_loss /= len(train_loader)
                
                # Validation phase
                self.models['lstm'].eval()
                val_loss = 0.0
                val_predictions = []
                val_actuals = []
                
                with torch.no_grad():
                    for batch_features, batch_targets in val_loader:
                        batch_features = batch_features.to(self.device)
                        batch_targets = batch_targets.to(self.device)
                        
                        price_pred, risk_pred = self.models['lstm'](batch_features)
                        loss = criterion(price_pred.squeeze(), batch_targets)
                        
                        val_loss += loss.item()
                        val_predictions.extend(price_pred.squeeze().detach().cpu().numpy())
                        val_actuals.extend(batch_targets.detach().cpu().numpy())
                
                val_loss /= len(val_loader)
                
                # Calculate metrics
                train_r2 = r2_score(train_actuals, train_predictions)
                val_r2 = r2_score(val_actuals, val_predictions)
                
                # Update metrics
                self.training_metrics['loss_history'].append(train_loss)
                self.training_metrics['val_loss_history'].append(val_loss)
                self.training_metrics['accuracy_history'].append(val_r2)
                self.training_metrics['last_update'] = datetime.utcnow()
                
                scheduler.step(val_loss)
                
                # Save best model
                if val_loss < self.training_metrics['best_val_loss']:
                    self.training_metrics['best_val_loss'] = val_loss
                    await self._save_model()
                
                # Log progress
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}: Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}, Val R²: {val_r2:.6f}")
                    await self._log_training_event("INFO", f"Epoch {epoch} completed", {
                        "train_loss": train_loss,
                        "val_loss": val_loss,
                        "val_r2": val_r2
                    })
                
                # Early stopping
                if epoch > 50 and val_loss > self.training_metrics['best_val_loss'] * 1.1:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            # Train ensemble models
            await self._train_ensemble_models(X_train.reshape(X_train.shape[0], -1), y_train)
            
            # Save final metrics
            await self._save_training_metrics()
            
            self.is_training = False
            
            result = {
                "status": "completed",
                "final_train_loss": train_loss,
                "final_val_loss": val_loss,
                "final_accuracy": val_r2,
                "epochs_trained": epoch + 1,
                "model_version": self.model_version
            }
            
            logger.info("Model training completed successfully")
            await self._log_training_event("INFO", "Model training completed", result)
            
            return result
        
        except Exception as e:
            self.is_training = False
            logger.error(f"Error training model: {e}")
            await self._log_training_event("ERROR", f"Training failed: {str(e)}", {})
            raise
    
    async def _train_ensemble_models(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train ensemble models (Random Forest, Gradient Boosting)"""
        try:
            # Random Forest
            self.models['rf'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.models['rf'].fit(X_train, y_train)
            
            # Gradient Boosting
            self.models['gb'] = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.models['gb'].fit(X_train, y_train)
            
            logger.info("Ensemble models trained successfully")
        
        except Exception as e:
            logger.error(f"Error training ensemble models: {e}")
            raise
    
    async def predict(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Make predictions using the trained models"""
        try:
            predictions = {}
            
            for symbol, df in market_data.items():
                if symbol not in self.scalers or 'lstm' not in self.models:
                    continue
                
                # Prepare features
                processed_df = await self.prepare_features(df, symbol)
                
                if len(processed_df) < self.sequence_length:
                    continue
                
                # Get last sequence
                features = processed_df[self.feature_columns].values
                features_scaled = self.scalers[symbol].transform(features)
                
                # Create sequence for LSTM
                if len(features_scaled) >= self.sequence_length:
                    lstm_input = features_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
                    lstm_input = torch.FloatTensor(lstm_input).to(self.device)
                    
                    self.models['lstm'].eval()
                    with torch.no_grad():
                        price_pred, risk_pred = self.models['lstm'](lstm_input)
                        lstm_prediction = price_pred.item()
                        risk_score = risk_pred.item()
                    
                    # Ensemble prediction
                    ensemble_input = features_scaled[-1:].reshape(1, -1)
                    rf_pred = self.models['rf'].predict(ensemble_input)[0] if 'rf' in self.models else 0
                    gb_pred = self.models['gb'].predict(ensemble_input)[0] if 'gb' in self.models else 0
                    
                    # Weighted ensemble
                    ensemble_pred = (lstm_prediction * 0.5 + rf_pred * 0.25 + gb_pred * 0.25)
                    
                    predictions[symbol] = {
                        'lstm_prediction': lstm_prediction,
                        'rf_prediction': rf_pred,
                        'gb_prediction': gb_pred,
                        'ensemble_prediction': ensemble_pred,
                        'risk_score': risk_score,
                        'confidence': 1 - risk_score,  # Inverse of risk as confidence
                        'timestamp': datetime.utcnow().isoformat()
                    }
            
            return predictions
        
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return {}
    
    async def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            'is_training': self.is_training,
            'current_epoch': self.training_metrics['current_epoch'],
            'total_epochs': self.training_metrics['total_epochs'],
            'progress_percentage': (self.training_metrics['current_epoch'] / self.training_metrics['total_epochs']) * 100,
            'current_loss': self.training_metrics['loss_history'][-1] if self.training_metrics['loss_history'] else None,
            'best_val_loss': self.training_metrics['best_val_loss'],
            'last_update': self.training_metrics['last_update'].isoformat() if self.training_metrics['last_update'] else None,
            'model_version': self.model_version,
            'feature_count': len(self.feature_columns),
            'model_confidence': 'High' if self.training_metrics['best_val_loss'] < 0.01 else 'Medium' if self.training_metrics['best_val_loss'] < 0.05 else 'Low'
        }
    
    async def get_training_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent training logs"""
        return self.training_logs[-limit:] if self.training_logs else []
    
    async def _log_training_event(self, level: str, message: str, metadata: Dict[str, Any]):
        """Log training event"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'component': 'AI_MODEL',
            'metadata': json.dumps(metadata)
        }
        
        self.training_logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self.training_logs) > 1000:
            self.training_logs = self.training_logs[-1000:]
    
    async def _save_model(self):
        """Save trained model to disk"""
        try:
            model_path = f"models/trading_model_{self.model_version}.pt"
            os.makedirs("models", exist_ok=True)
            
            if 'lstm' in self.models:
                torch.save({
                    'model_state_dict': self.models['lstm'].state_dict(),
                    'scalers': self.scalers,
                    'feature_columns': self.feature_columns,
                    'model_version': self.model_version,
                    'training_metrics': self.training_metrics
                }, model_path)
            
            # Save ensemble models
            if 'rf' in self.models:
                with open(f"models/rf_model_{self.model_version}.pkl", 'wb') as f:
                    pickle.dump(self.models['rf'], f)
            
            if 'gb' in self.models:
                with open(f"models/gb_model_{self.model_version}.pkl", 'wb') as f:
                    pickle.dump(self.models['gb'], f)
        
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    async def _save_training_metrics(self):
        """Save training metrics to database"""
        try:
            async with async_session() as session:
                metrics = AIModelMetrics(
                    model_version=self.model_version,
                    training_start=self.training_metrics['training_start_time'],
                    training_end=datetime.utcnow(),
                    training_loss=self.training_metrics['loss_history'][-1] if self.training_metrics['loss_history'] else None,
                    validation_loss=self.training_metrics['val_loss_history'][-1] if self.training_metrics['val_loss_history'] else None,
                    accuracy=self.training_metrics['accuracy_history'][-1] if self.training_metrics['accuracy_history'] else None,
                    data_points=len(self.training_metrics['loss_history']),
                    features_count=len(self.feature_columns),
                    is_active=True
                )
                session.add(metrics)
                await session.commit()
        
        except Exception as e:
            logger.error(f"Error saving training metrics to database: {e}")
