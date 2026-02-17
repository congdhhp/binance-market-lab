from apps.market_data.models import Kline, Symbol

symbol = Symbol.objects.get(name='BTCUSDT')

# Check available kline dates
klines_count = Kline.objects.filter(symbol=symbol, interval='1m').count()
print(f"Total 1m klines for BTCUSDT: {klines_count}")

if klines_count > 0:
    first = Kline.objects.filter(symbol=symbol, interval='1m').order_by('open_time').first()
    last = Kline.objects.filter(symbol=symbol, interval='1m').order_by('-open_time').first()
    
    print(f"First kline: {first.open_time}")
    print(f"Last kline: {last.open_time}")
else:
    print("No klines found!")
