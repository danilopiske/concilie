/**
 * Página principal de Importação
 * Menu de acesso às ferramentas de importação
 */

'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { 
  Upload,
  FileText,
  History,
} from 'lucide-react';

interface ToolCard {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const IMPORT_TOOLS: ToolCard[] = [
  {
    title: 'Importar Vendas',
    description: 'Faça upload de arquivos de vendas para processamento',
    href: '/importar/vendas',
    icon: Upload,
  },
  {
    title: 'De-Para',
    description: 'Configure mapeamentos de termos para padronização',
    href: '/importar/de-para',
    icon: FileText,
  },
  {
    title: 'Processamentos',
    description: 'Histórico e status de processamentos de arquivos',
    href: '/importar/processamentos',
    icon: History,
  },
];

export default function ImportarPage() {
  return (
    <div className="max-w-7xl mx-auto">
      {/* Cabeçalho */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Importar</h1>
        <p className="mt-2 text-sm text-gray-600">
          Ferramentas para importação e processamento de arquivos
        </p>
      </div>

      {/* Grid de Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {IMPORT_TOOLS.map((tool) => {
          const Icon = tool.icon;
          
          return (
            <Link key={tool.href} href={tool.href}>
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                <div className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <Icon className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {tool.title}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {tool.description}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
