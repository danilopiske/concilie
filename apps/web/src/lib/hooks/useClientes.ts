/**
 * Hook para gerenciar clientes
 * Baseado na lógica de ui_gestao.py do Panel
 */
'use client';

import { useState, useEffect } from 'react';
import { gestaoApi } from '@/lib/api/gestao';
import { Cliente, ClienteDetalhado, ClienteCreate } from '@/lib/types/gestao';

type ApiErr = { response?: { data?: { detail?: string } }; message?: string };

export function useClientes() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchClientes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await gestaoApi.clientes.listar();
      setClientes(data);
    } catch (err: unknown) {
      setError((err as ApiErr)?.response?.data?.detail || 'Erro ao carregar clientes');
      console.error('Erro ao buscar clientes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClientes();
  }, []);

  const criarCliente = async (cliente: ClienteCreate) => {
    try {
      const novoCliente = await gestaoApi.clientes.criar(cliente);
      await fetchClientes();
      return novoCliente;
    } catch (err: unknown) {
      throw new Error((err as ApiErr)?.response?.data?.detail || 'Erro ao criar cliente');
    }
  };

  const atualizarCliente = async (clienteId: number, cliente: Partial<ClienteCreate>) => {
    try {
      const clienteAtualizado = await gestaoApi.clientes.atualizar(clienteId, cliente);
      await fetchClientes();
      return clienteAtualizado;
    } catch (err: unknown) {
      throw new Error((err as ApiErr)?.response?.data?.detail || 'Erro ao atualizar cliente');
    }
  };

  const deletarCliente = async (clienteId: number) => {
    try {
      await gestaoApi.clientes.deletar(clienteId);
      await fetchClientes();
    } catch (err: unknown) {
      throw new Error((err as ApiErr)?.response?.data?.detail || 'Erro ao deletar cliente');
    }
  };

  return {
    clientes,
    loading,
    error,
    refetch: fetchClientes,
    criarCliente,
    atualizarCliente,
    deletarCliente,
  };
}

export function useClienteDetalhado(clienteId: number | null) {
  const [cliente, setCliente] = useState<ClienteDetalhado | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clienteId) {
      setCliente(null);
      return;
    }

    const fetchCliente = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await gestaoApi.clientes.obter(clienteId);
        setCliente(data);
      } catch (err: unknown) {
        setError((err as ApiErr)?.response?.data?.detail || 'Erro ao carregar cliente');
        console.error('Erro ao buscar cliente:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCliente();
  }, [clienteId]);

  return { cliente, loading, error };
}
