'use client';

import { SystemStatus } from '@/components/shared/SystemStatus';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Concilie
            </h1>
            <p className="text-gray-600">
              Selecione um módulo para começar
            </p>
          </div>

          <div className="mb-12">
            <SystemStatus />
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-12">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
                🎯 Gestão
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Gerenciar clientes, ECs, contextos, bandeiras, termos e taxas
              </p>
              <a
                href="/gestao"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Acessar Gestão
              </a>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
                📊 Análises
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Visualizar relatórios e análises financeiras
              </p>
              <a
                href="/analises"
                className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Ver Análises
              </a>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
                📁 Importação
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Importar arquivos de vendas e recebíveis
              </p>
              <a
                href="/importacao"
                className="inline-block bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Importar Dados
              </a>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
                🔧 Configurações
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Configurar sistema e preferências
              </p>
              <a
                href="/config"
                className="inline-block bg-gray-600 hover:bg-gray-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Configurar
              </a>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg text-center">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-2">
              Stack Moderno
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Next.js 16 + TypeScript + FastAPI + SQLAlchemy | MySQL/SQLite
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
