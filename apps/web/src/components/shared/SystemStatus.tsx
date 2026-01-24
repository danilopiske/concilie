/**
 * Componente para exibir status do sistema e banco de dados
 */
'use client';

import { useSystemInfo } from '@/lib/hooks/useSystemInfo';

export function SystemStatus() {
  const { info, loading, error } = useSystemInfo();

  if (loading) {
    return (
      <div className="bg-gray-100 bg-gray-800 rounded-lg p-4 animate-pulse">
        <div className="h-4 bg-gray-300 bg-gray-600 rounded w-3/4"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 bg-red-900/20 border border-red-200 border-red-800 rounded-lg p-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <span className="text-2xl">⚠️</span>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700 text-red-400">
              Backend offline: {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!info) return null;

  const isDatabaseConnected = info.status === 'healthy';
  const databaseType = info.database.type.toUpperCase();
  const isMySQL = info.database.type === 'mysql';

  return (
    <div className="bg-white bg-gray-800 rounded-lg shadow-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <div
              className={`w-3 h-3 rounded-full mr-2 ${
                isDatabaseConnected
                  ? 'bg-green-500 animate-pulse'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-sm font-medium text-gray-700 text-gray-300">
              {isDatabaseConnected ? 'Sistema Online' : 'Sistema Offline'}
            </span>
          </div>

          <div className="h-6 w-px bg-gray-300 bg-gray-600" />

          <div className="flex items-center">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                isMySQL
                  ? 'bg-blue-100 text-blue-800 bg-blue-900 text-blue-200'
                  : 'bg-green-100 text-green-800 bg-green-900 text-green-200'
              }`}
            >
              {isMySQL ? '🗄️' : '📁'} {databaseType}
            </span>
          </div>

          <div className="hidden md:flex items-center text-xs text-gray-500 text-gray-400">
            <span>v{info.version}</span>
          </div>
        </div>

        <div className="text-xs text-gray-500 text-gray-400">
          {info.database.dialect} / {info.database.driver}
        </div>
      </div>
    </div>
  );
}
