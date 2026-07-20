'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { gestaoApi } from '@/lib/api/gestao';
import { BandeiraDisponivel } from '@/lib/types/gestao';

interface BandeiraFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
  bandeira?: BandeiraDisponivel | null;
}

export function BandeiraFormModal({ isOpen, onClose, onSaved, bandeira }: BandeiraFormModalProps) {
  const isEditing = !!bandeira;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nome, setNome] = useState('');
  const [padrao, setPadrao] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setNome(bandeira?.nome ?? '');
      setPadrao(bandeira?.padrao ?? false);
      setError(null);
    }
  }, [isOpen, bandeira]);

  const handleSubmit = async () => {
    if (!nome.trim()) {
      setError('Nome é obrigatório');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      if (isEditing && bandeira) {
        await gestaoApi.bandeiras.atualizar(bandeira.id, { nome: nome.trim(), padrao });
      } else {
        await gestaoApi.bandeiras.criar({ nome: nome.trim(), padrao });
      }
      onSaved();
      onClose();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao salvar bandeira');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Editar Bandeira' : 'Nova Bandeira'}
      size="sm"
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
          label="Nome da Bandeira *"
          value={nome}
          onChange={e => setNome(e.target.value)}
          required
          placeholder="Ex: Visa, Mastercard, Elo"
        />

        <div className="flex items-center">
          <input
            type="checkbox"
            id="padrao"
            checked={padrao}
            onChange={e => setPadrao(e.target.checked)}
            className="h-4 w-4 text-blue-600 rounded"
          />
          <label htmlFor="padrao" className="ml-2 text-sm text-gray-700">
            Ativa por padrão
          </label>
        </div>
      </div>
    </Modal>
  );
}
