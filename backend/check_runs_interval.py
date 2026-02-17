from apps.backtest.models import BacktestRun

runs = BacktestRun.objects.filter(id__in=[3, 4])

for run in runs:
    print(f"Run #{run.id}: {run.name}")
    print(f"  Interval: {run.interval}")
    print(f"  Period: {run.start_date} to {run.end_date}")
    print()
