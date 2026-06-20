import { Outlet, Link, useNavigate } from 'react-router-dom';
import { Video, LogOut, Wallet } from 'lucide-react';
import { supabase } from '../lib/supabase';
import CreditWidget from './CreditWidget';

export default function Layout() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen flex-col">
      {/* ─── Header ─────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-2.5 font-bold text-xl text-gray-900">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
              <Video className="h-5 w-5" />
            </div>
            <span>UGC Studio</span>
          </Link>

          <div className="flex items-center gap-4">
            <CreditWidget />
            <Link
              to="/create"
              className="btn-primary text-sm"
            >
              + New Video
            </Link>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* ─── Main ───────────────────────────────── */}
      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>

      {/* ─── Footer ─────────────────────────────── */}
      <footer className="border-t border-gray-100 py-6">
        <div className="mx-auto max-w-7xl px-4 text-center text-xs text-gray-400 sm:px-6 lg:px-8">
          UGC Video Creator &mdash; Powered by AI
        </div>
      </footer>
    </div>
  );
}
