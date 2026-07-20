/**
 * Contexto Form Modal
 * Formulário de edição/criação de contexto
 * Migrado de conf/funcoesbd.py - contexto_inserir, contexto_atualizar
 */
'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { gestaoApi } from '@/lib/api/gestao';
import { Contexto } from '@/lib/types/gestao';

interface ContextoFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  contexto?: Contexto | null;
  onSaved: () => void;
}

interface FormData {
  nome: string;
  descricao: string;
  ativo: boolean;
}

export function ContextoFormModal({ isOpen, onClose, contexto, onSaved }: ContextoFormModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    nome: '',
    descricao: '',
    ativo: true,
  });

  useEffect(() => {
    if (contexto) {
      setFormData({
        nome: contexto.nome || '',
        descricao: contexto.descricao || '',
        ativo: contexto.ativo ?? true,
      });
    } else {
      resetForm();
    }
  }, [contexto, isOpen]);

  const resetForm = () => {
    setFormData({
      nome: '',
      descricao: '',
      ativo: true,
    });
    setError(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!formData.nome.trim()) {
        setError('Nome é obrigatório');
        return;
      }

      const dados = {
        nome: formData.nome.trim(),
        descricao: formData.descricao.trim() || undefined,
        ativo: formData.ativo,
      };

      if (contexto) {
        await gestaoApi.contextos.atualizar(contexto.id, dados);
      } else {
        await gestaoApi.contextos.criar(dados);
      }

      onSaved();
      onClose();
      resetForm();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao salvar contexto');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={contexto ? 'Editar Contexto' : 'Novo Contexto'}
      size="md"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Salvando...' : 'Salvar'}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <Input
          name="nome"
          label="Nome *"
          value={formData.nome}
          onChange={handleChange}
          required
          placeholder="Ex: Cielo, Rede, GetNet"
        />

        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700">
            Descrição
          </label>
          <textarea
            name="descricao"
            value={formData.descricao}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900"
            placeholder="Descrição do contexto (opcional)"
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            name="ativo"
            id="ativo"
            checked={formData.ativo}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 rounded"
          />
          <label htmlFor="ativo" className="ml-2 text-sm text-gray-700">
            Ativo
          </label>
        </div>
      </div>
    </Modal>
  );
}
