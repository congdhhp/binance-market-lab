from apps.backtest.models import Strategy, BacktestRun
from apps.market_data.models import Symbol
from apps.backtest.services import BacktestEngine
from datetime import datetime, timedelta
from django.utils import timezone

# Get strategy and symbol
strategy = Strategy.objects.get(name__icontains='RSI Moderate')
symbol = Symbol.objects.get(name='BTCUSDT')

# Create new backtest run
start_date = timezone.make_aware(datetime(2026, 2, 12, 0, 0, 0))
end_date = timezone.make_aware(datetime(2026, 2, 15, 0, 0, 0))

backtest_run = BacktestRun.objects.create(
    name=f"Test Fix - {datetime.now().strftime('%H:%M:%S')}",
    strategy=strategy,
    symbol=symbol,
    interval='1h',
    start_date=start_date,
    end_date=end_date,
    initial_capital=strategy.initial_capital,
    status='pending'
)

print(f"Created backtest run #{backtest_run.id}")
print(f"Running backtest...")

# Run backtest
engine = BacktestEngine(backtest_run)
result = engine.run()

# Print results
backtest_run.refresh_from_db()
print(f"\nBacktest Results:")
print(f"Status: {backtest_run.status}")
print(f"Total Trades: {backtest_run.total_trades}")
print(f"Winning Trades: {backtest_run.winning_trades}")
print(f"Losing Trades: {backtest_run.losing_trades}")
print(f"Win Rate: {backtest_run.win_rate}%")
print(f"Total Return: {backtest_run.total_return}%")

# Check some trades
from apps.backtest.models import Trade
trades = Trade.objects.filter(backtest_run=backtest_run).order_by('entry_time')[:5]

print(f"\nFirst 5 trades:")
for i, trade in enumerate(trades, 1):
    same_time = trade.entry_time == trade.exit_time
    print(f"{i}. {trade.side.upper()} - Entry: ${trade.entry_price:.2f} -> Exit: ${trade.exit_price:.2f}")
    print(f"   Same timestamp: {same_time}, Exit: {trade.exit_reason}, PnL: ${trade.pnl:.2f}")
