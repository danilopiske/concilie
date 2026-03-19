/**
 * Bandeira Form Modal
 * Formulário de criação de bandeira
 */
'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { gestaoApi } from '@/lib/api/gestao';

interface BandeiraFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
}

interface FormData {
  nome: string;
  padrao: boolean;
}

export function BandeiraFormModal({ isOpen, onClose, onSaved }: BandeiraFormModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    nome: '',
    padrao: false,
  });

  const resetForm = () => {
    setFormData({
      nome: '',
      padrao: false,
    });
    setError(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
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

      await gestaoApi.bandeiras.criar({
        nome: formData.nome.trim(),
        padrao: formData.padrao,
      });

      onSaved();
      onClose();
      resetForm();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao criar bandeira');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    onClose();
    resetForm();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Nova Bandeira"
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={handleClose} disabled={loading}>
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
          value={formData.nome}
          onChange={handleChange}
          required
          placeholder="Ex: Visa, Mastercard, Elo"
        />

        <div className="flex items-center">
          <input
            type="checkbox"
            name="padrao"
            id="padrao"
            checked={formData.padrao}
            onChange={handleChange}
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
