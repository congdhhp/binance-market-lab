"""
Market regime detection using Hidden Markov Models.
Identifies different market states (trending, ranging, volatile).
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects market regimes using Hidden Markov Models.
    
    Identifies 4 main regimes:
    - Trending Up: Positive returns, moderate volatility
    - Trending Down: Negative returns, moderate volatility
    - Ranging: Low returns, low volatility
    - High Volatility: High volatility regardless of direction
    """
    
    def __init__(self, n_regimes: int = 4):
        """
        Initialize regime detector.
        
        Args:
            n_regimes: Number of hidden states (default 4)
        """
        self.n_regimes = n_regimes
        self.model = None
        self.scaler = None  # Lazy loaded
        self.regime_labels = {
            0: 'Ranging',
            1: 'Trending Up',
            2: 'Trending Down',
            3: 'High Volatility'
        }
    
    def prepare_features(
        self,
        prices: np.ndarray,
        volumes: Optional[np.ndarray] = None,
        window: int = 20
    ) -> np.ndarray:
        """
        Prepare features for HMM.
        
        Features:
        - Returns (log returns)
        - Volatility (rolling std of returns)
        - Volume change (if provided)
        - Momentum (rate of change)
        
        Args:
            prices: Array of prices
            volumes: Optional array of volumes
            window: Window for rolling calculations
            
        Returns:
            Feature matrix (n_samples, n_features)
        """
        prices = np.array(prices)
        
        # Calculate returns
        returns = np.diff(np.log(prices))
        returns = np.append([0], returns)  # Prepend 0 for first value
        
        # Calculate rolling volatility
        volatility = pd.Series(returns).rolling(window=window, min_periods=5).std().fillna(0).values
        
        # Calculate momentum (rate of change)
        momentum = pd.Series(prices).pct_change(periods=window).fillna(0).values
        
        # Build feature matrix
        features = [returns, volatility, momentum]
        
        # Add volume change if provided
        if volumes is not None:
            volumes = np.array(volumes)
            volume_change = pd.Series(volumes).pct_change().fillna(0).values
            features.append(volume_change)
        
        feature_matrix = np.column_stack(features)
        
        return feature_matrix
    
    def fit(
        self,
        prices: np.ndarray,
        volumes: Optional[np.ndarray] = None,
        window: int = 20,
        n_iter: int = 100
    ):
        """
        Fit HMM to price data.
        
        Args:
            prices: Array of prices
            volumes: Optional array of volumes
            window: Window for feature calculation
            n_iter: Number of EM iterations for HMM
        """
        # Lazy import
        try:
            from hmmlearn import hmm
            from sklearn.preprocessing import StandardScaler
        except ImportError as e:
            logger.error(f"Required packages not installed: {e}")
            raise ImportError(
                "hmmlearn and scikit-learn are required for regime detection. "
                "Install with: pip install hmmlearn scikit-learn"
            )
        
        # Initialize scaler if needed
        if self.scaler is None:
            self.scaler = StandardScaler()
        
        # Prepare features
        features = self.prepare_features(prices, volumes, window)
        
        # Standardize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Fit Gaussian HMM
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type='full',
            n_iter=n_iter,
            random_state=42
        )
        
        self.model.fit(features_scaled)
        
        logger.info(f"HMM fitted with {self.n_regimes} regimes")
    
    def predict(
        self,
        prices: np.ndarray,
        volumes: Optional[np.ndarray] = None,
        window: int = 20
    ) -> np.ndarray:
        """
        Predict market regimes.
        
        Args:
            prices: Array of prices
            volumes: Optional array of volumes
            window: Window for feature calculation
            
        Returns:
            Array of regime labels (0 to n_regimes-1)
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Prepare features
        features = self.prepare_features(prices, volumes, window)
        
        # Standardize features
        features_scaled = self.scaler.transform(features)
        
        # Predict regimes
        regimes = self.model.predict(features_scaled)
        
        return regimes
    
    def predict_proba(
        self,
        prices: np.ndarray,
        volumes: Optional[np.ndarray] = None,
        window: int = 20
    ) -> np.ndarray:
        """
        Predict regime probabilities.
        
        Args:
            prices: Array of prices
            volumes: Optional array of volumes
            window: Window for feature calculation
            
        Returns:
            Array of probabilities (n_samples, n_regimes)
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Prepare features
        features = self.prepare_features(prices, volumes, window)
        
        # Standardize features
        features_scaled = self.scaler.transform(features)
        
        # Predict probabilities
        log_proba = self.model.score_samples(features_scaled)
        proba = np.exp(log_proba)
        
        return proba
    
    def label_regimes(
        self,
        regimes: np.ndarray,
        returns: np.ndarray,
        volatility: np.ndarray
    ) -> List[str]:
        """
        Label regimes based on characteristics.
        
        Args:
            regimes: Array of regime numbers
            returns: Array of returns
            volatility: Array of volatility
            
        Returns:
            List of regime labels
        """
        # Calculate mean characteristics for each regime
        regime_stats = {}
        
        for regime_id in range(self.n_regimes):
            mask = regimes == regime_id
            if np.sum(mask) == 0:
                continue
            
            regime_stats[regime_id] = {
                'mean_return': np.mean(returns[mask]),
                'mean_volatility': np.mean(volatility[mask])
            }
        
        # Assign labels based on characteristics
        labels = []
        
        for regime_id in range(self.n_regimes):
            if regime_id not in regime_stats:
                labels.append('Unknown')
                continue
            
            stats = regime_stats[regime_id]
            mean_ret = stats['mean_return']
            mean_vol = stats['mean_volatility']
            
            # Thresholds (can be adjusted)
            high_vol_threshold = np.percentile(volatility, 75)
            
            if mean_vol > high_vol_threshold:
                label = 'High Volatility'
            elif mean_ret > 0.001:  # Positive returns
                label = 'Trending Up'
            elif mean_ret < -0.001:  # Negative returns
                label = 'Trending Down'
            else:
                label = 'Ranging'
            
            labels.append(label)
        
        return labels
    
    def analyze_regime_transitions(self, regimes: np.ndarray) -> Dict:
        """
        Analyze regime transition patterns.
        
        Args:
            regimes: Array of regime labels
            
        Returns:
            Dictionary with transition analysis
        """
        # Transition matrix
        transition_matrix = np.zeros((self.n_regimes, self.n_regimes))
        
        for i in range(len(regimes) - 1):
            current_regime = regimes[i]
            next_regime = regimes[i + 1]
            transition_matrix[current_regime, next_regime] += 1
        
        # Normalize to probabilities
        row_sums = transition_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        transition_probs = transition_matrix / row_sums
        
        # Regime durations
        regime_durations = {}
        current_regime = regimes[0]
        current_duration = 1
        
        for regime in regimes[1:]:
            if regime == current_regime:
                current_duration += 1
            else:
                if current_regime not in regime_durations:
                    regime_durations[current_regime] = []
                regime_durations[current_regime].append(current_duration)
                
                current_regime = regime
                current_duration = 1
        
        # Add last duration
        if current_regime not in regime_durations:
            regime_durations[current_regime] = []
        regime_durations[current_regime].append(current_duration)
        
        # Calculate average durations
        avg_durations = {
            regime: np.mean(durations)
            for regime, durations in regime_durations.items()
        }
        
        return {
            'transition_matrix': transition_matrix.tolist(),
            'transition_probabilities': transition_probs.tolist(),
            'regime_durations': {int(k): v for k, v in regime_durations.items()},
            'average_durations': {int(k): float(v) for k, v in avg_durations.items()}
        }
    
    def get_current_regime(
        self,
        prices: np.ndarray,
        volumes: Optional[np.ndarray] = None,
        window: int = 20
    ) -> Dict:
        """
        Get current market regime and probabilities.
        
        Args:
            prices: Array of prices
            volumes: Optional array of volumes
            window: Window for feature calculation
            
        Returns:
            Dictionary with current regime info
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Predict regimes
        regimes = self.predict(prices, volumes, window)
        
        # Get current regime
        current_regime = int(regimes[-1])
        
        # Prepare features for probability
        features = self.prepare_features(prices, volumes, window)
        features_scaled = self.scaler.transform(features)
        
        # Get state probabilities for last observation
        # Using forward algorithm
        log_prob, posteriors = self.model.score_samples(features_scaled[-1:])
        current_probs = posteriors[0].tolist()
        
        # Calculate returns and volatility for labeling
        returns = np.diff(np.log(prices))
        volatility = pd.Series(returns).rolling(window=window, min_periods=5).std().fillna(0).values
        
        # Label regimes
        regime_labels = self.label_regimes(regimes, returns, volatility)
        
        return {
            'regime_id': current_regime,
            'regime_label': regime_labels[current_regime] if current_regime < len(regime_labels) else 'Unknown',
            'probabilities': {
                regime_labels[i] if i < len(regime_labels) else f'Regime {i}': prob
                for i, prob in enumerate(current_probs)
            },
            'all_regimes': regimes.tolist(),
            'regime_labels': regime_labels
        }


def detect_market_regime(
    prices: np.ndarray,
    volumes: Optional[np.ndarray] = None,
    n_regimes: int = 4,
    window: int = 20
) -> Dict:
    """
    Convenience function to detect market regimes.
    
    Args:
        prices: Array of prices
        volumes: Optional array of volumes
        n_regimes: Number of regimes
        window: Window for feature calculation
        
    Returns:
        Dictionary with regime detection results
    """
    detector = RegimeDetector(n_regimes=n_regimes)
    
    # Fit model
    detector.fit(prices, volumes, window)
    
    # Get current regime
    current_regime = detector.get_current_regime(prices, volumes, window)
    
    # Analyze transitions
    regimes = detector.predict(prices, volumes, window)
    transition_analysis = detector.analyze_regime_transitions(regimes)
    
    return {
        'current_regime': current_regime,
        'transition_analysis': transition_analysis,
        'model_parameters': {
            'n_regimes': n_regimes,
            'window': window,
            'n_observations': len(prices)
        }
    }
