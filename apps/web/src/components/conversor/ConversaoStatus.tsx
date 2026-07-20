'use client';

import { Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface Props {
  status: 'idle' | 'loading' | 'success' | 'error';
  nomeArquivo?: string;
  erro?: string;
  onDownload?: () => void;
}

export function ConversaoStatus({ status, nomeArquivo, erro, onDownload }: Props) {
  if (status === 'idle') return null;

  return (
    <div className="mt-6">
      {status === 'loading' && (
        <div className="flex items-center gap-3 text-blue-600 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <Loader2 className="h-5 w-5 animate-spin shrink-0" />
          <span className="text-sm font-medium">Processando arquivo(s)... aguarde</span>
        </div>
      )}

      {status === 'success' && (
        <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-4 py-3">
          <div className="flex items-center gap-3 text-green-700">
            <CheckCircle className="h-5 w-5 shrink-0" />
            <div>
              <p className="text-sm font-medium">Conversão concluída!</p>
              {nomeArquivo && <p className="text-xs text-green-600">{nomeArquivo}</p>}
            </div>
          </div>
          <button
            onClick={onDownload}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Download className="h-4 w-4" />
            Baixar XLSX
          </button>
        </div>
      )}

      {status === 'error' && (
        <div className="flex items-center gap-3 text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span className="text-sm">{erro || 'Erro ao processar arquivo(s).'}</span>
        </div>
      )}
    </div>
  );
}
