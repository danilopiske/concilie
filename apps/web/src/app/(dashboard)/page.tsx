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

       <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            
            {/* 1. Gestão */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                🎯 Gestão
              </h2>
              <p className="text-gray-600 mb-4 min-h-[48px]">
                Gerenciar clientes, ECs, contextos, bandeiras, termos e taxas
              </p>
              <Link
                href="/gestao"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition-colors w-full text-center"
              >
                Acessar Gestão
              </Link>
            </div>

            {/* 2. Importação */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                📁 Importação
              </h2>
              <p className="text-gray-600 mb-4 min-h-[48px]">
                Importar arquivos de vendas e recebíveis para processamento
              </p>
              <Link
                href="/importar"
                className="inline-block bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-2 rounded-lg transition-colors w-full text-center"
              >
                Importar Dados
              </Link>
            </div>

            {/* 3. Análise e Correções */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                📊 Análise e Correções
              </h2>
              <p className="text-gray-600 mb-4 min-h-[48px]">
                Auditar processamentos, corrigir dados e verificar abusividades
              </p>
              <Link
                href="/analise-correcoes"
                className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium px-6 py-2 rounded-lg transition-colors w-full text-center"
              >
                Acessar Análises
              </Link>
            </div>

            {/* 4. Cálculos */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                🧮 Cálculos
              </h2>
              <p className="text-gray-600 mb-4 min-h-[48px]">
                Executar cálculos de taxas e conferências financeiras
              </p>
              <Link
                href="/calculos"
                className="inline-block bg-orange-600 hover:bg-orange-700 text-white font-medium px-6 py-2 rounded-lg transition-colors w-full text-center"
              >
                Ir para Cálculos
              </Link>
            </div>

            {/* 5. Relatórios */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                📄 Relatórios
              </h2>
              <p className="text-gray-600 mb-4 min-h-[48px]">
                Gerar relatórios gerenciais, sintéticos e demonstrativos
              </p>
              <Link
                href="/relatorios"
                className="inline-block bg-teal-600 hover:bg-teal-700 text-white font-medium px-6 py-2 rounded-lg transition-colors w-full text-center"
              >
                Ver Relatórios
              </Link>
            </div>

            {/* 6. Configurações */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                🔧 Configurações
              </h2>
              <p className="text-gray-600 mb-4 min-h-[48px]">
                Configurar usuários, permissões e preferências do sistema
              </p>
              <Link
                href="/configuracoes"
                className="inline-block bg-gray-600 hover:bg-gray-700 text-white font-medium px-6 py-2 rounded-lg transition-colors w-full text-center"
              >
                Configurar
              </Link>
            </div>
       </div>
    </div>
  );
}
