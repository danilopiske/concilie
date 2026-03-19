'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Table, TableColumn } from '@/components/ui/Table';
import { Panel } from '@/components/ui/Panel';
import { Tags, Plus, Pencil, Trash2, AlertCircle, Loader2 } from 'lucide-react';
import { relatorioTagsApi, RelatorioTag, RelatorioTagCreate, RelatorioTagUpdate } from '@/lib/api/relatorio-tags';

const TIPOS: RelatorioTag['tipo'][] = ['secao', 'clausula', 'assinatura', 'cabecalho', 'rodape'];

const TIPO_LABELS: Record<RelatorioTag['tipo'], string> = {
  secao: 'Seção',
  clausula: 'Cláusula',
  assinatura: 'Assinatura',
  cabecalho: 'Cabeçalho',
  rodape: 'Rodapé',
};

const emptyForm = (): RelatorioTagCreate => ({
  nome: '',
  tipo: 'secao',
  descricao: '',
  conteudo_padrao: '',
  ativo: true,
});

export default function RelatorioTagsPage() {
  const [tags, setTags] = useState<RelatorioTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Modal de criação/edição
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<RelatorioTag | null>(null);
  const [form, setForm] = useState<RelatorioTagCreate>(emptyForm());
  const [formError, setFormError] = useState<string | null>(null);

  // Modal de confirmação de exclusão
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const fetchTags = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await relatorioTagsApi.listar('all');
      setTags(data);
    } catch {
      setError('Erro ao carregar tags.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTags(); }, []);

  const openCreate = () => {
    setEditingTag(null);
    setForm(emptyForm());
    setFormError(null);
    setModalOpen(true);
  };

  const openEdit = (tag: RelatorioTag) => {
    setEditingTag(tag);
    setForm({
      nome: tag.nome,
      tipo: tag.tipo,
      descricao: tag.descricao ?? '',
      conteudo_padrao: tag.conteudo_padrao,
      ativo: tag.ativo,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.nome.trim()) { setFormError('Nome é obrigatório.'); return; }
    if (!form.conteudo_padrao.trim()) { setFormError('Conteúdo padrão é obrigatório.'); return; }

    try {
      setSaving(true);
      setFormError(null);
      if (editingTag) {
        const update: RelatorioTagUpdate = {
          nome: form.nome,
          tipo: form.tipo,
          descricao: form.descricao || undefined,
          conteudo_padrao: form.conteudo_padrao,
          ativo: form.ativo,
        };
        await relatorioTagsApi.atualizar(editingTag.id, update);
      } else {
        await relatorioTagsApi.criar(form);
      }
      setModalOpen(false);
      await fetchTags();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Erro ao salvar tag.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (deleteId === null) return;
    try {
      await relatorioTagsApi.excluir(deleteId);
      setDeleteId(null);
      await fetchTags();
    } catch {
      setError('Erro ao excluir tag.');
      setDeleteId(null);
    }
  };

  const columns: TableColumn<RelatorioTag>[] = [
    {
      key: 'nome',
      label: 'Nome',
      render: (val, row) => (
        <span className={`font-semibold text-sm ${!row.ativo ? 'text-gray-400 line-through' : 'text-gray-800'}`}>
          {val}
        </span>
      ),
    },
    {
      key: 'tipo',
      label: 'Tipo',
      render: (val) => (
        <Badge variant="info">{TIPO_LABELS[val as RelatorioTag['tipo']] ?? val}</Badge>
      ),
    },
    {
      key: 'descricao',
      label: 'Descrição',
      render: (val) => (
        <span className="text-sm text-gray-500">{val || '—'}</span>
      ),
    },
    {
      key: 'ativo',
      label: 'Status',
      render: (val) => val
        ? <Badge variant="success">Ativa</Badge>
        : <Badge variant="default">Inativa</Badge>,
    },
    {
      key: 'actions',
      label: '',
      width: '100px',
      render: (_, row) => (
        <div className="flex gap-2 justify-end">
          <Button size="sm" variant="secondary" onClick={() => openEdit(row)}>
            <Pencil className="h-3 w-3" />
          </Button>
          <Button size="sm" variant="danger" onClick={() => setDeleteId(row.id)}>
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 flex items-center gap-1">
        <Link href="/relatorios" className="hover:text-primary transition-colors">Relatórios</Link>
        <span>/</span>
        <span className="font-semibold text-gray-800">Gerenciar Tags</span>
      </nav>

      <Panel>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Tags className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">Tags de Relatório</h1>
              <p className="text-sm text-gray-500">Seções inseríveis via <code>/</code> no editor</p>
            </div>
          </div>
          <Button variant="primary" onClick={openCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Tag
          </Button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg mb-4 text-red-700 text-sm">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : tags.length === 0 ? (
          <div className="text-center py-16 border-2 border-dashed border-gray-100 rounded-3xl text-gray-400">
            <Tags className="h-12 w-12 mx-auto mb-3 text-gray-200" />
            <p>Nenhuma tag cadastrada ainda.</p>
          </div>
        ) : (
          <Table data={tags} columns={columns} pagination pageSize={10} />
        )}
      </Panel>

      {/* Modal criar/editar */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingTag ? 'Editar Tag' : 'Nova Tag'}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button variant="primary" onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Salvar
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {formError && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {formError}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome <span className="text-red-500">*</span></label>
              <Input
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
                placeholder="ex: clausula_contratual"
                maxLength={50}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo <span className="text-red-500">*</span></label>
              <select
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value as RelatorioTag['tipo'] })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                {TIPOS.map((t) => (
                  <option key={t} value={t}>{TIPO_LABELS[t]}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
            <Input
              value={form.descricao ?? ''}
              onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              placeholder="Breve descrição exibida no menu do editor"
              maxLength={200}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Conteúdo Padrão <span className="text-red-500">*</span>
            </label>
            <textarea
              value={form.conteudo_padrao}
              onChange={(e) => setForm({ ...form, conteudo_padrao: e.target.value })}
              rows={6}
              placeholder="HTML ou texto que será inserido no editor ao selecionar esta tag"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="ativo"
              checked={form.ativo}
              onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
              className="rounded"
            />
            <label htmlFor="ativo" className="text-sm text-gray-700">Tag ativa (aparece no menu do editor)</label>
          </div>
        </div>
      </Modal>

      {/* Modal confirmação exclusão */}
      <Modal
        isOpen={deleteId !== null}
        onClose={() => setDeleteId(null)}
        title="Confirmar exclusão"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteId(null)}>Cancelar</Button>
            <Button variant="danger" onClick={handleDelete}>Excluir</Button>
          </>
        }
      >
        <p className="text-gray-700">A tag será marcada como inativa e não aparecerá mais no editor. Confirma?</p>
      </Modal>
    </div>
  );
}
