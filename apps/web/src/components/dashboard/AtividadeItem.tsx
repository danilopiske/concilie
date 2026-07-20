'use client';

import { EventoAtividade } from '@/lib/api/dashboard';

const TIPO_LABEL: Record<string, string> = {
  importacao: 'Importação',
  calculo: 'Cálculo',
  relatorio: 'Relatório',
  abusividade: 'Abusividade',
  extrato: 'Extrato',
};

const STATUS_STYLE: Record<string, string> = {
  ok: 'bg-green-100 text-green-700',
  alerta: 'bg-yellow-100 text-yellow-700',
  erro: 'bg-red-100 text-red-700',
};

const TIPO_STYLE: Record<string, string> = {
  importacao: 'bg-purple-100 text-purple-700',
  calculo: 'bg-blue-100 text-blue-700',
  relatorio: 'bg-cyan-100 text-cyan-700',
  abusividade: 'bg-orange-100 text-orange-700',
  extrato: 'bg-gray-100 text-gray-700',
};

interface AtividadeItemProps {
  evento: EventoAtividade;
}

export function AtividadeItem({ evento }: AtividadeItemProps) {
  const dataFormatada = new Date(evento.created_at).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${TIPO_STYLE[evento.tipo]}`}>
        {TIPO_LABEL[evento.tipo]}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 truncate">{evento.descricao}</p>
        <p className="text-xs text-gray-500 mt-0.5">{evento.cliente_nome} · {dataFormatada}</p>
      </div>
      <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${STATUS_STYLE[evento.status]}`}>
        {evento.status}
      </span>
    </div>
  );
}
