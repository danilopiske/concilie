'use client';

import { useEffect, useState } from 'react';
import { FileText, Database } from 'lucide-react';
import { processamentosApi, type ArquivoImportado } from '@/lib/api/processamentos';

interface ArquivosImportadosProps {
  processamentoId: string;
}

export function ArquivosImportados({ processamentoId }: ArquivosImportadosProps) {
  const [arquivos, setArquivos] = useState<ArquivoImportado[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!processamentoId) return;
    setLoading(true);
    processamentosApi
      .getArquivos(processamentoId)
      .then(setArquivos)
      .catch(() => setArquivos([]))
      .finally(() => setLoading(false));
  }, [processamentoId]);

  if (loading) return null;
  if (arquivos.length === 0) return null;

  const vendas = arquivos.filter(a => a.tabela === 'vendas_processadas');
  const recebiveis = arquivos.filter(a => a.tabela === 'recebiveis_processados');
  const totalLinhas = arquivos.reduce((s, a) => s + a.total_linhas, 0);

  return (
    <div className="border border-gray-200 rounded bg-gray-50 p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
          Arquivos importados neste processamento
        </span>
        <span className="text-xs text-gray-400">
          {arquivos.length} arquivo{arquivos.length !== 1 ? 's' : ''} · {totalLinhas.toLocaleString('pt-BR')} linhas
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {vendas.map((a) => (
          <FileChip key={a.arquivo_origem_raw} arquivo={a} cor="blue" />
        ))}
        {recebiveis.map((a) => (
          <FileChip key={a.arquivo_origem_raw} arquivo={a} cor="green" />
        ))}
      </div>

      {recebiveis.length > 0 && vendas.length > 0 && (
        <div className="flex gap-3 mt-2 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-200 inline-block" />
            Vendas
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-200 inline-block" />
            Recebíveis
          </span>
        </div>
      )}
    </div>
  );
}

function FileChip({ arquivo, cor }: { arquivo: ArquivoImportado; cor: 'blue' | 'green' }) {
  const bg = cor === 'blue' ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-green-50 border-green-200 text-green-700';
  const nome = arquivo.nome_arquivo.replace(/\.xlsx?$/i, '');

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-mono ${bg}`}
      title={`${arquivo.nome_arquivo} · ${arquivo.total_linhas.toLocaleString('pt-BR')} linhas`}
    >
      <FileText className="w-3 h-3 shrink-0" />
      <span className="max-w-[240px] truncate">{nome}</span>
      <span className="opacity-60 shrink-0">({arquivo.total_linhas.toLocaleString('pt-BR')})</span>
    </span>
  );
}
