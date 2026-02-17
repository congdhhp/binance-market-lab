from apps.backtest.models import Trade
from decimal import Decimal

# Get first trade from run 3
trade = Trade.objects.filter(backtest_run_id=3).order_by('entry_time').first()

if trade:
    print(f'Trade Analysis:')
    print(f'  Side: {trade.side}')
    print(f'  Entry: ${trade.entry_price} at {trade.entry_time}')
    print(f'  Exit: ${trade.exit_price} at {trade.exit_time}')
    print(f'  Quantity: {trade.quantity}')
    print(f'  Position Size (quote): ${trade.position_size_quote}')
    print(f'  Entry Fee: ${trade.entry_fee}')
    print(f'  Exit Fee: ${trade.exit_fee}')
    print(f'  Total Fees: ${trade.entry_fee + trade.exit_fee}')
    print()
    
    # Manual PnL calculation
    if trade.side == 'buy':
        raw_pnl = (trade.exit_price - trade.entry_price) * trade.quantity
    else:
        raw_pnl = (trade.entry_price - trade.exit_price) * trade.quantity
    
    total_pnl = raw_pnl - trade.entry_fee - trade.exit_fee
    
    print(f'  Raw PnL (no fees): ${raw_pnl:.2f}')
    print(f'  Calculated PnL: ${total_pnl:.2f}')
    print(f'  Stored PnL: ${trade.pnl}')
    print(f'  Stored PnL %: {trade.pnl_pct}%')
    print()
    
    # Check winning/losing logic
    print(f'Is winning? {trade.pnl > 0}')
    print(f'PnL decimal value: {trade.pnl}')
