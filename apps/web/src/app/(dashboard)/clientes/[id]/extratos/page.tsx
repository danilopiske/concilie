'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Upload, Download, CheckCircle, AlertTriangle, RefreshCw, Trash2 } from 'lucide-react';
import { extratoClienteApi, ExtratoCliente, ExtratoStatusResumo } from '@/lib/api/extrato_cliente';

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  aguardando: { label: '🔵 Aguardando', className: 'bg-blue-100 text-blue-700' },
  importado:  { label: '🟢 Importado',  className: 'bg-green-100 text-green-700' },
  divergente: { label: '🟡 Divergente', className: 'bg-yellow-100 text-yellow-700' },
};

const TIPOS = ['Venda', 'Recebivel', 'Outro'];

export default function ExtratosClientePage() {
  const params = useParams();
  const clienteId = Number(params.id);

  const [extratos, setExtratos] = useState<ExtratoCliente[]>([]);
  const [resumo, setResumo] = useState<ExtratoStatusResumo | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingValidar, setLoadingValidar] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [tipo, setTipo] = useState('Venda');
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [list, res] = await Promise.all([
        extratoClienteApi.listar(clienteId),
        extratoClienteApi.statusResumo(clienteId),
      ]);
      setExtratos(list);
      setResumo(res);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [clienteId]);

  const handleUpload = async () => {
    if (!selectedFile) return;
    setLoadingUpload(true);
    setMsg(null);
    try {
      await extratoClienteApi.upload(clienteId, selectedFile, tipo);
      setMsg('Extrato enviado com sucesso!');
      setShowUpload(false);
      setSelectedFile(null);
      fetchData();
    } catch {
      setMsg('Erro ao fazer upload do extrato.');
    } finally {
      setLoadingUpload(false);
    }
  };

  const handleValidar = async () => {
    setLoadingValidar(true);
    setMsg(null);
    try {
      const r = await extratoClienteApi.validar(clienteId);
      setMsg(`Validação concluída: ${r.atualizados} extrato(s) atualizado(s).`);
      fetchData();
    } catch {
      setMsg('Erro ao validar extratos.');
    } finally {
      setLoadingValidar(false);
    }
  };

  const handleDeletar = async (id: string) => {
    if (!confirm('Remover este extrato?')) return;
    try {
      await extratoClienteApi.deletar(clienteId, id);
      fetchData();
    } catch {
      setMsg('Erro ao remover extrato.');
    }
  };

  return (
    <div className="max-w-5xl mx-auto pb-10 space-y-6">
      <div className="flex items-center gap-3 border-b pb-4">
        <Link href="/clientes" className="text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-xl font-bold text-gray-800">Extratos do Cliente #{clienteId}</h1>
      </div>

      {msg && (
        <div className={`p-3 rounded text-sm ${msg.includes('Erro') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {msg}
        </div>
      )}

      {/* Resumo */}
      {resumo && (
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Total', value: resumo.total, color: 'text-gray-700' },
            { label: 'Aguardando', value: resumo.aguardando, color: 'text-blue-600' },
            { label: 'Importado', value: resumo.importado, color: 'text-green-600' },
            { label: 'Divergente', value: resumo.divergente, color: 'text-yellow-600' },
          ].map((s) => (
            <div key={s.label} className="border rounded-lg p-3 text-center">
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Ações */}
      <div className="flex gap-3">
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
        >
          <Upload className="w-4 h-4" /> Upload Extrato
        </button>
        <button
          onClick={handleValidar}
          disabled={loadingValidar}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm disabled:opacity-50"
        >
          <CheckCircle className="w-4 h-4" />
          {loadingValidar ? 'Validando...' : 'Validar Coerência'}
        </button>
        <button onClick={fetchData} className="p-2 text-gray-500 hover:text-gray-700" title="Atualizar">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Modal upload */}
      {showUpload && (
        <div className="border rounded-lg p-4 bg-gray-50 space-y-3">
          <h3 className="font-medium text-gray-700">Novo Extrato</h3>
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-xs text-gray-600 block mb-1">Arquivo</label>
              <input
                ref={fileRef}
                type="file"
                accept=".xlsx,.xls,.csv,.txt,.zip"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                className="text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 block mb-1">Tipo</label>
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
                className="border rounded px-2 py-1 text-sm"
              >
                {TIPOS.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <button
              onClick={handleUpload}
              disabled={!selectedFile || loadingUpload}
              className="px-4 py-1.5 bg-blue-600 text-white rounded text-sm disabled:opacity-50"
            >
              {loadingUpload ? 'Enviando...' : 'Enviar'}
            </button>
            <button onClick={() => setShowUpload(false)} className="text-gray-500 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      {/* Tabela */}
      {loading ? (
        <p className="text-gray-500 text-sm">Carregando...</p>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Arquivo</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Tipo</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Enviado em</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-center font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {extratos.map((e) => {
                const badge = STATUS_BADGE[e.status] ?? STATUS_BADGE.aguardando;
                return (
                  <tr key={e.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">{e.nome_arquivo}</td>
                    <td className="px-4 py-3 text-gray-500">{e.tipo}</td>
                    <td className="px-4 py-3 text-gray-500">{new Date(e.uploaded_at).toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${badge.className}`}>
                        {badge.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 flex justify-center gap-2">
                      <a
                        href={extratoClienteApi.downloadUrl(clienteId, e.id)}
                        className="text-blue-600 hover:text-blue-800"
                        title="Baixar"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                      {e.status === 'aguardando' && (
                        <button
                          onClick={() => handleDeletar(e.id)}
                          className="text-red-400 hover:text-red-600"
                          title="Remover"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
              {extratos.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                    Nenhum extrato cadastrado para este cliente.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

