'use client';
import { useState, useEffect } from 'react';
import { User, Key, Check, AlertCircle, Building2 } from 'lucide-react';
import { perfilApi, type MeuPerfil } from '@/lib/api/perfil';

export default function PerfilPage() {
  const [perfil, setPerfil] = useState<MeuPerfil | null>(null);
  const [senhaAtual, setSenhaAtual] = useState('');
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);

  useEffect(() => {
    perfilApi.getMeuPerfil().then(setPerfil).catch(() => {});
  }, []);

  const handleAlterarSenha = async (e: React.FormEvent) => {
    e.preventDefault();
    if (novaSenha !== confirmarSenha) {
      setMsg({ tipo: 'erro', texto: 'As senhas não coincidem.' });
      return;
    }
    if (novaSenha.length < 4) {
      setMsg({ tipo: 'erro', texto: 'A nova senha deve ter pelo menos 4 caracteres.' });
      return;
    }
    setLoading(true);
    setMsg(null);
    try {
      await perfilApi.alterarSenha(senhaAtual, novaSenha);
      setMsg({ tipo: 'ok', texto: 'Senha alterada com sucesso!' });
      setSenhaAtual('');
      setNovaSenha('');
      setConfirmarSenha('');
    } catch {
      setMsg({ tipo: 'erro', texto: 'Senha atual incorreta ou erro ao alterar.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-lg mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <User className="w-6 h-6 text-[#1e3a8a]" />
        <h1 className="text-xl font-bold text-gray-900">Meu Perfil</h1>
      </div>

      {/* Dados do perfil */}
      {perfil && (
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Dados da Conta</h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-500">Usuário</label>
              <p className="text-sm font-medium text-gray-900">{perfil.usuario}</p>
            </div>
            {perfil.nome && (
              <div>
                <label className="text-xs text-gray-500">Nome</label>
                <p className="text-sm font-medium text-gray-900">{perfil.nome}</p>
              </div>
            )}
            {perfil.empresa && (
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-gray-400" />
                <div>
                  <label className="text-xs text-gray-500">Empresa</label>
                  <p className="text-sm font-medium text-gray-900">{perfil.empresa}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Alterar senha */}
      <div className="bg-white rounded-xl border border-gray-100 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Key className="w-4 h-4 text-gray-500" />
          <h2 className="text-sm font-semibold text-gray-700">Alterar Senha</h2>
        </div>

        <form onSubmit={handleAlterarSenha} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Senha Atual</label>
            <input
              type="password"
              value={senhaAtual}
              onChange={e => setSenhaAtual(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a8a]/20 focus:border-[#1e3a8a]"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Nova Senha</label>
            <input
              type="password"
              value={novaSenha}
              onChange={e => setNovaSenha(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a8a]/20 focus:border-[#1e3a8a]"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Confirmar Nova Senha</label>
            <input
              type="password"
              value={confirmarSenha}
              onChange={e => setConfirmarSenha(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a8a]/20 focus:border-[#1e3a8a]"
            />
          </div>

          {msg && (
            <div
              className={`flex items-center gap-2 text-sm p-3 rounded-lg ${
                msg.tipo === 'ok' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}
            >
              {msg.tipo === 'ok' ? (
                <Check className="w-4 h-4" />
              ) : (
                <AlertCircle className="w-4 h-4" />
              )}
              {msg.texto}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-[#1e3a8a] text-white text-sm font-medium rounded-lg hover:bg-[#1e40af] disabled:opacity-50 transition-colors"
          >
            {loading ? 'Alterando...' : 'Alterar Senha'}
          </button>
        </form>
      </div>
    </div>
  );
}
