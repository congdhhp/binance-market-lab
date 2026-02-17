from apps.backtest.models import Trade, BacktestRun
from django.db.models import Count, Q

# Analyze all backtest runs
runs = BacktestRun.objects.all()

for run in runs:
    print(f"\n{'='*60}")
    print(f"Backtest Run #{run.id}: {run.strategy.name}")
    print(f"{'='*60}")
    print(f"Symbol: {run.symbol.name}")
    print(f"Period: {run.start_date} to {run.end_date}")
    print(f"Stats: {run.total_trades} trades, {run.winning_trades} wins, {run.losing_trades} losses")
    print(f"Win Rate: {run.win_rate}%")
    print()
    
    # Count by side
    buy_count = Trade.objects.filter(backtest_run=run, side='buy').count()
    sell_count = Trade.objects.filter(backtest_run=run, side='sell').count()
    
    print(f"Trade Distribution:")
    print(f"  BUY trades: {buy_count}")
    print(f"  SELL trades: {sell_count}")
    print()
    
    # Analyze profitable vs unprofitable by side
    buy_profitable = Trade.objects.filter(backtest_run=run, side='buy', pnl__gt=0).count()
    buy_unprofitable = Trade.objects.filter(backtest_run=run, side='buy', pnl__lte=0).count()
    sell_profitable = Trade.objects.filter(backtest_run=run, side='sell', pnl__gt=0).count()
    sell_unprofitable = Trade.objects.filter(backtest_run=run, side='sell', pnl__lte=0).count()
    
    print(f"BUY trades:")
    print(f"  Profitable: {buy_profitable}")
    print(f"  Unprofitable: {buy_unprofitable}")
    print()
    print(f"SELL trades:")
    print(f"  Profitable: {sell_profitable}")
    print(f"  Unprofitable: {sell_unprofitable}")
    print()
    
    # Sample a profitable trade if exists
    profitable_trade = Trade.objects.filter(backtest_run=run, pnl__gt=0).first()
    if profitable_trade:
        print(f"Sample Profitable Trade:")
        print(f"  Side: {profitable_trade.side}")
        print(f"  Entry: ${profitable_trade.entry_price}")
        print(f"  Exit: ${profitable_trade.exit_price}")
        print(f"  PnL: ${profitable_trade.pnl}")
    else:
        print("No profitable trades found!")
        # Show a sample unprofitable trade
        unprofitable = Trade.objects.filter(backtest_run=run).order_by('pnl').first()
        if unprofitable:
            print(f"\nWorst Trade:")
            print(f"  Side: {unprofitable.side}")
            print(f"  Entry: ${unprofitable.entry_price}")
            print(f"  Exit: ${unprofitable.exit_price}")
            print(f"  PnL: ${unprofitable.pnl}")
