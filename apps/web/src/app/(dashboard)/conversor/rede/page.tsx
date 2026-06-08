'use client';

import { useRef, useState } from 'react';
import { FileOutput } from 'lucide-react';
import { RedeUploader } from '@/components/conversor/RedeUploader';
import { ConversaoStatus } from '@/components/conversor/ConversaoStatus';
import { converterRedeFiles } from '@/lib/api/conversor';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function ConverRedePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [erro, setErro] = useState('');
  const blobRef = useRef<Blob | null>(null);
  const nomeRef = useRef<string>('');

  const handleConverter = async () => {
    if (!files.length) return;
    setStatus('loading');
    setErro('');
    try {
      const blob = await converterRedeFiles(files);
      blobRef.current = blob;
      const cd = `Conciliacao_Rede_${new Date().toISOString().slice(0, 10)}.xlsx`;
      nomeRef.current = cd;
      setStatus('success');
    } catch (e: any) {
      setErro(e.message || 'Erro ao processar arquivos.');
      setStatus('error');
    }
  };

  const handleDownload = () => {
    if (!blobRef.current) return;
    const url = URL.createObjectURL(blobRef.current);
    const a = document.createElement('a');
    a.href = url;
    a.download = nomeRef.current;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <ProtectedRoute telaEspecifica="conversor">
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-100 rounded-lg">
          <FileOutput className="h-6 w-6 text-blue-600" />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Conversor — Rede</h1>
          <p className="text-sm text-gray-500">Converta extratos TXT da Rede para XLSX estruturado</p>
        </div>
      </div>

      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <RedeUploader onFilesChange={setFiles} disabled={status === 'loading'} />

        <div className="mt-6">
          <button
            onClick={handleConverter}
            disabled={!files.length || status === 'loading'}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400
              text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
          >
            {status === 'loading'
              ? 'Processando...'
              : `Converter ${files.length > 0 ? `(${files.length} arquivo${files.length > 1 ? 's' : ''})` : ''}`}
          </button>
        </div>

        <ConversaoStatus
          status={status}
          nomeArquivo={nomeRef.current}
          erro={erro}
          onDownload={handleDownload}
        />
      </div>
    </div>
    </ProtectedRoute>
  );
}
