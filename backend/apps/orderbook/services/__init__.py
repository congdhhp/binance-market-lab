"""
Orderbook analysis service.
Computes metrics from orderbook snapshots.
"""
import logging
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from apps.market_data.models import OrderBookSnapshot
from apps.orderbook.models import OrderbookAnalysis, ImbalanceAlert

logger = logging.getLogger(__name__)


class OrderbookAnalyzer:
    """
    Analyzes orderbook snapshots and computes metrics.
    """
    
    def __init__(self, snapshot: OrderBookSnapshot):
        self.snapshot = snapshot
        self.symbol = snapshot.symbol
        self.timestamp = snapshot.timestamp
        self.bids = snapshot.bids  # [[price, qty], ...]
        self.asks = snapshot.asks
    
    def analyze(self, levels: int = 10) -> OrderbookAnalysis:
        """
        Perform complete orderbook analysis.
        
        Args:
            levels: Number of price levels to analyze
            
        Returns:
            OrderbookAnalysis instance
        """
        # Extract top N levels
        top_bids = self.bids[:levels] if isinstance(self.bids, list) else []
        top_asks = self.asks[:levels] if isinstance(self.asks, list) else []
        
        if not top_bids or not top_asks:
            logger.warning(f"Empty orderbook for {self.symbol.name} at {self.timestamp}")
            return self._create_empty_analysis()
        
        # Parse prices and quantities
        bid_price = Decimal(str(top_bids[0][0]))
        ask_price = Decimal(str(top_asks[0][0]))
        
        # Calculate spread
        mid_price = (bid_price + ask_price) / 2
        spread_absolute = ask_price - bid_price
        spread_bps = (spread_absolute / mid_price) * Decimal('10000')  # basis points
        
        # Calculate depth
        bid_depth = sum(Decimal(str(bid[1])) for bid in top_bids)
        ask_depth = sum(Decimal(str(ask[1])) for ask in top_asks)
        total_depth = bid_depth + ask_depth
        
        # Calculate imbalance
        imbalance_ratio = bid_depth / total_depth if total_depth > 0 else Decimal('0.5')
        imbalance_pct = ((bid_depth - ask_depth) / total_depth * 100) if total_depth > 0 else Decimal('0')
        
        # Estimate VWAP for fixed quote amount
        vwap_buy = self._calculate_vwap(top_asks, Decimal('1000'), is_buy=True)
        vwap_sell = self._calculate_vwap(top_bids, Decimal('1000'), is_buy=False)
        
        # Liquidity score (0-100)
        liquidity_score = self._calculate_liquidity_score(
            spread_bps, bid_depth, ask_depth, levels
        )
        
        # Detect liquidity holes
        has_liquidity_hole = self._detect_liquidity_holes(top_bids, top_asks)
        
        # Create analysis record
        analysis = OrderbookAnalysis.objects.create(
            symbol=self.symbol,
            timestamp=self.timestamp,
            bid_price=bid_price,
            ask_price=ask_price,
            mid_price=mid_price,
            spread_absolute=spread_absolute,
            spread_bps=spread_bps,
            bid_depth_10=bid_depth,
            ask_depth_10=ask_depth,
            total_depth_10=total_depth,
            imbalance_ratio=imbalance_ratio,
            imbalance_pct=imbalance_pct,
            vwap_buy_1000=vwap_buy,
            vwap_sell_1000=vwap_sell,
            liquidity_score=liquidity_score,
            has_liquidity_hole=has_liquidity_hole,
            levels_analyzed=levels,
        )
        
        # Check for imbalance alerts
        self._check_imbalance_alerts(imbalance_ratio, bid_depth, ask_depth)
        
        return analysis
    
    def _calculate_vwap(
        self, 
        orders: List, 
        quote_amount: Decimal, 
        is_buy: bool
    ) -> Optional[Decimal]:
        """
        Calculate VWAP for executing a market order of given quote amount.
        
        Args:
            orders: List of [price, qty]
            quote_amount: Dollar amount to trade
            is_buy: True for buy, False for sell
            
        Returns:
            VWAP price or None
        """
        total_base = Decimal('0')
        total_quote = Decimal('0')
        
        for price_str, qty_str in orders:
            price = Decimal(str(price_str))
            qty = Decimal(str(qty_str))
            
            quote_value = price * qty
            
            if total_quote + quote_value >= quote_amount:
                # Partially fill this level
                remaining_quote = quote_amount - total_quote
                partial_qty = remaining_quote / price
                total_base += partial_qty
                total_quote += remaining_quote
                break
            else:
                # Fully fill this level
                total_base += qty
                total_quote += quote_value
        
        if total_base == 0:
            return None
        
        vwap = total_quote / total_base
        return vwap
    
    def _calculate_liquidity_score(
        self,
        spread_bps: Decimal,
        bid_depth: Decimal,
        ask_depth: Decimal,
        levels: int
    ) -> Decimal:
        """
        Calculate composite liquidity score (0-100).
        
        Higher score = better liquidity
        Factors: tight spread, high depth, balanced book
        """
        # Spread component (0-40 points)
        # Lower spread = higher score
        spread_score = max(Decimal('0'), Decimal('40') - spread_bps * 2)
        spread_score = min(spread_score, Decimal('40'))
        
        # Depth component (0-40 points)
        # Log scale: depth > $10k = 40, $1k = 20, $100 = 10
        if self.snapshot.bids:
            best_bid_price = Decimal(str(self.snapshot.bids[0][0]))
            total_depth_usd = (bid_depth + ask_depth) * best_bid_price
        else:
            total_depth_usd = Decimal('0')
            
        if total_depth_usd > 0:
            import math
            depth_score = Decimal(str(min(40, math.log10(float(total_depth_usd)) * 10)))
        else:
            depth_score = Decimal('0')
        
        # Balance component (0-20 points)
        # Perfectly balanced = 20, heavily imbalanced = 0
        imbalance = abs(bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else Decimal('1')
        balance_score = Decimal('20') * (Decimal('1') - imbalance)
        
        total_score = spread_score + depth_score + balance_score
        return min(total_score, Decimal('100'))
    
    def _detect_liquidity_holes(self, bids: List, asks: List) -> bool:
        """
        Detect large gaps in orderbook (liquidity holes).
        
        A hole is detected if price difference between consecutive levels
        exceeds 2x the typical spread.
        """
        if len(bids) < 2 or len(asks) < 2:
            return False
        
        # Calculate typical spread (top level)
        typical_spread = Decimal(str(asks[0][0])) - Decimal(str(bids[0][0]))
        hole_threshold = typical_spread * 2
        
        # Check bids
        for i in range(len(bids) - 1):
            price_gap = Decimal(str(bids[i][0])) - Decimal(str(bids[i+1][0]))
            if price_gap > hole_threshold:
                return True
        
        # Check asks
        for i in range(len(asks) - 1):
            price_gap = Decimal(str(asks[i+1][0])) - Decimal(str(asks[i][0]))
            if price_gap > hole_threshold:
                return True
        
        return False
    
    def _check_imbalance_alerts(
        self,
        imbalance_ratio: Decimal,
        bid_depth: Decimal,
        ask_depth: Decimal
    ):
        """
        Check if imbalance exceeds thresholds and create alerts.
        
        Thresholds:
        - High bid pressure: imbalance_ratio > 0.70
        - High ask pressure: imbalance_ratio < 0.30
        - Extreme: > 0.80 or < 0.20
        """
        alerts = []
        
        # High bid pressure
        if imbalance_ratio > Decimal('0.70'):
            severity = 'high' if imbalance_ratio > Decimal('0.80') else 'medium'
            alert_type = 'extreme_imbalance' if imbalance_ratio > Decimal('0.80') else 'high_bid_pressure'
            
            alerts.append({
                'alert_type': alert_type,
                'severity': severity,
                'threshold_value': Decimal('0.70') if severity == 'medium' else Decimal('0.80'),
                'message': f"Strong buying pressure detected. Bid/Ask ratio: {imbalance_ratio:.2f}"
            })
        
        # High ask pressure
        elif imbalance_ratio < Decimal('0.30'):
            severity = 'high' if imbalance_ratio < Decimal('0.20') else 'medium'
            alert_type = 'extreme_imbalance' if imbalance_ratio < Decimal('0.20') else 'high_ask_pressure'
            
            alerts.append({
                'alert_type': alert_type,
                'severity': severity,
                'threshold_value': Decimal('0.30') if severity == 'medium' else Decimal('0.20'),
                'message': f"Strong selling pressure detected. Bid/Ask ratio: {imbalance_ratio:.2f}"
            })
        
        # Create alert records
        for alert_data in alerts:
            ImbalanceAlert.objects.create(
                symbol=self.symbol,
                timestamp=self.timestamp,
                imbalance_ratio=imbalance_ratio,
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                **alert_data
            )
    
    def _create_empty_analysis(self) -> OrderbookAnalysis:
        """Create placeholder analysis for empty orderbook."""
        return OrderbookAnalysis.objects.create(
            symbol=self.symbol,
            timestamp=self.timestamp,
            bid_price=Decimal('0'),
            ask_price=Decimal('0'),
            mid_price=Decimal('0'),
            spread_absolute=Decimal('0'),
            spread_bps=Decimal('0'),
            bid_depth_10=Decimal('0'),
            ask_depth_10=Decimal('0'),
            total_depth_10=Decimal('0'),
            imbalance_ratio=Decimal('0.5'),
            imbalance_pct=Decimal('0'),
            liquidity_score=Decimal('0'),
            has_liquidity_hole=False,
            levels_analyzed=0,
        )


def analyze_orderbook(snapshot: OrderBookSnapshot, levels: int = 10) -> OrderbookAnalysis:
    """
    Convenience function to analyze an orderbook snapshot.
    
    Args:
        snapshot: OrderBookSnapshot instance
        levels: Number of price levels to analyze
        
    Returns:
        OrderbookAnalysis instance
    """
    analyzer = OrderbookAnalyzer(snapshot)
    return analyzer.analyze(levels=levels)


# Export all
__all__ = [
    'OrderbookAnalyzer',
    'analyze_orderbook',
]

