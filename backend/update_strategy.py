from apps.backtest.models import Strategy
from decimal import Decimal

# Update strategy with more realistic parameters
strategy = Strategy.objects.get(name__icontains='RSI Moderate')

print(f"Current settings:")
print(f"  Stop Loss: {strategy.stop_loss_pct}%")
print(f"  Take Profit: {strategy.take_profit_pct}%")
print(f"  Position Size: {strategy.position_size}")
print()

# Update to more reasonable values
strategy.stop_loss_pct = Decimal('1.0')  # 1% instead of 0.03%
strategy.take_profit_pct = Decimal('1.5')  # 1.5% instead of 0.06%
strategy.save()

print(f"Updated settings:")
print(f"  Stop Loss: {strategy.stop_loss_pct}%")
print(f"  Take Profit: {strategy.take_profit_pct}%")
print(f"  Position Size: {strategy.position_size}")
