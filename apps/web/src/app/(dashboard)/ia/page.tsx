'use client';

import { useEffect, useRef, useState } from 'react';
import { Bot, Send, Sparkles, RefreshCw } from 'lucide-react';
import { iaApi, ChatMessage } from '@/lib/api/ia';
import { importacaoApi, Processamento } from '@/lib/api/importacao';

const EXEMPLOS = [
  'Qual bandeira cobrou mais acima do esperado?',
  'Houve cobranças abusivas neste processamento?',
  'Quais modalidades tiveram maior perda?',
  'Qual o valor total de excesso cobrado?',
];

export default function IAPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState('');
  const [mensagem, setMensagem] = useState('');
  const [historico, setHistorico] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    importacaoApi.processamentos
      .listar(undefined, undefined, true)
      .then(setProcessamentos)
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [historico, loading]);

  const handleProcessamentoChange = (id: string) => {
    setSelectedProcessamento(id);
    setHistorico([]);
    setError(null);
  };

  const enviar = async (texto?: string) => {
    const msg = (texto ?? mensagem).trim();
    if (!msg || loading) return;

    const novaMsg: ChatMessage = { role: 'user', content: msg };
    const novoHistorico = [...historico, novaMsg];
    setHistorico(novoHistorico);
    setMensagem('');
    setLoading(true);
    setError(null);

    try {
      const res = await iaApi.chat({
        mensagem: msg,
        processamento_id: selectedProcessamento || undefined,
        historico: historico,
      });
      setHistorico([
        ...novoHistorico,
        { role: 'assistant', content: res.resposta },
      ]);
      // Armazenar sugestões na última mensagem do assistente (via data attr workaround)
      if (res.sugestoes?.length) {
        setSugestoes(res.sugestoes);
      } else {
        setSugestoes([]);
      }
    } catch {
      setError('Erro ao obter resposta. Verifique se o GEMINI_API_KEY está configurado.');
    } finally {
      setLoading(false);
    }
  };

  const [sugestoes, setSugestoes] = useState<string[]>([]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  return (
    <div className="max-w-4xl mx-auto pb-10 flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="border-b pb-4 flex items-center gap-3">
        <Sparkles className="w-6 h-6 text-purple-600" />
        <div>
          <h1 className="text-xl font-bold text-gray-800">Assistente IA</h1>
          <p className="text-sm text-gray-500">Faça perguntas em linguagem natural sobre seus processamentos</p>
        </div>
      </div>

      {/* Seletor de processamento */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600 whitespace-nowrap">Processamento:</label>
        <select
          value={selectedProcessamento}
          onChange={(e) => handleProcessamentoChange(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm flex-1 max-w-xs"
        >
          <option value="">Sem contexto específico</option>
          {processamentos.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nome_arquivo || p.id}
            </option>
          ))}
        </select>
        {historico.length > 0 && (
          <button
            onClick={() => { setHistorico([]); setSugestoes([]); }}
            className="flex items-center gap-1 px-3 py-1.5 text-xs border rounded hover:bg-gray-50 text-gray-500"
          >
            <RefreshCw className="w-3 h-3" /> Nova conversa
          </button>
        )}
      </div>

      {/* Área de chat */}
      <div className="flex-1 border rounded-xl bg-gray-50 overflow-y-auto p-4 space-y-4 min-h-[400px] max-h-[500px]">
        {historico.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full py-10 space-y-4">
            <Bot className="w-12 h-12 text-purple-300" />
            <p className="text-gray-400 text-sm">Selecione um processamento e faça uma pergunta</p>
            <div className="flex flex-wrap gap-2 justify-center max-w-md">
              {EXEMPLOS.map((ex) => (
                <button
                  key={ex}
                  onClick={() => enviar(ex)}
                  className="px-3 py-1.5 text-xs border rounded-full bg-white hover:bg-purple-50 hover:border-purple-300 text-gray-600 transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {historico.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-purple-600 text-white rounded-br-sm'
                  : 'bg-white border text-gray-800 rounded-bl-sm shadow-sm'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-1.5 mb-1 text-xs text-purple-600 font-medium">
                  <Bot className="w-3 h-3" /> Assistente
                </div>
              )}
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-gray-400 flex items-center gap-2 shadow-sm">
              <Bot className="w-3 h-3 text-purple-400" />
              <span className="animate-pulse">Digitando...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Chips de sugestões */}
      {sugestoes.length > 0 && !loading && (
        <div className="flex flex-wrap gap-2">
          {sugestoes.map((s) => (
            <button
              key={s}
              onClick={() => enviar(s)}
              className="px-3 py-1 text-xs border rounded-full bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      {/* Input */}
      <div className="flex gap-2">
        <textarea
          value={mensagem}
          onChange={(e) => setMensagem(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Faça uma pergunta sobre os dados... (Enter para enviar)"
          rows={2}
          className="flex-1 border rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-300"
          disabled={loading}
        />
        <button
          onClick={() => enviar()}
          disabled={!mensagem.trim() || loading}
          className="px-4 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:opacity-40 flex items-center gap-2 text-sm"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
