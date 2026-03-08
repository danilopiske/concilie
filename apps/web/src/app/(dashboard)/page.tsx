'use client';

import { SystemStatus } from '@/components/shared/SystemStatus';
import Link from 'next/link';
import { 
  Users, 
  Upload, 
  BarChart3, 
  Calculator, 
  FileText, 
  Settings,
  ArrowRight 
} from 'lucide-react';

const MODULES = [
  {
    title: 'Gestão',
    description: 'Gerenciar clientes, ECs, contextos, bandeiras, termos e taxas',
    href: '/gestao',
    icon: Users,
    color: 'from-[#1e3a8a] to-[#2563eb]',
  },
  {
    title: 'Importação',
    description: 'Importar arquivos de vendas e recebíveis para processamento',
    href: '/importar',
    icon: Upload,
    color: 'from-[#7c3aed] to-[#a855f7]',
  },
  {
    title: 'Análise e Correções',
    description: 'Auditar processamentos, corrigir dados e verificar abusividades',
    href: '/analise-correcoes',
    icon: BarChart3,
    color: 'from-[#059669] to-[#10b981]',
  },
  {
    title: 'Cálculos',
    description: 'Executar cálculos de taxas e conferências financeiras',
    href: '/calculos',
    icon: Calculator,
    color: 'from-[#f59e0b] to-[#fbbf24]',
  },
  {
    title: 'Relatórios',
    description: 'Gerar relatórios gerenciais, sintéticos e demonstrativos',
    href: '/relatorios',
    icon: FileText,
    color: 'from-[#0891b2] to-[#06b6d4]',
  },
  {
    title: 'Configurações',
    description: 'Configurar usuários, permissões e preferências do sistema',
    href: '/configuracoes',
    icon: Settings,
    color: 'from-[#64748b] to-[#94a3b8]',
  },
];


export default function DashboardHome() {
  return (
    <div className="max-w-7xl mx-auto py-8">
       {/* Header */}
       <div className="mb-8">
            <h1 className="text-4xl font-bold text-[#1e3a8a] mb-2" style={{ fontFamily: '"Poppins", sans-serif' }}>
              Bem-vindo ao Financial 
            </h1>
            <p className="text-gray-600 text-lg">
              Sistema de Conciliação Financeira Executiva
            </p>
       </div>


       {/* System Status */}
       <div className="mb-8">
            <SystemStatus />
       </div>

       {/* Module Cards */}
       <div>
         <h2 className="text-2xl font-bold text-[#1e3a8a] mb-6" style={{ fontFamily: '"Poppins", sans-serif' }}>
           Módulos do Sistema
         </h2>
         
         <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
           {MODULES.map((module) => {
             const Icon = module.icon;
             return (
               <Link
                 key={module.href}
                 href={module.href}
                 className="group relative bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100"
               >
                 {/* Gradient Top Border */}
                 <div className={`h-1 bg-gradient-to-r ${module.color}`} />
                 
                 <div className="p-6">
                   {/* Icon */}
                   <div className="mb-4">
                     <div className={`inline-flex p-3 rounded-lg bg-gradient-to-r ${module.color}`}>
                       <Icon className="w-6 h-6 text-white" />
                     </div>
                   </div>
                   
                   {/* Title */}
                   <h3 className="text-xl font-bold text-[#1e3a8a] mb-2 group-hover:text-[#f59e0b] transition-colors">
                     {module.title}
                   </h3>
                   
                   {/* Description */}
                   <p className="text-gray-600 text-sm mb-4 min-h-[48px]">
                     {module.description}
                   </p>
                   
                   {/* Arrow */}
                   <div className="flex items-center text-[#f59e0b] font-medium text-sm group-hover:gap-2 transition-all">
                     Acessar
                     <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                   </div>
                 </div>
                 
                 {/* Hover Glow Effect */}
                 <div className="absolute inset-0 bg-gradient-to-r from-[#f59e0b]/0 to-[#fbbf24]/0 group-hover:from-[#f59e0b]/5 group-hover:to-[#fbbf24]/5 transition-all duration-300 pointer-events-none" />
               </Link>
             );
           })}
         </div>
       </div>
    </div>
  );
}
