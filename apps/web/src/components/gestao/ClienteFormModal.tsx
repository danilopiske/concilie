/**
 * Cliente Form Modal
 * Formulário de edição/criação de cliente
 * Migrado de modules/ui_gestao.py - formulário de clientes
 */
'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { gestaoApi } from '@/lib/api/gestao';
import { Cliente } from '@/lib/types/gestao';

interface ClienteFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  cliente?: Cliente | null;
  onSaved: () => void;
}

interface FormData {
  cliente_id: string;
  nome_fantasia: string;
  razao_social: string;
  cnpj: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf_id: string;
  telefone1: string;
  telefone2: string;
  telefone3: string;
  email1: string;
  email2: string;
  banco: string;
  agencia: string;
  conta: string;
  ecs: string;
}

export function ClienteFormModal({ isOpen, onClose, cliente, onSaved }: ClienteFormModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    cliente_id: '',
    nome_fantasia: '',
    razao_social: '',
    cnpj: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf_id: '',
    telefone1: '',
    telefone2: '',
    telefone3: '',
    email1: '',
    email2: '',
    banco: '',
    agencia: '',
    conta: '',
    ecs: '',
  });

  useEffect(() => {
    if (cliente) {
      loadClienteDetalhes(cliente.cliente_id);
    } else {
      resetForm();
    }
  }, [cliente]);

  const loadClienteDetalhes = async (clienteId: number) => {
    try {
      setLoading(true);
      const detalhes = await gestaoApi.clientes.obter(clienteId);
      
      setFormData({
        cliente_id: detalhes.cliente_id.toString(),
        nome_fantasia: detalhes.nome_fantasia || '',
        razao_social: detalhes.razao_social || '',
        cnpj: detalhes.cnpj || '',
        logradouro: detalhes.endereco?.logradouro || '',
        numero: detalhes.endereco?.numero || '',
        complemento: detalhes.endereco?.complemento || '',
        bairro: detalhes.endereco?.bairro || '',
        cidade: detalhes.endereco?.cidade || '',
        uf_id: detalhes.endereco?.uf_id || '',
        telefone1: detalhes.contatos?.telefone1 || '',
          telefone2: detalhes.contatos?.telefone2 || '',
          telefone3: detalhes.contatos?.telefone3 || '',
          email1: detalhes.contatos?.email1 || '',
          email2: detalhes.contatos?.email2 || '',
        banco: detalhes.bancario?.banco || '',
        agencia: detalhes.bancario?.agencia || '',
        conta: detalhes.bancario?.conta || '',
        ecs: detalhes.ecs?.join(', ') || '',
      });
    } catch (err) {
      setError('Erro ao carregar detalhes do cliente');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      cliente_id: '',
      nome_fantasia: '',
      razao_social: '',
      cnpj: '',
      logradouro: '',
      numero: '',
      complemento: '',
      bairro: '',
      cidade: '',
      uf_id: '',
      telefone1: '',
      telefone2: '',
      telefone3: '',
      email1: '',
      email2: '',
      banco: '',
      agencia: '',
      conta: '',
      ecs: '',
    });
    setError(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.cliente_id || !formData.nome_fantasia.trim()) {
      setError('Cliente ID e Nome Fantasia são obrigatórios');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const dados = {
        cliente_id: parseInt(formData.cliente_id),
        nome_fantasia: formData.nome_fantasia,
        razao_social: formData.razao_social,
        cnpj: formData.cnpj,
        endereco: {
          logradouro: formData.logradouro,
          numero: formData.numero,
          complemento: formData.complemento,
          bairro: formData.bairro,
          cidade: formData.cidade,
          uf_id: formData.uf_id.toUpperCase(),
        },
        contatos: {
          telefone1: formData.telefone1,
          telefone2: formData.telefone2,
          telefone3: formData.telefone3,
          email1: formData.email1,
          email2: formData.email2,
        },
        bancario: {
          banco: formData.banco,
          agencia: formData.agencia,
          conta: formData.conta,
        },
        ecs: formData.ecs.split(',').map(ec => ec.trim()).filter(ec => ec),
      };

      if (cliente) {
        await gestaoApi.clientes.atualizar(cliente.cliente_id, dados);
      } else {
        await gestaoApi.clientes.criar(dados);
      }

      onSaved();
      onClose();
      resetForm();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao salvar cliente');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={cliente ? 'Editar Cliente' : 'Novo Cliente'}
      size="xl"
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
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-3 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded">
            {error}
          </div>
        )}

        {/* Dados Principais */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-900 dark:text-white">
            Dados Principais
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <Input
              name="cliente_id"
              label="Cliente ID"
              type="number"
              value={formData.cliente_id}
              onChange={handleChange}
              disabled={!!cliente}
              required
            />
            <Input
              name="cnpj"
              label="CNPJ"
              value={formData.cnpj}
              onChange={handleChange}
              placeholder="00.000.000/0000-00"
            />
            <Input
              name="nome_fantasia"
              label="Nome Fantasia"
              value={formData.nome_fantasia}
              onChange={handleChange}
              required
              className="col-span-2"
            />
            <Input
              name="razao_social"
              label="Razão Social"
              value={formData.razao_social}
              onChange={handleChange}
              className="col-span-2"
            />
          </div>
        </div>

        {/* Endereço */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-900 dark:text-white">
            Endereço
          </h4>
          <div className="grid grid-cols-4 gap-4">
            <Input
              name="logradouro"
              label="Logradouro"
              value={formData.logradouro}
              onChange={handleChange}
              className="col-span-3"
            />
            <Input
              name="numero"
              label="Número"
              value={formData.numero}
              onChange={handleChange}
            />
            <Input
              name="complemento"
              label="Complemento"
              value={formData.complemento}
              onChange={handleChange}
              className="col-span-2"
            />
            <Input
              name="bairro"
              label="Bairro"
              value={formData.bairro}
              onChange={handleChange}
              className="col-span-2"
            />
            <Input
              name="cidade"
              label="Cidade"
              value={formData.cidade}
              onChange={handleChange}
              className="col-span-3"
            />
            <Input
              name="uf_id"
              label="UF"
              value={formData.uf_id}
              onChange={handleChange}
              maxLength={2}
              placeholder="PR"
            />
          </div>
        </div>

        {/* Contatos */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-900 dark:text-white">
            Contatos
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <Input
              name="telefone1"
              label="Telefone 1"
              value={formData.telefone1}
              onChange={handleChange}
              placeholder="(41) 99999-9999"
            />
            <Input
              name="telefone2"
              label="Telefone 2"
              value={formData.telefone2}
              onChange={handleChange}
              placeholder="(41) 99999-9999"
            />
            <Input
              name="telefone3"
              label="Telefone 3"
              value={formData.telefone3}
              onChange={handleChange}
              placeholder="(41) 99999-9999"
            />
            <Input
              name="email1"
              label="Email 1"
              type="email"
              value={formData.email1}
              onChange={handleChange}
              placeholder="email@exemplo.com"
            />
            <Input
              name="email2"
              label="Email 2"
              type="email"
              value={formData.email2}
              onChange={handleChange}
              placeholder="email2@exemplo.com"
            />
          </div>
        </div>

        {/* Dados Bancários */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-900 dark:text-white">
            Dados Bancários
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <Input
              name="banco"
              label="Banco"
              value={formData.banco}
              onChange={handleChange}
            />
            <Input
              name="agencia"
              label="Agência"
              value={formData.agencia}
              onChange={handleChange}
            />
            <Input
              name="conta"
              label="Conta"
              value={formData.conta}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* ECs */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-900 dark:text-white">
            Estabelecimentos Comerciais (ECs)
          </h4>
          <Input
            name="ecs"
            label="ECs (separados por vírgula)"
            value={formData.ecs}
            onChange={handleChange}
            placeholder="12345, 67890, 11223"
          />
        </div>
      </form>
    </Modal>
  );
}
