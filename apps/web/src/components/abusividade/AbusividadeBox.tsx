'use client';

import { useState } from 'react';
import { BandeiraFormaPagamento, GranularidadeItem } from '@/lib/api/abusividade';

const STATUS_STYLE: Record<string, string> = {
  normal: 'bg-green-100 text-green-700',
  atencao: 'bg-yellow-100 text-yellow-700',
  critico: 'bg-red-100 text-red-700',
};

const STATUS_LABEL: Record<string, string> = {
  normal: '🟢 Normal',
  atencao: '🟡 Atenção',
  critico: '🔴 Crítico',
};

type Tab = 'dia' | 'hora' | 'semana';

function GranularidadeTabela({ items }: { items: GranularidadeItem[] }) {
  if (!items.length) return <p className="text-xs text-gray-400 py-4 text-center">Sem dados</p>;
  return (
    <table className="w-full text-xs">
      <thead className="bg-gray-50 border-b">
        <tr>
          <th className="px-3 py-2 text-left font-medium text-gray-600">Período</th>
          <th className="px-3 py-2 text-right font-medium text-gray-600">Qtd</th>
          <th className="px-3 py-2 text-right font-medium text-gray-600">Taxa Média</th>
          <th className="px-3 py-2 text-right font-medium text-gray-600">Variação</th>
          <th className="px-3 py-2 text-center font-medium text-gray-600">Status</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.label} className="border-b hover:bg-gray-50">
            <td className="px-3 py-1.5 font-medium text-gray-700">{item.label}</td>
            <td className="px-3 py-1.5 text-right text-gray-500">{item.quantidade}</td>
            <td className="px-3 py-1.5 text-right text-gray-700">{(item.taxa_media * 100).toFixed(2)}%</td>
            <td className={`px-3 py-1.5 text-right font-medium ${item.variacao_vs_media > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {item.variacao_vs_media > 0 ? '+' : ''}{item.variacao_vs_media.toFixed(1)}%
            </td>
            <td className="px-3 py-1.5 text-center">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLE[item.status]}`}>
                {STATUS_LABEL[item.status]}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface AbusividadeBoxProps {
  grupo: BandeiraFormaPagamento;
}

export default function AbusividadeBox({ grupo }: AbusividadeBoxProps) {
  const [activeTab, setActiveTab] = useState<Tab>('dia');

  const tabs: { key: Tab; label: string }[] = [
    { key: 'dia', label: 'Por Dia da Semana' },
    { key: 'hora', label: 'Por Hora do Dia' },
    { key: 'semana', label: 'Por Semana do Mês' },
  ];

  const dataMap: Record<Tab, GranularidadeItem[]> = {
    dia: grupo.por_dia_semana,
    hora: grupo.por_hora,
    semana: grupo.por_semana_mes,
  };

  return (
    <div className="border rounded-lg overflow-hidden shadow-sm">
      {/* Header */}
      <div className="bg-gray-800 text-white px-4 py-3 flex items-center justify-between">
        <div>
          <span className="font-semibold">{grupo.bandeira}</span>
          <span className="text-gray-300 mx-2">·</span>
          <span className="text-gray-300 text-sm">{grupo.forma_pagamento}</span>
        </div>
        <div className="text-sm text-gray-300">
          Taxa média: <span className="text-white font-medium">{(grupo.taxa_media_geral * 100).toFixed(2)}%</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b bg-gray-50">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Conteúdo */}
      <div className="overflow-x-auto">
        <GranularidadeTabela items={dataMap[activeTab]} />
      </div>
    </div>
  );
}
