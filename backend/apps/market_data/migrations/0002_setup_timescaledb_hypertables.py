# Generated migration for TimescaleDB hypertables setup

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('market_data', '0001_initial'),
    ]

    operations = [
        # Drop primary key constraint from tables before creating hypertables
        # TimescaleDB requires partitioning column in all unique indexes
        migrations.RunSQL(
            sql="""
            ALTER TABLE market_data_kline DROP CONSTRAINT IF EXISTS market_data_kline_pkey CASCADE;
            ALTER TABLE market_data_trade DROP CONSTRAINT IF EXISTS market_data_trade_pkey CASCADE;
            ALTER TABLE market_data_orderbook_snapshot DROP CONSTRAINT IF EXISTS market_data_orderbook_snapshot_pkey CASCADE;
            ALTER TABLE market_data_ticker24h DROP CONSTRAINT IF EXISTS market_data_ticker24h_pkey CASCADE;
            ALTER TABLE market_data_funding_rate DROP CONSTRAINT IF EXISTS market_data_funding_rate_pkey CASCADE;
            ALTER TABLE market_data_open_interest DROP CONSTRAINT IF EXISTS market_data_open_interest_pkey CASCADE;
            """,
            reverse_sql=""
        ),
        
        # Convert Kline table to hypertable partitioned by open_time
        migrations.RunSQL(
            sql="SELECT create_hypertable('market_data_kline', 'open_time', if_not_exists => TRUE, migrate_data => TRUE);",
            reverse_sql="SELECT * FROM drop_hypertable('market_data_kline', if_exists => TRUE);"
        ),
        
        # Convert Trade table to hypertable partitioned by timestamp
        migrations.RunSQL(
            sql="SELECT create_hypertable('market_data_trade', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);",
            reverse_sql="SELECT * FROM drop_hypertable('market_data_trade', if_exists => TRUE);"
        ),
        
        # Convert OrderBookSnapshot table to hypertable partitioned by timestamp
        migrations.RunSQL(
            sql="SELECT create_hypertable('market_data_orderbook_snapshot', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);",
            reverse_sql="SELECT * FROM drop_hypertable('market_data_orderbook_snapshot', if_exists => TRUE);"
        ),
        
        # Convert Ticker24h table to hypertable partitioned by timestamp
        migrations.RunSQL(
            sql="SELECT create_hypertable('market_data_ticker24h', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);",
            reverse_sql="SELECT * FROM drop_hypertable('market_data_ticker24h', if_exists => TRUE);"
        ),
        
        # Convert FundingRate table to hypertable partitioned by timestamp
        migrations.RunSQL(
            sql="SELECT create_hypertable('market_data_funding_rate', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);",
            reverse_sql="SELECT * FROM drop_hypertable('market_data_funding_rate', if_exists => TRUE);"
        ),
        
        # Convert OpenInterest table to hypertable partitioned by timestamp
        migrations.RunSQL(
            sql="SELECT create_hypertable('market_data_open_interest', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);",
            reverse_sql="SELECT * FROM drop_hypertable('market_data_open_interest', if_exists => TRUE);"
        ),
        
        # Enable compression on Kline hypertable
        migrations.RunSQL(
            sql="""
            ALTER TABLE market_data_kline SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'symbol_id,interval'
            );
            """,
            reverse_sql=""
        ),
        
        # Add compression policy for Kline (compress data older than 7 days)
        migrations.RunSQL(
            sql="SELECT add_compression_policy('market_data_kline', INTERVAL '7 days', if_not_exists => TRUE);",
            reverse_sql="SELECT remove_compression_policy('market_data_kline', if_exists => TRUE);"
        ),
        
        # Enable compression on Trade hypertable
        migrations.RunSQL(
            sql="""
            ALTER TABLE market_data_trade SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'symbol_id'
            );
            """,
            reverse_sql=""
        ),
        
        # Add compression policy for Trade (compress data older than 7 days)
        migrations.RunSQL(
            sql="SELECT add_compression_policy('market_data_trade', INTERVAL '7 days', if_not_exists => TRUE);",
            reverse_sql="SELECT remove_compression_policy('market_data_trade', if_exists => TRUE);"
        ),
        
        # Enable compression on OrderBookSnapshot hypertable
        migrations.RunSQL(
            sql="""
            ALTER TABLE market_data_orderbook_snapshot SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'symbol_id'
            );
            """,
            reverse_sql=""
        ),
        
        # Add compression policy for OrderBookSnapshot (compress data older than 3 days)
        migrations.RunSQL(
            sql="SELECT add_compression_policy('market_data_orderbook_snapshot', INTERVAL '3 days', if_not_exists => TRUE);",
            reverse_sql="SELECT remove_compression_policy('market_data_orderbook_snapshot', if_exists => TRUE);"
        ),
    ]
