"""
Signal Engine - Evaluates rules and generates trading signals.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from django.utils import timezone
from apps.analysis.models import Signal, SignalRule, IndicatorCache
from apps.market_data.models import Symbol

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Evaluates signal rules against indicator values and generates signals.
    """
    
    def __init__(self):
        self.rules = SignalRule.objects.filter(is_active=True).order_by('-priority')
    
    def evaluate_symbol(
        self,
        symbol: Symbol,
        interval: str,
        indicators: Dict[str, float],
        price: float
    ) -> List[Signal]:
        """
        Evaluate all rules for a symbol and generate signals.
        
        Args:
            symbol: Symbol instance
            interval: Time interval (e.g., '1h')
            indicators: Dict of indicator values
            price: Current price
            
        Returns:
            List of generated Signal objects (not saved)
        """
        generated_signals = []
        
        # Get applicable rules for this symbol and interval
        applicable_rules = self._get_applicable_rules(symbol, interval)
        
        for rule in applicable_rules:
            try:
                if rule.evaluate(indicators):
                    signal = Signal(
                        symbol=symbol,
                        timestamp=timezone.now(),
                        interval=interval,
                        signal_type=rule.signal_type,
                        strength=rule.strength,
                        rule=rule,
                        price_at_signal=price,
                        indicators_snapshot=indicators,
                        confidence=self._calculate_confidence(indicators, rule)
                    )
                    generated_signals.append(signal)
                    logger.info(
                        f"Signal generated: {symbol.name} {rule.signal_type} "
                        f"(rule: {rule.name}, strength: {rule.strength})"
                    )
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name} for {symbol.name}: {e}")
        
        return generated_signals
    
    def _get_applicable_rules(self, symbol: Symbol, interval: str) -> List[SignalRule]:
        """Get rules that apply to this symbol and interval."""
        applicable = []
        
        for rule in self.rules:
            # Check if rule has symbol restrictions
            if rule.symbols.exists() and symbol not in rule.symbols.all():
                continue
            
            # Check if rule has interval restrictions
            if rule.intervals and interval not in rule.intervals:
                continue
            
            applicable.append(rule)
        
        return applicable
    
    def _calculate_confidence(self, indicators: Dict[str, float], rule: SignalRule) -> float:
        """
        Calculate confidence score for a signal based on indicator alignment.
        
        Args:
            indicators: Current indicator values
            rule: Signal rule that was triggered
            
        Returns:
            Confidence score 0-100
        """
        confidence_factors = []
        
        # RSI confirmation
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rule.signal_type == 'buy' and rsi < 40:
                confidence_factors.append(80)
            elif rule.signal_type == 'sell' and rsi > 60:
                confidence_factors.append(80)
            else:
                confidence_factors.append(50)
        
        # MACD confirmation
        if 'macd' in indicators and 'macd_signal' in indicators:
            macd_diff = indicators['macd'] - indicators['macd_signal']
            if rule.signal_type == 'buy' and macd_diff > 0:
                confidence_factors.append(75)
            elif rule.signal_type == 'sell' and macd_diff < 0:
                confidence_factors.append(75)
            else:
                confidence_factors.append(50)
        
        # ADX trend strength
        if 'adx' in indicators:
            adx = indicators['adx']
            if adx > 25:  # Strong trend
                confidence_factors.append(85)
            elif adx > 20:
                confidence_factors.append(70)
            else:
                confidence_factors.append(50)
        
        # If no factors, return base confidence
        if not confidence_factors:
            return 60.0
        
        # Average of all factors
        return sum(confidence_factors) / len(confidence_factors)
    
    def generate_composite_signal(
        self,
        symbol: Symbol,
        interval: str,
        indicators: Dict[str, float],
        price: float
    ) -> Optional[Signal]:
        """
        Generate a composite signal by analyzing multiple indicators.
        This is a simple scoring system, can be enhanced with ML.
        
        Args:
            symbol: Symbol instance
            interval: Time interval
            indicators: Dict of indicator values
            price: Current price
            
        Returns:
            Single composite Signal or None
        """
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        
        # RSI scoring (weight: 20)
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            weight = 20
            if rsi < 30:
                bullish_score += weight
            elif rsi > 70:
                bearish_score += weight
            total_weight += weight
        
        # MACD scoring (weight: 25)
        if 'macd' in indicators and 'macd_signal' in indicators:
            macd = indicators['macd']
            macd_signal = indicators['macd_signal']
            weight = 25
            if macd > macd_signal:
                bullish_score += weight
            else:
                bearish_score += weight
            total_weight += weight
        
        # ADX + DI scoring (weight: 20)
        if 'adx' in indicators and 'adx_pos' in indicators and 'adx_neg' in indicators:
            adx = indicators['adx']
            di_plus = indicators['adx_pos']
            di_minus = indicators['adx_neg']
            
            if adx > 25:  # Strong trend
                weight = 20
                if di_plus > di_minus:
                    bullish_score += weight
                else:
                    bearish_score += weight
                total_weight += weight
        
        # Bollinger Bands scoring (weight: 15)
        if 'bb_high' in indicators and 'bb_low' in indicators:
            bb_high = indicators['bb_high']
            bb_low = indicators['bb_low']
            weight = 15
            
            if price < bb_low:
                bullish_score += weight
            elif price > bb_high:
                bearish_score += weight
            total_weight += weight
        
        # EMA trend scoring (weight: 20)
        if 'ema_21' in indicators and 'ema_50' in indicators:
            ema_21 = indicators['ema_21']
            ema_50 = indicators['ema_50']
            weight = 20
            
            if ema_21 > ema_50 and price > ema_21:
                bullish_score += weight
            elif ema_21 < ema_50 and price < ema_21:
                bearish_score += weight
            total_weight += weight
        
        # Calculate percentages
        if total_weight == 0:
            return None
        
        bullish_pct = (bullish_score / total_weight) * 100
        bearish_pct = (bearish_score / total_weight) * 100
        
        # Determine signal type and strength
        signal_type = None
        strength = 0
        
        if bullish_pct > 70:
            signal_type = 'strong_buy'
            strength = int(bullish_pct)
        elif bullish_pct > 50:
            signal_type = 'buy'
            strength = int(bullish_pct)
        elif bearish_pct > 70:
            signal_type = 'strong_sell'
            strength = int(bearish_pct)
        elif bearish_pct > 50:
            signal_type = 'sell'
            strength = int(bearish_pct)
        else:
            signal_type = 'neutral'
            strength = 50
        
        # Only generate signals for strong enough signals
        if strength < 55 and signal_type not in ['strong_buy', 'strong_sell']:
            return None
        
        signal = Signal(
            symbol=symbol,
            timestamp=timezone.now(),
            interval=interval,
            signal_type=signal_type,
            strength=strength,
            rule=None,  # Composite signal, no specific rule
            price_at_signal=price,
            indicators_snapshot=indicators,
            confidence=strength,
            notes=f"Composite signal (bullish: {bullish_pct:.1f}%, bearish: {bearish_pct:.1f}%)"
        )
        
        logger.info(
            f"Composite signal: {symbol.name} {signal_type} "
            f"(strength: {strength}, conf: {strength})"
        )
        
        return signal
    
    def cleanup_old_signals(self, days: int = 30) -> int:
        """
        Delete signals older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted signals
        """
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count, _ = Signal.objects.filter(
            timestamp__lt=cutoff_date,
            is_active=False
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old signals")
        return deleted_count
