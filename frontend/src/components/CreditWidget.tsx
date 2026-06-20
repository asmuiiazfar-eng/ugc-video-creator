import { useEffect, useState } from 'react';
import { Coins, AlertTriangle } from 'lucide-react';
import { getCredits } from '../lib/api';

export default function CreditWidget() {
  const [balance, setBalance] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCredits()
      .then((res) => setBalance(res.balance))
      .catch(() => setBalance(0))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="h-8 w-24 animate-pulse rounded-lg bg-gray-200" />
    );
  }

  const low = balance !== null && balance < 20;

  return (
    <div
      className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
        low
          ? 'border-red-200 bg-red-50 text-red-700'
          : 'border-gray-200 bg-gray-50 text-gray-700'
      }`}
    >
      {low ? (
        <AlertTriangle className="h-4 w-4 text-red-500" />
      ) : (
        <Coins className="h-4 w-4 text-yellow-500" />
      )}
      <span>{balance ?? 0}</span>
      <span className="text-xs text-gray-400">credits</span>
    </div>
  );
}
