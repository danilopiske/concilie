'use client';

import { useEffect, useRef, useState } from 'react';
import { Database, MessageSquarePlus, Send, Trash2, ChevronDown, ChevronUp, Paperclip, X } from 'lucide-react';
import { dbAiApi, ChatSession, ChatMessageItem, MessageResult } from '@/lib/api/db-ai';

const EXEMPLOS = [
  'Quantos clientes estão cadastrados?',
  'Quais são os 10 processamentos mais recentes?',
  'Qual o total de vendas por bandeira?',
  'Quais usuários estão ativos?',
];

interface LocalMessage {
  role: 'user' | 'assistant';
  content: string;
  result?: MessageResult;
}

export default function IaDbPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [pergunta, setPergunta] = useState('');
  const [loading, setLoading] = useState(false);
  const [sqlExpandido, setSqlExpandido] = useState<number | null>(null);
  const [anexo, setAnexo] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dbAiApi.listSessions().then(setSessions).catch(() => {});
  }, []);

  const loadSession = async (session: ChatSession) => {
    setActiveSession(session);
    setSqlExpandido(null);
    try {
      const msgs = await dbAiApi.getMessages(session.id);
      setMessages(msgs.map(m => ({
        role: m.role,
        content: m.content,
        result: m.role === 'assistant' ? { tipo: 'texto' as const, resposta: m.content, sql: m.sql_gerado || '' } : undefined,
      })));
    } catch { setMessages([]); }
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  const newChat = async () => {
    try {
      const session = await dbAiApi.newSession();
      const updated = await dbAiApi.listSessions();
      setSessions(updated);
      setActiveSession(session);
      setMessages([]);
      setSqlExpandido(null);
    } catch {}
  };

  const deleteSession = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    await dbAiApi.deleteSession(id).catch(() => {});
    const updated = await dbAiApi.listSessions();
    setSessions(updated);
    if (activeSession?.id === id) { setActiveSession(null); setMessages([]); }
  };

  const enviar = async (texto?: string) => {
    const q = (texto ?? pergunta).trim();
    if (!q || loading) return;

    let session = activeSession;
    if (!session) {
      try { session = await dbAiApi.newSession(); const upd = await dbAiApi.listSessions(); setSessions(upd); setActiveSession(session); }
      catch { return; }
    }

    const fileToSend = anexo;
    setPergunta('');
    setAnexo(null);
    const userContent = fileToSend ? `${q} [📎 ${fileToSend.name}]` : q;
    setMessages(m => [...m, { role: 'user', content: userContent }]);
    setLoading(true);

    try {
      const result = await dbAiApi.sendMessage(session.id, q, fileToSend);
      setMessages(m => [...m, { role: 'assistant', content: result.resposta || result.erro || '', result }]);
      const upd = await dbAiApi.listSessions();
      setSessions(upd);
      setActiveSession(s => upd.find(x => x.id === s?.id) ?? s);
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Erro ao processar sua pergunta.' }]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  return (
    <div className="flex h-[calc(100vh-68px)] overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-gray-50 flex flex-col shrink-0">
        <div className="p-3 border-b">
          <button
            onClick={newChat}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium bg-violet-600 hover:bg-violet-700 text-white rounded-lg transition-colors"
          >
            <MessageSquarePlus className="w-4 h-4" />
            Novo chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 && (
            <p className="text-xs text-gray-400 text-center mt-4">Nenhum chat ainda</p>
          )}
          {sessions.map(s => (
            <div
              key={s.id}
              onClick={() => loadSession(s)}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors ${
                activeSession?.id === s.id ? 'bg-violet-100 text-violet-800' : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              <Database className="w-3.5 h-3.5 shrink-0 text-gray-400" />
              <span className="flex-1 truncate">{s.titulo || 'Novo chat'}</span>
              <button
                onClick={e => deleteSession(s.id, e)}
                className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-500 transition-opacity"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
        <div className="p-2 border-t">
          <p className="text-xs text-gray-400 text-center">{sessions.length}/3 chats</p>
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!activeSession ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-6 p-8">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-violet-100 rounded-xl">
                <Database className="h-7 w-7 text-violet-600" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">IA — Consulta ao Banco</h1>
                <p className="text-sm text-gray-500">Pergunte em português sobre as tabelas do sistema</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 w-full max-w-lg">
              {EXEMPLOS.map(e => (
                <button key={e} onClick={() => enviar(e)}
                  className="text-left text-sm px-4 py-3 border rounded-lg hover:bg-violet-50 hover:border-violet-300 transition-colors text-gray-600">
                  {e}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'user' ? (
                  <div className="max-w-[70%] bg-violet-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
                    {msg.content}
                  </div>
                ) : (
                  <div className="max-w-[90%] space-y-2">
                    <div className={`rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm ${msg.result?.erro ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-white border text-gray-700'}`}>
                      {msg.content}
                    </div>
                    {msg.result?.tipo === 'sql' && msg.result.dados && msg.result.dados.length > 0 && (
                      <div className="bg-white border rounded-xl overflow-hidden">
                        <div className="overflow-x-auto max-h-56">
                          <table className="text-xs w-full">
                            <thead className="bg-gray-50 sticky top-0">
                              <tr>{msg.result.colunas?.map(c => <th key={c} className="px-3 py-2 text-left font-medium text-gray-600 border-b whitespace-nowrap">{c}</th>)}</tr>
                            </thead>
                            <tbody>
                              {msg.result.dados.map((row, ri) => (
                                <tr key={ri} className="border-b last:border-0 hover:bg-gray-50">
                                  {msg.result!.colunas?.map(c => <td key={c} className="px-3 py-1.5 text-gray-700 whitespace-nowrap">{String(row[c] ?? '')}</td>)}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="px-3 py-1.5 text-xs text-gray-400 border-t">{msg.result.total} linha{msg.result.total !== 1 ? 's' : ''}</div>
                      </div>
                    )}
                    {msg.result?.sql && (
                      <div className="text-xs">
                        <button onClick={() => setSqlExpandido(sqlExpandido === i ? null : i)}
                          className="flex items-center gap-1 text-gray-400 hover:text-gray-600">
                          {sqlExpandido === i ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          Ver SQL
                        </button>
                        {sqlExpandido === i && (
                          <pre className="mt-1 bg-gray-900 text-green-400 rounded-lg px-3 py-2 overflow-x-auto text-xs">{msg.result.sql}</pre>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1">
                    {[0,1,2].map(i => <div key={i} className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{animationDelay:`${i*0.15}s`}} />)}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        <div className="border-t bg-white p-3 space-y-2">
          {anexo && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-violet-50 border border-violet-200 rounded-lg text-xs text-violet-700">
              <Paperclip className="w-3 h-3" />
              <span className="flex-1 truncate">{anexo.name}</span>
              <button onClick={() => setAnexo(null)}><X className="w-3 h-3" /></button>
            </div>
          )}
          <div className="flex gap-2">
            <input ref={fileInputRef} type="file" accept=".txt,.csv,.xlsx,.xls" className="hidden"
              onChange={e => setAnexo(e.target.files?.[0] ?? null)} />
            <button onClick={() => fileInputRef.current?.click()} disabled={loading}
              className="p-2.5 border rounded-xl hover:bg-gray-50 text-gray-500 disabled:opacity-50 transition-colors">
              <Paperclip className="w-4 h-4" />
            </button>
            <input
              value={pergunta}
              onChange={e => setPergunta(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && enviar()}
              placeholder={activeSession ? 'Pergunte sobre as tabelas...' : 'Clique em Novo chat ou escreva para começar...'}
              disabled={loading}
              className="flex-1 border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 disabled:opacity-50"
            />
            <button onClick={() => enviar()} disabled={(!pergunta.trim() && !anexo) || loading}
              className="p-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-gray-200 text-white rounded-xl transition-colors">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
