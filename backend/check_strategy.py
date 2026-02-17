from apps.backtest.models import Strategy, BacktestRun, Trade

# Check strategy settings
strategy = Strategy.objects.get(name__icontains='RSI Moderate')
print(f"Strategy: {strategy.name}")
print(f"Type: {strategy.strategy_type}")
print(f"Parameters: {strategy.parameters}")
print(f"Stop Loss: {strategy.stop_loss_pct}%")
print(f"Take Profit: {strategy.take_profit_pct}%")
print(f"Position Size: {strategy.position_size}")
print()

# Check sample trades to see the pattern
run = BacktestRun.objects.get(id=3)
trades = Trade.objects.filter(backtest_run=run).order_by('entry_time')[:10]

print(f"First 10 trades from Run #{run.id}:")
for i, trade in enumerate(trades, 1):
    entry_exit_same = trade.entry_time == trade.exit_time
    print(f"{i}. {trade.side.upper()} - Entry: {trade.entry_time} -> Exit: {trade.exit_time}")
    print(f"   Same timestamp: {entry_exit_same}, Exit reason: {trade.exit_reason}")
    print(f"   PnL: ${trade.pnl}")
    print()
