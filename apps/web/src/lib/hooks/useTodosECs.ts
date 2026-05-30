/**
 * Hook para carregar todos os ECs de todos os clientes
 */
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

type ApiErr = { response?: { data?: { detail?: string } } };

export function useTodosECs() {
  const [todosECs, setTodosECs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const carregarTodosECs = async () => {
      console.log('🔍 [useTodosECs] Iniciando carregamento de todos os ECs...');
      try {
        setLoading(true);
        setError(null);

        // Buscar todos os clientes
        console.log('📡 [useTodosECs] Buscando clientes...');
        const { data: clientes } = await apiClient.get('/clientes');
        console.log('✅ [useTodosECs] Clientes recebidos:', clientes.length, clientes);

        // Buscar ECs de cada cliente
        const todosECsSet = new Set<string>();
        
        for (const cliente of clientes) {
          try {
            console.log(`📡 [useTodosECs] Buscando ECs do cliente ${cliente.cliente_id}...`);
            const { data: ecsCliente } = await apiClient.get(
              `/clientes/${cliente.cliente_id}/ecs`
            );
            console.log(`✅ [useTodosECs] ECs do cliente ${cliente.cliente_id}:`, ecsCliente);
            console.log(`   Cliente: ${cliente.nome_fantasia || cliente.razao_social}`);
            console.log(`   ECs recebidos:`, ecsCliente);
            ecsCliente.forEach((ec: string) => {
              console.log(`   - Adicionando EC: ${ec}`);
              todosECsSet.add(ec);
            });
          } catch (err) {
            console.error(`❌ [useTodosECs] Erro ao carregar ECs do cliente ${cliente.cliente_id}:`, err);
          }
        }

        // Converter para array e ordenar
        const ecsArray = Array.from(todosECsSet).sort();
        console.log('✅ [useTodosECs] TODOS OS ECs CARREGADOS:', ecsArray.length, ecsArray);
        setTodosECs(ecsArray);
      } catch (err: unknown) {
        console.error('❌ [useTodosECs] ERRO CRÍTICO ao carregar ECs:', err);
        setError((err as ApiErr)?.response?.data?.detail || 'Erro ao carregar ECs');
      } finally {
        console.log('🏁 [useTodosECs] Carregamento finalizado. Loading = false');
        setLoading(false);
      }
    };

    carregarTodosECs();
  }, []);

  console.log('🎯 [useTodosECs] RETORNANDO:', { 
    todosECs_length: todosECs.length, 
    todosECs, 
    loading, 
    error 
  });

  return { todosECs, loading, error };
}
