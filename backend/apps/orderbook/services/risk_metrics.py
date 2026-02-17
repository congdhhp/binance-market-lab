"""
Risk metrics calculation service.
Computes VaR, volatility, Sharpe ratios, and other risk measures.
"""
import logging
import numpy as np
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import timedelta
from django.db.models import QuerySet
from django.utils import timezone
from scipy import stats

logger = logging.getLogger(__name__)


class RiskMetricsCalculator:
    """
    Calculates various risk metrics for trading strategies and portfolios.
    """
    
    def __init__(self, returns: np.ndarray, prices: Optional[np.ndarray] = None):
        """
        Initialize calculator with returns series.
        
        Args:
            returns: Array of returns (e.g., daily % changes)
            prices: Optional array of prices (for drawdown calculations)
        """
        self.returns = np.array(returns)
        self.prices = np.array(prices) if prices is not None else None
        
        if len(self.returns) == 0:
            logger.warning("Empty returns array provided")
    
    def calculate_all(
        self,
        confidence_level: float = 0.95,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 365
    ) -> Dict:
        """
        Calculate all risk metrics.
        
        Args:
            confidence_level: VaR confidence level (default 95%)
            risk_free_rate: Annual risk-free rate for Sharpe ratio
            periods_per_year: Trading periods per year (365 for daily)
            
        Returns:
            Dictionary of risk metrics
        """
        if len(self.returns) == 0:
            return self._empty_metrics()
        
        metrics = {
            # Volatility metrics
            'volatility_daily': self.calculate_volatility(),
            'volatility_annual': self.calculate_volatility(annualize=True, periods_per_year=periods_per_year),
            
            # VaR metrics
            'var_historical_95': self.calculate_var_historical(confidence_level),
            'var_parametric_95': self.calculate_var_parametric(confidence_level),
            'var_monte_carlo_95': self.calculate_var_monte_carlo(confidence_level),
            'cvar_95': self.calculate_cvar(confidence_level),
            
            # Performance ratios
            'sharpe_ratio': self.calculate_sharpe_ratio(risk_free_rate, periods_per_year),
            'sortino_ratio': self.calculate_sortino_ratio(risk_free_rate, periods_per_year),
            'calmar_ratio': self.calculate_calmar_ratio(periods_per_year),
            
            # Drawdown metrics
            'max_drawdown': self.calculate_max_drawdown(),
            'max_drawdown_duration': self.calculate_max_drawdown_duration(),
            
            # Distribution metrics
            'skewness': self.calculate_skewness(),
            'kurtosis': self.calculate_kurtosis(),
            
            # Summary stats
            'mean_return': float(np.mean(self.returns)),
            'median_return': float(np.median(self.returns)),
            'std_return': float(np.std(self.returns)),
            'min_return': float(np.min(self.returns)),
            'max_return': float(np.max(self.returns)),
        }
        
        return metrics
    
    def calculate_volatility(
        self,
        annualize: bool = False,
        periods_per_year: int = 365
    ) -> float:
        """
        Calculate volatility (standard deviation of returns).
        
        Args:
            annualize: Whether to annualize the volatility
            periods_per_year: Periods per year for annualization
            
        Returns:
            Volatility as float
        """
        vol = float(np.std(self.returns))
        
        if annualize:
            vol *= np.sqrt(periods_per_year)
        
        return vol
    
    def calculate_var_historical(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk using historical simulation.
        
        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            VaR as positive number (loss amount)
        """
        if len(self.returns) == 0:
            return 0.0
        
        percentile = (1 - confidence_level) * 100
        var = -np.percentile(self.returns, percentile)
        
        return float(var)
    
    def calculate_var_parametric(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk using parametric (variance-covariance) method.
        
        Assumes normal distribution of returns.
        
        Args:
            confidence_level: Confidence level
            
        Returns:
            VaR as positive number
        """
        if len(self.returns) == 0:
            return 0.0
        
        mean = np.mean(self.returns)
        std = np.std(self.returns)
        
        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # VaR = -(mean + z_score * std)
        var = -(mean + z_score * std)
        
        return float(var)
    
    def calculate_var_monte_carlo(
        self,
        confidence_level: float = 0.95,
        num_simulations: int = 10000,
        periods: int = 1
    ) -> float:
        """
        Calculate Value at Risk using Monte Carlo simulation.
        
        Args:
            confidence_level: Confidence level
            num_simulations: Number of simulation paths
            periods: Number of periods to simulate
            
        Returns:
            VaR as positive number
        """
        if len(self.returns) == 0:
            return 0.0
        
        mean = np.mean(self.returns)
        std = np.std(self.returns)
        
        # Simulate returns
        simulated_returns = np.random.normal(
            mean * periods,
            std * np.sqrt(periods),
            num_simulations
        )
        
        # Calculate VaR from simulations
        percentile = (1 - confidence_level) * 100
        var = -np.percentile(simulated_returns, percentile)
        
        return float(var)
    
    def calculate_cvar(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall).
        
        Average loss beyond VaR threshold.
        
        Args:
            confidence_level: Confidence level
            
        Returns:
            CVaR as positive number
        """
        if len(self.returns) == 0:
            return 0.0
        
        var = self.calculate_var_historical(confidence_level)
        
        # Losses beyond VaR
        losses = self.returns[self.returns <= -var]
        
        if len(losses) == 0:
            return var
        
        cvar = -np.mean(losses)
        
        return float(cvar)
    
    def calculate_sharpe_ratio(
        self,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 365
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        (Mean return - Risk free rate) / Volatility
        
        Args:
            risk_free_rate: Annual risk-free rate
            periods_per_year: Periods per year
            
        Returns:
            Sharpe ratio
        """
        if len(self.returns) == 0:
            return 0.0
        
        # Convert annual risk-free rate to period rate
        period_rf_rate = risk_free_rate / periods_per_year
        
        mean_return = np.mean(self.returns)
        vol = np.std(self.returns)
        
        if vol == 0:
            return 0.0
        
        sharpe = (mean_return - period_rf_rate) / vol
        
        # Annualize
        sharpe *= np.sqrt(periods_per_year)
        
        return float(sharpe)
    
    def calculate_sortino_ratio(
        self,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 365
    ) -> float:
        """
        Calculate Sortino ratio.
        
        Like Sharpe, but only considers downside volatility.
        
        Args:
            risk_free_rate: Annual risk-free rate
            periods_per_year: Periods per year
            
        Returns:
            Sortino ratio
        """
        if len(self.returns) == 0:
            return 0.0
        
        period_rf_rate = risk_free_rate / periods_per_year
        
        mean_return = np.mean(self.returns)
        
        # Downside deviation (only negative returns)
        negative_returns = self.returns[self.returns < 0]
        
        if len(negative_returns) == 0:
            return float('inf')
        
        downside_vol = np.std(negative_returns)
        
        if downside_vol == 0:
            return 0.0
        
        sortino = (mean_return - period_rf_rate) / downside_vol
        
        # Annualize
        sortino *= np.sqrt(periods_per_year)
        
        return float(sortino)
    
    def calculate_calmar_ratio(self, periods_per_year: int = 365) -> float:
        """
        Calculate Calmar ratio.
        
        Annual return / Max drawdown
        
        Args:
            periods_per_year: Periods per year
            
        Returns:
            Calmar ratio
        """
        if len(self.returns) == 0 or self.prices is None:
            return 0.0
        
        # Annualized return
        total_return = (self.prices[-1] / self.prices[0]) - 1
        periods = len(self.returns)
        annual_return = ((1 + total_return) ** (periods_per_year / periods)) - 1
        
        # Max drawdown
        max_dd = self.calculate_max_drawdown()
        
        if max_dd == 0:
            return 0.0
        
        calmar = annual_return / abs(max_dd)
        
        return float(calmar)
    
    def calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown from peak.
        
        Returns:
            Max drawdown as negative percentage
        """
        if self.prices is None or len(self.prices) == 0:
            return 0.0
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(self.prices)
        
        # Calculate drawdowns
        drawdowns = (self.prices - running_max) / running_max
        
        max_dd = np.min(drawdowns)
        
        return float(max_dd)
    
    def calculate_max_drawdown_duration(self) -> int:
        """
        Calculate longest drawdown duration in periods.
        
        Returns:
            Number of periods
        """
        if self.prices is None or len(self.prices) == 0:
            return 0
        
        running_max = np.maximum.accumulate(self.prices)
        
        # Find periods where price equals running max (new highs)
        new_highs = self.prices >= running_max
        
        # Calculate duration between new highs
        max_duration = 0
        current_duration = 0
        
        for is_new_high in new_highs:
            if is_new_high:
                max_duration = max(max_duration, current_duration)
                current_duration = 0
            else:
                current_duration += 1
        
        max_duration = max(max_duration, current_duration)
        
        return int(max_duration)
    
    def calculate_skewness(self) -> float:
        """
        Calculate skewness of returns distribution.
        
        Positive skew = tail on right (occasional large gains)
        Negative skew = tail on left (occasional large losses)
        
        Returns:
            Skewness value
        """
        if len(self.returns) < 3:
            return 0.0
        
        return float(stats.skew(self.returns))
    
    def calculate_kurtosis(self) -> float:
        """
        Calculate kurtosis of returns distribution.
        
        High kurtosis = fat tails (extreme events more likely)
        
        Returns:
            Excess kurtosis value
        """
        if len(self.returns) < 4:
            return 0.0
        
        return float(stats.kurtosis(self.returns))
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics dictionary."""
        return {
            'volatility_daily': 0.0,
            'volatility_annual': 0.0,
            'var_historical_95': 0.0,
            'var_parametric_95': 0.0,
            'var_monte_carlo_95': 0.0,
            'cvar_95': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_duration': 0,
            'skewness': 0.0,
            'kurtosis': 0.0,
            'mean_return': 0.0,
            'median_return': 0.0,
            'std_return': 0.0,
            'min_return': 0.0,
            'max_return': 0.0,
        }


def calculate_portfolio_risk(
    returns: np.ndarray,
    prices: Optional[np.ndarray] = None,
    confidence_level: float = 0.95,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 365
) -> Dict:
    """
    Convenience function to calculate all risk metrics.
    
    Args:
        returns: Array of returns
        prices: Optional array of prices
        confidence_level: VaR confidence level
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year
        
    Returns:
        Dictionary of risk metrics
    """
    calculator = RiskMetricsCalculator(returns, prices)
    return calculator.calculate_all(confidence_level, risk_free_rate, periods_per_year)
