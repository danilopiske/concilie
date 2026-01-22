/**
 * Página principal de Gestão
 * Menu de acesso às ferramentas de gestão
 */

'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { 
  Users,
  Filter,
  CreditCard,
  DollarSign,
  Wallet,
} from 'lucide-react';

interface GestaoCard {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const GESTAO_TOOLS: GestaoCard[] = [
  {
    title: 'Clientes',
    description: 'Gerencie clientes, endereços e estabelecimentos comerciais',
    href: '/gestao/clientes',
    icon: Users,
  },
  {
    title: 'Termos Filtráveis',
    description: 'Configure termos para filtrar transações automaticamente',
    href: '/gestao/termos',
    icon: Filter,
  },
  {
    title: 'Bandeiras',
    description: 'Configure as bandeiras de cartão disponíveis',
    href: '/gestao/bandeiras',
    icon: CreditCard,
  },
  {
    title: 'Bandeiras por EC',
    description: 'Defina quais bandeiras são aceitas em cada EC',
    href: '/gestao/bandeiras-ec',
    icon: CreditCard,
  },
  {
    title: 'Taxas',
    description: 'Gerencie taxas de transação por bandeira e forma de pagamento',
    href: '/gestao/taxas',
    icon: DollarSign,
  },
  {
    title: 'Formas de Pagamento',
    description: 'Configure as formas de pagamento aceitas',
    href: '/gestao/formas-pagamento',
    icon: Wallet,
  },
];

export default function GestaoPage() {
  return (
    <div className="max-w-7xl mx-auto">
      {/* Cabeçalho */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Gestão</h1>
        <p className="mt-2 text-sm text-gray-600">
          Ferramentas para gerenciar cadastros e configurações do sistema
        </p>
      </div>

      {/* Grid de Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {GESTAO_TOOLS.map((tool) => {
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
