"""
Correlation analysis service.
Computes correlation matrices and PCA for portfolio analysis.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Analyzes correlations between multiple assets.
    """
    
    def __init__(self, returns_df: pd.DataFrame):
        """
        Initialize analyzer with returns data.
        
        Args:
            returns_df: DataFrame with columns as symbols and rows as timestamps
                       Values should be returns (price changes)
        """
        self.returns_df = returns_df
        self.symbols = list(returns_df.columns)
    
    def calculate_correlation_matrix(
        self,
        method: str = 'pearson',
        min_periods: int = 20
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix.
        
        Args:
            method: 'pearson', 'spearman', or 'kendall'
            min_periods: Minimum number of periods required
            
        Returns:
            Correlation matrix DataFrame
        """
        if len(self.returns_df) < min_periods:
            logger.warning(f"Insufficient data for correlation: {len(self.returns_df)} < {min_periods}")
            return pd.DataFrame()
        
        corr_matrix = self.returns_df.corr(method=method, min_periods=min_periods)
        
        return corr_matrix
    
    def calculate_rolling_correlation(
        self,
        symbol1: str,
        symbol2: str,
        window: int = 30,
        min_periods: int = 20
    ) -> pd.Series:
        """
        Calculate rolling correlation between two symbols.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            window: Rolling window size
            min_periods: Minimum periods required
            
        Returns:
            Series of rolling correlations
        """
        if symbol1 not in self.symbols or symbol2 not in self.symbols:
            logger.error(f"Symbols not found: {symbol1}, {symbol2}")
            return pd.Series()
        
        rolling_corr = self.returns_df[symbol1].rolling(
            window=window,
            min_periods=min_periods
        ).corr(self.returns_df[symbol2])
        
        return rolling_corr
    
    def calculate_correlation_heatmap_data(self, method: str = 'pearson') -> Dict:
        """
        Calculate correlation matrix in heatmap-ready format.
        
        Args:
            method: Correlation method
            
        Returns:
            Dictionary with heatmap data
        """
        corr_matrix = self.calculate_correlation_matrix(method)
        
        if corr_matrix.empty:
            return {'symbols': [], 'matrix': [], 'values': []}
        
        # Convert to list format for frontend
        symbols = list(corr_matrix.columns)
        matrix = corr_matrix.values.tolist()
        
        # Flatten for easy processing
        values = []
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                values.append({
                    'symbol1': symbol1,
                    'symbol2': symbol2,
                    'correlation': matrix[i][j]
                })
        
        return {
            'symbols': symbols,
            'matrix': matrix,
            'values': values
        }
    
    def find_highly_correlated_pairs(
        self,
        threshold: float = 0.7,
        method: str = 'pearson'
    ) -> List[Dict]:
        """
        Find pairs of symbols with high correlation.
        
        Args:
            threshold: Absolute correlation threshold
            method: Correlation method
            
        Returns:
            List of correlated pairs
        """
        corr_matrix = self.calculate_correlation_matrix(method)
        
        if corr_matrix.empty:
            return []
        
        pairs = []
        
        # Iterate through upper triangle only (avoid duplicates)
        for i in range(len(corr_matrix)):
            for j in range(i + 1, len(corr_matrix)):
                corr_value = corr_matrix.iloc[i, j]
                
                if abs(corr_value) >= threshold:
                    pairs.append({
                        'symbol1': corr_matrix.columns[i],
                        'symbol2': corr_matrix.columns[j],
                        'correlation': float(corr_value),
                        'relationship': 'positive' if corr_value > 0 else 'negative'
                    })
        
        # Sort by absolute correlation (descending)
        pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return pairs
    
    def perform_pca(
        self,
        n_components: Optional[int] = None,
        variance_threshold: float = 0.95
    ) -> Dict:
        """
        Perform Principal Component Analysis.
        
        Args:
            n_components: Number of components (None = auto based on variance)
            variance_threshold: Cumulative variance threshold for auto selection
            
        Returns:
            Dictionary with PCA results
        """
        # Lazy import
        try:
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
        except ImportError as e:
            logger.error(f"scikit-learn is required for PCA: {e}")
            return self._empty_pca_result()
        
        if self.returns_df.empty:
            return self._empty_pca_result()
        
        # Handle missing values
        data = self.returns_df.fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)
        
        # Fit PCA
        if n_components is None:
            pca = PCA()
            pca.fit(scaled_data)
            
            # Find components that explain variance_threshold of variance
            cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
            n_components = np.argmax(cumsum_variance >= variance_threshold) + 1
            
            # Refit with selected components
            pca = PCA(n_components=n_components)
            pca.fit(scaled_data)
        else:
            pca = PCA(n_components=n_components)
            pca.fit(scaled_data)
        
        # Transform data
        transformed = pca.transform(scaled_data)
        
        # Component loadings (how much each symbol contributes to each component)
        loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
        
        result = {
            'n_components': pca.n_components_,
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
            'cumulative_variance_ratio': np.cumsum(pca.explained_variance_ratio_).tolist(),
            'components': pca.components_.tolist(),
            'loadings': loadings.tolist(),
            'symbols': self.symbols,
            'transformed_data': transformed.tolist()
        }
        
        return result
    
    def detect_regime_changes(
        self,
        window: int = 90,
        threshold: float = 0.3
    ) -> List[Dict]:
        """
        Detect correlation regime changes.
        
        A regime change is detected when average correlation shifts significantly.
        
        Args:
            window: Rolling window for correlation calculation
            threshold: Change threshold to trigger regime change
            
        Returns:
            List of regime change events
        """
        if len(self.returns_df) < window * 2:
            return []
        
        # Calculate rolling average correlation (excluding diagonal)
        regime_changes = []
        
        for i in range(window, len(self.returns_df) - window, window // 2):
            # Calculate correlation for current window
            current_window = self.returns_df.iloc[i:i+window]
            current_corr = current_window.corr().values
            
            # Average off-diagonal correlations
            mask = ~np.eye(len(current_corr), dtype=bool)
            current_avg = np.mean(current_corr[mask])
            
            # Calculate correlation for previous window
            prev_window = self.returns_df.iloc[i-window:i]
            prev_corr = prev_window.corr().values
            prev_avg = np.mean(prev_corr[mask])
            
            # Check for significant change
            change = current_avg - prev_avg
            
            if abs(change) >= threshold:
                regime_changes.append({
                    'timestamp': self.returns_df.index[i],
                    'prev_correlation': float(prev_avg),
                    'current_correlation': float(current_avg),
                    'change': float(change),
                    'regime': 'high_correlation' if current_avg > 0.5 else 'low_correlation'
                })
        
        return regime_changes
    
    def calculate_diversification_ratio(self) -> float:
        """
        Calculate diversification ratio.
        
        Ratio of weighted average volatility to portfolio volatility.
        Higher ratio = better diversification.
        
        Returns:
            Diversification ratio
        """
        if self.returns_df.empty:
            return 0.0
        
        # Equal weights
        n_assets = len(self.symbols)
        weights = np.array([1.0 / n_assets] * n_assets)
        
        # Individual volatilities
        volatilities = self.returns_df.std().values
        
        # Weighted average volatility
        weighted_vol = np.sum(weights * volatilities)
        
        # Portfolio volatility
        cov_matrix = self.returns_df.cov().values
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        if portfolio_vol == 0:
            return 0.0
        
        diversification_ratio = weighted_vol / portfolio_vol
        
        return float(diversification_ratio)
    
    def _empty_pca_result(self) -> Dict:
        """Return empty PCA result."""
        return {
            'n_components': 0,
            'explained_variance_ratio': [],
            'cumulative_variance_ratio': [],
            'components': [],
            'loadings': [],
            'symbols': [],
            'transformed_data': []
        }


def analyze_correlation(
    returns_df: pd.DataFrame,
    method: str = 'pearson',
    min_periods: int = 20
) -> Dict:
    """
    Convenience function to perform correlation analysis.
    
    Args:
        returns_df: DataFrame with returns
        method: Correlation method
        min_periods: Minimum periods required
        
    Returns:
        Dictionary with correlation analysis results
    """
    analyzer = CorrelationAnalyzer(returns_df)
    
    corr_matrix = analyzer.calculate_correlation_matrix(method, min_periods)
    heatmap_data = analyzer.calculate_correlation_heatmap_data(method)
    high_corr_pairs = analyzer.find_highly_correlated_pairs(threshold=0.7, method=method)
    pca_result = analyzer.perform_pca()
    diversification = analyzer.calculate_diversification_ratio()
    
    return {
        'correlation_matrix': corr_matrix.to_dict() if not corr_matrix.empty else {},
        'heatmap_data': heatmap_data,
        'highly_correlated_pairs': high_corr_pairs,
        'pca_analysis': pca_result,
        'diversification_ratio': diversification,
    }
