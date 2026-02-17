"""
Celery tasks for backtesting.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_backtest_task(self, backtest_run_id: int):
    """
    Execute a backtest run asynchronously.
    
    Args:
        backtest_run_id: BacktestRun ID to execute
    """
    from apps.backtest.models import BacktestRun
    from apps.backtest.services import BacktestEngine
    
    try:
        backtest_run = BacktestRun.objects.get(id=backtest_run_id)
        logger.info(f"Starting backtest task: {backtest_run.name}")
        
        # Create engine and run
        engine = BacktestEngine(backtest_run)
        result = engine.run()
        
        logger.info(f"Backtest completed: {result}")
        
        return {
            'status': 'success',
            'backtest_run_id': backtest_run_id,
            **result
        }
        
    except BacktestRun.DoesNotExist:
        logger.error(f"BacktestRun {backtest_run_id} not found")
        return {'status': 'error', 'message': 'Backtest run not found'}
    
    except Exception as e:
        logger.error(f"Error running backtest {backtest_run_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task
def run_strategy_optimization(strategy_id: int, symbol_id: int, interval: str = '1h'):
    """
    Run parameter optimization for a strategy.
    
    Args:
        strategy_id: Strategy ID
        symbol_id: Symbol ID
        interval: Time interval
    """
    from apps.backtest.models import Strategy, BacktestRun
    from apps.market_data.models import Symbol
    
    try:
        strategy = Strategy.objects.get(id=strategy_id)
        symbol = Symbol.objects.get(id=symbol_id)
        
        logger.info(f"Starting optimization for strategy: {strategy.name}")
        
        # Define parameter grid
        parameter_grid = []
        
        if strategy.strategy_type == 'indicator':
            # Example: RSI parameter optimization
            for rsi_oversold in range(20, 35, 5):
                for rsi_overbought in range(65, 85, 5):
                    for stop_loss in [1.0, 2.0, 3.0]:
                        for take_profit in [2.0, 3.0, 5.0]:
                            parameter_grid.append({
                                'rsi_oversold': rsi_oversold,
                                'rsi_overbought': rsi_overbought,
                                'stop_loss_pct': stop_loss,
                                'take_profit_pct': take_profit
                            })
        
        # Run backtests for each parameter set
        results = []
        end_date = timezone.now()
        start_date = end_date - timedelta(days=90)
        
        for params in parameter_grid[:10]:  # Limit to 10 for demo
            # Create backtest run
            backtest_run = BacktestRun.objects.create(
                name=f"Optimization {strategy.name} - {params}",
                strategy=strategy,
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                initial_capital=strategy.initial_capital
            )
            
            # Update strategy parameters temporarily
            # Run backtest
            run_backtest_task.delay(backtest_run.id)
            
            results.append(backtest_run.id)
        
        logger.info(f"Started {len(results)} optimization runs")
        
        return {
            'status': 'success',
            'strategy': strategy.name,
            'runs': results
        }
        
    except Exception as e:
        logger.error(f"Error in strategy optimization: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_backtests(days: int = 90):
    """
    Delete old backtest runs and related data.
    
    Args:
        days: Keep backtests from last N days
    """
    from apps.backtest.models import BacktestRun
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Delete old backtests (cascade will delete trades, portfolios)
    deleted_count, _ = BacktestRun.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed', 'cancelled']
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old backtest runs")
    
    return {
        'status': 'success',
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def generate_backtest_report(backtest_run_id: int):
    """
    Generate detailed report for a backtest run.
    
    Args:
        backtest_run_id: BacktestRun ID
    """
    from apps.backtest.models import BacktestRun, BacktestMetrics
    
    try:
        backtest_run = BacktestRun.objects.get(id=backtest_run_id)
        
        if backtest_run.status != 'completed':
            return {'status': 'error', 'message': 'Backtest not completed'}
        
        # Calculate detailed metrics
        trades = backtest_run.trades.all()
        
        if not trades:
            return {'status': 'error', 'message': 'No trades found'}
        
        # Calculate metrics
        winning_trades = trades.filter(pnl__gt=0)
        losing_trades = trades.filter(pnl__lt=0)
        
        # Consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades.order_by('entry_time'):
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            elif trade.pnl < 0:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        # Create or update metrics
        metrics, created = BacktestMetrics.objects.update_or_create(
            backtest_run=backtest_run,
            defaults={
                'total_return': backtest_run.total_return or 0,
                'max_drawdown': backtest_run.max_drawdown or 0,
                'sharpe_ratio': backtest_run.sharpe_ratio,
                'total_trades': backtest_run.total_trades,
                'winning_trades': backtest_run.winning_trades,
                'losing_trades': backtest_run.losing_trades,
                'win_rate': backtest_run.win_rate or 0,
                'avg_win': backtest_run.avg_win or 0,
                'avg_loss': backtest_run.avg_loss or 0,
                'largest_win': winning_trades.order_by('-pnl').first().pnl if winning_trades.exists() else 0,
                'largest_loss': abs(losing_trades.order_by('pnl').first().pnl) if losing_trades.exists() else 0,
                'profit_factor': backtest_run.profit_factor or 0,
                'expectancy': trades.aggregate(models.Avg('pnl'))['pnl__avg'] or 0,
                'max_consecutive_wins': max_consecutive_wins,
                'max_consecutive_losses': max_consecutive_losses,
            }
        )
        
        logger.info(f"Generated metrics for backtest {backtest_run.name}")
        
        return {
            'status': 'success',
            'backtest_run_id': backtest_run_id,
            'metrics_id': metrics.id
        }
        
    except BacktestRun.DoesNotExist:
        return {'status': 'error', 'message': 'Backtest run not found'}
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}
