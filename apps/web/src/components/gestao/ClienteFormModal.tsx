'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { gestaoApi } from '@/lib/api/gestao';
import { Cliente } from '@/lib/types/gestao';
import { X, Plus } from 'lucide-react';

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
  ecs: string[]; // Changed to array
}

export function ClienteFormModal({ isOpen, onClose, cliente, onSaved }: ClienteFormModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newEc, setNewEc] = useState(''); // State for the new EC input
  
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
    ecs: [],
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
        ecs: detalhes.ecs || [], // Expecting array from API, fallback to empty
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
      ecs: [],
    });
    setNewEc('');
    setError(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // EC Handling
  const handleAddEc = () => {
    if (!newEc.trim()) return;
    const cleanEc = newEc.trim();
    
    // Prevent duplicates
    if (formData.ecs.includes(cleanEc)) {
      setNewEc('');
      return;
    }

    setFormData(prev => ({
      ...prev,
      ecs: [...prev.ecs, cleanEc]
    }));
    setNewEc('');
  };

  const handleKeyDownEc = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddEc();
    }
  };

  const handleRemoveEc = (ecToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      ecs: prev.ecs.filter(ec => ec !== ecToRemove)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.nome_fantasia.trim()) {
      setError('Nome Fantasia é obrigatório');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const dados: any = { // Use any safely here or create proper type
        // cliente_id: parseInt(formData.cliente_id), // Don't force this anymore
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
        ecs: formData.ecs, // Already an array
      };

      if (formData.cliente_id) {
          dados.cliente_id = parseInt(formData.cliente_id);
      }

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
          <div className="p-3 bg-red-100 border border-red-200 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {/* Dados Principais */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-900">
            Dados Principais
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <Input
              name="cliente_id"
              label="Cliente ID"
              type="text"
              value={cliente ? formData.cliente_id : 'Automático'}
              onChange={handleChange}
              disabled={true} // Always disabled, auto-generated or PK
              className={!cliente ? 'text-gray-500 bg-gray-50' : ''}
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
          <h4 className="text-md font-semibold mb-3 text-gray-900">
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
          <h4 className="text-md font-semibold mb-3 text-gray-900">
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
          <h4 className="text-md font-semibold mb-3 text-gray-900">
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

        {/* ECs Selector */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-900">
            Estabelecimentos Comerciais (ECs)
          </h4>
          
          <div className="space-y-3">
            <div className="flex gap-2 items-end">
              <div className="flex-1">
                <Input
                  name="newEc"
                  label="Adicionar EC"
                  value={newEc}
                  onChange={(e) => setNewEc(e.target.value)}
                  onKeyDown={handleKeyDownEc}
                  placeholder="Digite o código EC"
                />
              </div>
              <Button type="button" onClick={handleAddEc} variant="secondary">
                <Plus size={18} className="mr-1" />
                Adicionar
              </Button>
            </div>

            <div className="flex flex-wrap gap-2 min-h-[40px] p-2 border border-gray-200 rounded-md bg-gray-50">
              {formData.ecs.length === 0 && (
                <span className="text-gray-400 text-sm italic py-1 px-2">
                  Nenhum EC vinculado
                </span>
              )}
              {formData.ecs.map((ec, index) => (
                <Badge key={`${ec}-${index}`} variant="info" className="flex items-center gap-1 pr-1">
                  {ec}
                  <button
                    type="button"
                    onClick={() => handleRemoveEc(ec)}
                    className="hover:bg-blue-200 rounded-full p-0.5 transition-colors focus:outline-none"
                    title="Remover EC"
                  >
                    <X size={14} />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </form>
    </Modal>
  );
}
