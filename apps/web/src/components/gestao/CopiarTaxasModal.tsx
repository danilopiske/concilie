/**
 * Modal para copiar taxas entre ECs
 * Replica funcionalidade do Panel
 */
'use client';

import { useState, useEffect } from 'react';
import { X, Copy, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { taxasApi, TaxaCopiarRequest, TaxaCopiarResponse } from '@/lib/api/taxas';
import { apiClient } from '@/lib/api/client';

interface CopiarTaxasModalProps {
  isOpen: boolean;
  onClose: () => void;
  contextoAtual: string;
  todosECs: string[];
  onCopiaCompleta?: () => void;
}

export function CopiarTaxasModal({
  isOpen,
  onClose,
  contextoAtual,
  todosECs: todosECsProp,
  onCopiaCompleta,
}: CopiarTaxasModalProps) {
  console.log('🎭 [CopiarTaxasModal] RENDER - Props recebidas:', {
    isOpen,
    contextoAtual,
    todosECs_length: todosECsProp?.length || 0,
    todosECs_sample: todosECsProp?.slice(0, 3),
  });

  const [todosECs, setTodosECs] = useState<string[]>(todosECsProp || []);
  const [ecOrigem, setEcOrigem] = useState('');
  const [ecsDestino, setEcsDestino] = useState<string[]>([]);
  const [sobrescrever, setSobrescrever] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingECs, setLoadingECs] = useState(false);
  const [resultado, setResultado] = useState<TaxaCopiarResponse | null>(null);
  const [error, setError] = useState('');

  // Atualizar todosECs quando props mudar
  useEffect(() => {
    if (todosECsProp && todosECsProp.length > 0) {
      console.log('✅ [CopiarTaxasModal] Atualizando ECs da prop:', todosECsProp);
      setTodosECs(todosECsProp);
    }
  }, [todosECsProp]);

  // Carregar ECs quando modal abrir (fallback se prop estiver vazia)
  useEffect(() => {
    const carregarECs = async () => {
      if (!isOpen || todosECs.length > 0) return;

      console.log('🔄 [CopiarTaxasModal] Carregando ECs diretamente...');
      setLoadingECs(true);

      try {
        // Buscar todos os clientes
        const { data: clientes } = await apiClient.get('/clientes');
        console.log('📡 [CopiarTaxasModal] Clientes:', clientes.length);

        // Buscar ECs de cada cliente
        const todosECsSet = new Set<string>();
        for (const cliente of clientes) {
          try {
            const { data: ecsCliente } = await apiClient.get(
              `/clientes/${cliente.cliente_id}/ecs`
            );
            ecsCliente.forEach((ec: string) => todosECsSet.add(ec));
          } catch (err) {
            console.error(`❌ Erro ao carregar ECs do cliente ${cliente.cliente_id}:`, err);
          }
        }

        const ecsArray = Array.from(todosECsSet).sort();
        console.log('✅ [CopiarTaxasModal] ECs carregados:', ecsArray);
        setTodosECs(ecsArray);
      } catch (err) {
        console.error('❌ [CopiarTaxasModal] Erro ao carregar ECs:', err);
        setError('Erro ao carregar lista de ECs');
      } finally {
        setLoadingECs(false);
      }
    };

    carregarECs();
  }, [isOpen, todosECs.length]);

  // Inicializar EC origem quando abrir modal
  useEffect(() => {
    console.log('🔄 [CopiarTaxasModal] useEffect disparado:', {
      isOpen,
      todosECs_length: todosECs?.length || 0,
      ecOrigem_atual: ecOrigem,
    });
    if (isOpen && todosECs.length > 0 && !ecOrigem) {
      console.log('✅ [CopiarTaxasModal] Inicializando EC origem:', todosECs[0]);
      setEcOrigem(todosECs[0]);
    }
  }, [isOpen, todosECs, ecOrigem]);

  const handleCopiar = async () => {
    // Validações
    if (!ecOrigem) {
      setError('Selecione um EC de origem');
      return;
    }

    if (ecsDestino.length === 0) {
      setError('Selecione pelo menos um EC de destino');
      return;
    }

    setError('');
    setResultado(null);
    setLoading(true);

    try {
      const request: TaxaCopiarRequest = {
        ec_origem: ecOrigem,
        ecs_destino: ecsDestino,
        sobrescrever,
        contexto: contextoAtual,
      };

      const response = await taxasApi.copiar(request);
      setResultado(response);

      // Callback para atualizar lista de taxas
      if (onCopiaCompleta) {
        onCopiaCompleta();
      }
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao copiar taxas');
    } finally {
      setLoading(false);
    }
  };

  const handleFechar = () => {
    setEcOrigem('');
    setEcsDestino([]);
    setSobrescrever(false);
    setResultado(null);
    setError('');
    onClose();
  };

  const toggleEcDestino = (ec: string) => {
    if (ecsDestino.includes(ec)) {
      setEcsDestino(ecsDestino.filter((e) => e !== ec));
    } else {
      setEcsDestino([...ecsDestino, ec]);
    }
  };

  const selecionarTodos = () => {
    const destinos = todosECs.filter((ec) => ec !== ecOrigem);
    setEcsDestino(destinos);
  };

  const limparSelecao = () => {
    setEcsDestino([]);
  };

  if (!isOpen) return null;

  // Filtrar ECs destino (não pode copiar para o mesmo EC)
  const ecsDestinoDisponiveis = todosECs.filter((ec) => ec !== ecOrigem);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Copy className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Copiar Taxas entre ECs
            </h2>
          </div>
          <button
            onClick={handleFechar}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Descrição */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Copie todas as taxas de um EC para outros ECs. Útil para replicar
              configurações entre estabelecimentos.
            </p>
          </div>

          {/* DEBUG INFO */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs font-mono text-yellow-900">
              🐛 DEBUG: todosECs.length = {todosECs?.length || 0} | 
              Array válido? {Array.isArray(todosECs) ? 'SIM' : 'NÃO'} |
              Amostra: [{todosECs?.slice(0, 2).join(', ')}]
            </p>
          </div>

          {/* EC Origem */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              EC de Origem
            </label>
            <select
              value={ecOrigem}
              onChange={(e) => {
                setEcOrigem(e.target.value);
                // Remove EC origem dos destinos se estiver selecionado
                setEcsDestino(ecsDestino.filter((ec) => ec !== e.target.value));
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
              disabled={loading || loadingECs || todosECs.length === 0}
            >
              {loadingECs ? (
                <option value="">Carregando ECs...</option>
              ) : todosECs.length === 0 ? (
                <option value="">Nenhum EC encontrado</option>
              ) : (
                <>
                  <option value="">Selecione...</option>
                  {todosECs.map((ec) => (
                    <option key={ec} value={ec}>
                      {ec}
                    </option>
                  ))}
                </>
              )}
            </select>
            {todosECs.length === 0 && !loadingECs && (
              <p className="text-xs text-red-500 mt-1">
                ⚠️ Nenhum EC disponível. Verifique se há clientes cadastrados.
              </p>
            )}
            {loadingECs && (
              <p className="text-xs text-gray-500 mt-1">
                Carregando lista de ECs...
              </p>
            )}
          </div>

          {/* ECs Destino */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                ECs de Destino (selecione um ou mais)
              </label>
              <div className="flex gap-2">
                <button
                  onClick={selecionarTodos}
                  className="text-xs text-blue-600 hover:text-blue-800"
                  disabled={loading || ecsDestinoDisponiveis.length === 0}
                >
                  Selecionar todos
                </button>
                <span className="text-gray-400">|</span>
                <button
                  onClick={limparSelecao}
                  className="text-xs text-blue-600 hover:text-blue-800"
                  disabled={loading || ecsDestino.length === 0}
                >
                  Limpar seleção
                </button>
              </div>
            </div>
            <div className="border border-gray-300 rounded-lg max-h-48 overflow-y-auto">
              {ecsDestinoDisponiveis.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  {ecOrigem
                    ? 'Nenhum outro EC disponível'
                    : 'Selecione um EC de origem primeiro'}
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {ecsDestinoDisponiveis.map((ec) => (
                    <label
                      key={ec}
                      className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={ecsDestino.includes(ec)}
                        onChange={() => toggleEcDestino(ec)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                      />
                      <span className="text-sm text-gray-700 font-mono">{ec}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
            {ecsDestino.length > 0 && (
              <p className="text-xs text-gray-600 mt-2">
                {ecsDestino.length} EC(s) selecionado(s)
              </p>
            )}
          </div>

          {/* Sobrescrever */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={sobrescrever}
                onChange={(e) => setSobrescrever(e.target.checked)}
                className="mt-0.5 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <div>
                <span className="text-sm font-medium text-gray-900">
                  Sobrescrever taxas existentes nos ECs de destino
                </span>
                <p className="text-xs text-gray-600 mt-1">
                  {sobrescrever
                    ? '⚠️ Taxas existentes nos destinos serão REMOVIDAS antes da cópia'
                    : 'Taxas existentes nos destinos serão mantidas (apenas novas serão adicionadas)'}
                </p>
              </div>
            </label>
          </div>

          {/* Erro */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-900">Erro</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Resultado */}
          {resultado && (
            <div className="space-y-3">
              {resultado.copiadas > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-green-900">
                      {resultado.copiadas} taxa(s) copiada(s) com sucesso!
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      De {ecOrigem} para {ecsDestino.length} EC(s)
                    </p>
                  </div>
                </div>
              )}

              {resultado.removidas > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-orange-900">
                    {resultado.removidas} taxa(s) removida(s) (sobrescrever ativado)
                  </p>
                </div>
              )}

              {resultado.erros && resultado.erros.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start gap-3 mb-2">
                    <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm font-medium text-red-900">
                      Erros encontrados:
                    </p>
                  </div>
                  <ul className="space-y-1 ml-8">
                    {resultado.erros.slice(0, 5).map((erro, idx) => (
                      <li key={idx} className="text-xs text-red-700">
                        • {erro}
                      </li>
                    ))}
                    {resultado.erros.length > 5 && (
                      <li className="text-xs text-red-700">
                        • ... e mais {resultado.erros.length - 5} erro(s)
                      </li>
                    )}
                  </ul>
                </div>
              )}

              {resultado.copiadas === 0 &&
                resultado.removidas === 0 &&
                (!resultado.erros || resultado.erros.length === 0) && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-sm text-gray-700">
                      Nenhuma operação realizada.
                    </p>
                  </div>
                )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={handleFechar}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            disabled={loading}
          >
            {resultado ? 'Fechar' : 'Cancelar'}
          </button>
          <button
            onClick={handleCopiar}
            disabled={loading || !ecOrigem || ecsDestino.length === 0}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Copiando...
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copiar Taxas
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
