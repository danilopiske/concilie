'use client';

import { SystemStatus } from '@/components/shared/SystemStatus';
import Link from 'next/link';

export default function DashboardHome() {
  return (
    <div className="max-w-4xl mx-auto py-8">
       <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Bem-vindo ao Concilie
            </h1>
            <p className="text-gray-600">
              Selecione um módulo para começar
            </p>
       </div>

       <div className="mb-8">
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
              <Link
                href="/gestao"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Acessar Gestão
              </Link>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
                📊 Análises
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Visualizar relatórios e análises financeiras
              </p>
              <Link
                href="/analises"
                className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Ver Análises
              </Link>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
                📁 Importação
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Importar arquivos de vendas e recebíveis
              </p>
              <Link
                href="/importar"
                className="inline-block bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Importar Dados
              </Link>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
                🔧 Configurações
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Configurar sistema e preferências
              </p>
              <Link
                href="/configuracoes"
                className="inline-block bg-gray-600 hover:bg-gray-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Configurar
              </Link>
            </div>
       </div>
    </div>
  );
}
