/**
 * Componente de Gestão de Taxas
 * Formulário + Tabela + Copiar Taxas
 */

'use client';

import { useState } from 'react';
import { useTaxas } from '@/lib/hooks/useTaxas';
import { Taxa, TaxaCreate } from '@/lib/api/taxas';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { Card } from '@/components/ui/Card';
import { Table, TableColumn } from '@/components/ui/Table';
import { Checkbox } from '@/components/ui/Checkbox';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

interface TaxasFormProps {
  ec: string;
  contexto: string;
}

export function TaxasForm({ ec, contexto }: TaxasFormProps) {
  const { taxas, loading, error, adicionar, excluir, refetch } = useTaxas(ec, contexto);

  // Form state
  const [taxaGenerica, setTaxaGenerica] = useState(false);
  const [bandeira, setBandeira] = useState('');
  const [formaPagamento, setFormaPagamento] = useState('');
  const [parcelado, setParcelado] = useState<'S' | 'N'>('N');
  const [parcelasIni, setParcelasIni] = useState(1);
  const [parcelasFim, setParcelasFim] = useState(1);
  const [dataIni, setDataIni] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [taxa, setTaxa] = useState('');

  // UI state
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Taxa | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    // Validação
    if (!formaPagamento.trim() || parseFloat(taxa) <= 0 || !dataIni) {
      setFormError('Preencha forma de pagamento, taxa e data de início');
      return;
    }

    if (!taxaGenerica && !bandeira.trim()) {
      setFormError('Preencha a bandeira ou marque "Taxa Genérica"');
      return;
    }

    if (parcelasFim < parcelasIni) {
      setFormError('Parcela final deve ser maior ou igual à parcela inicial');
      return;
    }

    if (dataFim && dataFim < dataIni) {
      setFormError('Data fim deve ser maior ou igual à data de início');
      return;
    }

    try {
      const novaTaxa: TaxaCreate = {
        ec,
        bandeira: taxaGenerica ? null : bandeira.trim(),
        forma_pagamento: formaPagamento.trim().toUpperCase(),
        parcelado,
        parcelas_ini: parcelasIni,
        parcelas_fim: parcelasFim,
        data_ini: dataIni,
        data_fim: dataFim || null,
        taxa: parseFloat(taxa),
        contexto,
      };

      await adicionar(novaTaxa);
      
      const tipoTaxa = taxaGenerica ? 'genérica (todas bandeiras)' : 'específica';
      setSuccessMessage(`Taxa ${tipoTaxa} inserida com sucesso!`);

      // Limpar formulário
      setBandeira('');
      setFormaPagamento('');
      setParcelado('N');
      setParcelasIni(1);
      setParcelasFim(1);
      setDataFim('');
      setTaxa('');
      setTaxaGenerica(false);

    } catch (err) {
      // Erro já tratado no hook
    }
  };

  const handleDeleteClick = (taxa: Taxa) => {
    setConfirmDelete(taxa);
  };

  const handleConfirmDelete = async () => {
    if (!confirmDelete) return;

    try {
      setDeleting(true);
      setFormError(null);
      await excluir(confirmDelete.id);
      setSuccessMessage('Taxa deletada com sucesso!');
      setConfirmDelete(null);
    } catch (err) {
      setFormError('Erro ao deletar taxa');
    } finally {
      setDeleting(false);
    }
  };

  // Colunas da tabela
  const columns: TableColumn<Taxa>[] = [
    {
      key: 'id',
      label: 'ID',
      width: '60px',
    },
    {
      key: 'bandeira',
      label: 'Bandeira',
      width: '150px',
      render: (value) => value || <span className="text-blue-600 font-semibold">TODAS (Genérica)</span>,
    },
    {
      key: 'forma_pagamento',
      label: 'Forma Pagamento',
      width: '200px',
    },
    {
      key: 'parcelado',
      label: 'Parcelado',
      width: '100px',
      render: (value) => value === 'S' ? 'Sim' : 'Não',
    },
    {
      key: 'parcelas_ini',
      label: 'Parc. Ini',
      width: '80px',
    },
    {
      key: 'parcelas_fim',
      label: 'Parc. Fim',
      width: '80px',
    },
    {
      key: 'data_ini',
      label: 'Data Início',
      width: '120px',
      render: (value) => new Date(value).toLocaleDateString('pt-BR'),
    },
    {
      key: 'data_fim',
      label: 'Data Fim',
      width: '120px',
      render: (value) => value ? new Date(value).toLocaleDateString('pt-BR') : '-',
    },
    {
      key: 'taxa',
      label: 'Taxa (%)',
      width: '100px',
      render: (value) => parseFloat(value).toFixed(2) + '%',
    },
    {
      key: 'actions',
      label: 'Ações',
      width: '100px',
      render: (_, taxa) => (
        <Button
          variant="text"
          onClick={() => handleDeleteClick(taxa)}
          className="text-red-600 hover:text-red-700"
        >
          Deletar
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Mensagens */}
      {successMessage && (
        <Alert variant="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {(error || formError) && (
        <Alert variant="error" onClose={() => { setFormError(null); }}>
          {error || formError}
        </Alert>
      )}

      {/* Formulário de Inserção */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Taxa</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Taxa Genérica Checkbox */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <Checkbox
              label="Taxa Genérica (aplica a todas as bandeiras)"
              checked={taxaGenerica}
              onChange={setTaxaGenerica}
            />
            <p className="text-sm text-gray-600 mt-1 ml-6">
              Marque esta opção para criar uma taxa que se aplica a todas as bandeiras de cartão
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Bandeira */}
            <Input
              label="Bandeira"
              value={bandeira}
              onChange={(e) => setBandeira(e.target.value)}
              placeholder="Ex: Visa, Mastercard, Elo"
              disabled={taxaGenerica}
              helperText={taxaGenerica ? "Desabilitado para taxa genérica" : ""}
            />

            {/* Forma de Pagamento */}
            <Input
              label="Forma de Pagamento"
              value={formaPagamento}
              onChange={(e) => setFormaPagamento(e.target.value)}
              placeholder="Ex: CRÉDITO À VISTA"
              required
            />

            {/* Parcelado */}
            <div className="flex items-center h-full pt-6">
              <Checkbox
                label="Parcelado?"
                checked={parcelado === 'S'}
                onChange={(checked) => setParcelado(checked ? 'S' : 'N')}
              />
            </div>

            {/* Taxa */}
            <Input
              label="Taxa (%)"
              type="number"
              step="0.01"
              min="0"
              value={taxa}
              onChange={(e) => setTaxa(e.target.value)}
              placeholder="Ex: 2.35"
              required
            />

            {/* Parcelas Inicial */}
            <Input
              label="Parcela Inicial"
              type="number"
              min="1"
              value={parcelasIni}
              onChange={(e) => setParcelasIni(parseInt(e.target.value))}
              required
            />

            {/* Parcelas Final */}
            <Input
              label="Parcela Final"
              type="number"
              min="1"
              value={parcelasFim}
              onChange={(e) => setParcelasFim(parseInt(e.target.value))}
              required
            />

            {/* Data Início */}
            <Input
              label="Data de Início"
              type="date"
              value={dataIni}
              onChange={(e) => setDataIni(e.target.value)}
              required
            />

            {/* Data Fim */}
            <Input
              label="Data de Fim (opcional)"
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
            />
          </div>

          {/* Botão Inserir */}
          <div className="flex justify-end">
            <Button type="submit" variant="primary">
              Inserir Taxa
            </Button>
          </div>
        </form>
      </Card>

      {/* Tabela de Taxas */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Taxas Cadastradas
          </h3>
          <span className="text-sm text-gray-600">
            Total: {taxas.length}
          </span>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-600">
            Carregando taxas...
          </div>
        ) : taxas.length === 0 ? (
          <div className="text-center py-8 text-gray-600">
            Nenhuma taxa cadastrada para este EC
          </div>
        ) : (
          <Table
            variant="simple"
            columns={columns}
            data={taxas}
          />
        )}
      </Card>

      {/* Confirm Delete Dialog */}
      {confirmDelete && (
        <ConfirmDialog
          title="Confirmar Exclusão"
          message={`Deseja realmente deletar a taxa ${confirmDelete.bandeira || 'GENÉRICA'} - ${confirmDelete.forma_pagamento} (${confirmDelete.taxa}%)?`}
          confirmText="Deletar"
          cancelText="Cancelar"
          onConfirm={handleConfirmDelete}
          onClose={() => setConfirmDelete(null)}
          isOpen={!!confirmDelete}
          variant="danger"
          loading={deleting}
        />
      )}
    </div>
  );
}
