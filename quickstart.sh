#!/bin/bash
# Quick start script for Binance Market Lab

set -e  # Exit on error

echo "🚀 Binance Market Lab - Quick Start"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your Binance API keys before proceeding."
    echo "   Use READ-ONLY API keys for security."
    echo ""
    read -p "Press Enter after editing .env file..."
fi

echo "🏗️  Building Docker images..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 10

echo ""
echo "📊 Running database migrations..."
docker compose exec -T backend python backend/manage.py migrate

echo ""
echo "🔧 Creating TimescaleDB hypertables..."
docker compose exec -T backend python backend/manage.py migrate market_data 0002

echo ""
echo "📦 Collecting static files..."
docker compose exec -T backend python backend/manage.py collectstatic --noinput

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Services are running at:"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/api/docs/"
echo "   - Django Admin: http://localhost:8000/admin/"
echo ""
echo "🔐 Next steps:"
echo "   1. Create admin user: make createsuperuser"
echo "   2. Add tracked symbols via Django admin"
echo "   3. Start data ingestion: make ingest-test"
echo ""
echo "📚 View logs: make logs"
echo "📖 All commands: make help"
echo ""
