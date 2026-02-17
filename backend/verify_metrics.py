from apps.backtest.models import BacktestRun, Trade
from decimal import Decimal

# Get the latest test run
run = BacktestRun.objects.latest('id')

print(f"Backtest Run #{run.id}: {run.name}")
print(f"{'='*60}")

# Get all trades
trades = Trade.objects.filter(backtest_run=run, is_open=False)

# Manual calculation
winning_trades = trades.filter(pnl__gt=0)
losing_trades = trades.filter(pnl__lte=0)

total = trades.count()
wins = winning_trades.count()
losses = losing_trades.count()

print(f"\nTrade Counts:")
print(f"  Total trades: {total}")
print(f"  Winning trades: {wins}")
print(f"  Losing trades: {losses}")

# Calculate win rate manually
if total > 0:
    win_rate = (wins / total) * 100
    print(f"  Calculated win rate: {win_rate:.2f}%")
    print(f"  Stored win rate: {run.win_rate}%")
    print(f"  Match: {abs(float(run.win_rate) - win_rate) < 0.01}")

# Calculate total P&L
total_pnl = sum([float(t.pnl) for t in trades])
winning_pnl = sum([float(t.pnl) for t in winning_trades])
losing_pnl = sum([float(t.pnl) for t in losing_trades])

print(f"\nProfit/Loss:")
print(f"  Total P&L: ${total_pnl:.2f}")
print(f"  Winning P&L: ${winning_pnl:.2f}")
print(f"  Losing P&L: ${losing_pnl:.2f}")

# Average win/loss
if wins > 0:
    avg_win = winning_pnl / wins
    print(f"  Avg Win: ${avg_win:.2f}")
    print(f"  Stored Avg Win: ${run.avg_win}")

if losses > 0:
    avg_loss = abs(losing_pnl / losses)
    print(f"  Avg Loss: ${avg_loss:.2f}")
    print(f"  Stored Avg Loss: ${run.avg_loss}")

# Profit factor
if losses > 0 and abs(losing_pnl) > 0:
    profit_factor = abs(winning_pnl / losing_pnl)
    print(f"  Profit Factor: {profit_factor:.2f}")
    print(f"  Stored Profit Factor: {run.profit_factor}")

# Return calculation
print(f"\nCapital:")
print(f"  Initial: ${run.initial_capital}")
print(f"  Final: ${run.final_capital}")
if run.total_return:
    print(f"  Total Return: {run.total_return}%")
else:
    if run.initial_capital and run.final_capital:
        returns = ((run.final_capital - run.initial_capital) / run.initial_capital) * 100
        print(f"  Calculated Return: {returns:.2f}%")

# Show sample winning and losing trades
print(f"\nSample Winning Trade:")
winner = winning_trades.first()
if winner:
    print(f"  {winner.side.upper()}: Entry ${winner.entry_price} -> Exit ${winner.exit_price}")
    print(f"  P&L: ${winner.pnl} ({winner.pnl_pct}%)")
    print(f"  Exit reason: {winner.exit_reason}")

print(f"\nSample Losing Trade:")
loser = losing_trades.first()
if loser:
    print(f"  {loser.side.upper()}: Entry ${loser.entry_price} -> Exit ${loser.exit_price}")
    print(f"  P&L: ${loser.pnl} ({loser.pnl_pct}%)")
    print(f"  Exit reason: {loser.exit_reason}")
