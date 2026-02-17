from apps.market_data.models import Kline, Symbol

symbol = Symbol.objects.get(name='BTCUSDT')

# Check all intervals
for interval in ['1m', '5m', '15m', '1h', '4h', '1d']:
    count = Kline.objects.filter(symbol=symbol, interval=interval).count()
    if count > 0:
        first = Kline.objects.filter(symbol=symbol, interval=interval).order_by('open_time').first()
        last = Kline.objects.filter(symbol=symbol, interval=interval).order_by('-open_time').first()
        print(f"{interval}: {count} klines, {first.open_time} to {last.open_time}")
    else:
        print(f"{interval}: 0 klines")
