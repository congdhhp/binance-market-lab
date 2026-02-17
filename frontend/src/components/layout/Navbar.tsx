import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path ? 'bg-blue-700' : 'hover:bg-blue-600';
  };

  return (
    <nav className="bg-blue-500 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-2">
              <span className="text-2xl">🚀</span>
              <span className="text-xl font-bold">Binance Market Lab</span>
            </Link>

            <div className="hidden md:flex space-x-1">
              <Link
                to="/"
                className={`px-4 py-2 rounded transition ${isActive('/')}`}
              >
                Dashboard
              </Link>
              <Link
                to="/market-data"
                className={`px-4 py-2 rounded transition ${isActive('/market-data')}`}
              >
                Market Data
              </Link>
              <Link
                to="/analysis"
                className={`px-4 py-2 rounded transition ${isActive('/analysis')}`}
              >
                Technical Analysis
              </Link>
              <Link
                to="/backtest"
                className={`px-4 py-2 rounded transition ${isActive('/backtest')}`}
              >
                Backtest
              </Link>
              <Link
                to="/orderbook"
                className={`px-4 py-2 rounded transition ${isActive('/orderbook')}`}
              >
                Orderbook Analytics
              </Link>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-sm">
              <span className="opacity-75">Backend:</span>{' '}
              <span className="font-semibold">✅ Connected</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
