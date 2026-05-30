
import { useState, useEffect, useRef } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Checkbox } from '@/components/ui/Checkbox';
import { DeParaRule, DeParaCreate } from '@/lib/types/importacao';
import { deparaApi } from '@/lib/api/depara';

interface DeParaFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: DeParaCreate) => Promise<void>;
  initialData?: DeParaRule | null;
}

export function DeParaFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
}: DeParaFormModalProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<Partial<DeParaCreate>>({
    ativo: 1,
    tipo_origem: 'V',
    tipo_preenchimento: 'importado',
    contexto: '',
    destino_nome: '',
    origem_nome: '',
    valor_padrao: ''
  });

  const [systemColumns, setSystemColumns] = useState<string[]>([]);
  const [fileHeaders, setFileHeaders] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load initial data
  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData({ ...initialData });
      } else {
        setFormData({
            ativo: 1,
            tipo_origem: 'V',
            tipo_preenchimento: 'importado',
            contexto: '',
            destino_nome: '',
            origem_nome: '',
            valor_padrao: ''
        });
      }
      setFileHeaders([]);
    }
  }, [isOpen, initialData]);

  // Load system columns when type changes
  useEffect(() => {
    const fetchColumns = async () => {
      try {
        const tipo = formData.tipo_origem || 'V';
        const cols = await deparaApi.listarColunasSistema(tipo);
        setSystemColumns(cols);
      } catch (error) {
        console.error("Erro ao carregar colunas sistema", error);
        setSystemColumns([]);
      }
    };
    if (isOpen) fetchColumns();
  }, [isOpen, formData.tipo_origem]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setLoading(true);
      const response = await deparaApi.lerCabecalhos(file);
      setFileHeaders(response.headers || []);
    } catch (err) {
      console.error(err);
      alert('Erro ao ler arquivo');
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    if (!formData.contexto || !formData.destino_nome) {
      alert('Contexto e Destino são obrigatórios');
      return;
    }
    if (formData.tipo_preenchimento === 'importado' && !formData.origem_nome) {
      alert('Para preenchimento "Importado", a Origem é obrigatória');
      return;
    }
    
    try {
      setLoading(true);
      await onSave(formData as DeParaCreate);
      onClose();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? `Editar Regra #${initialData.id}` : 'Nova Regra De-Para'}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
            <Select
                label="Contexto"
                value={formData.contexto || ''}
                onChange={(e) => setFormData({ ...formData, contexto: e.target.value })}
                options={[
                    { label: 'Selecione...', value: '' },
                    { label: 'CIELO', value: 'CIELO' },
                    { label: 'REDE', value: 'REDE' },
                    { label: 'GETNET', value: 'GETNET' },
                    { label: 'STONE', value: 'STONE' },
                    { label: 'BIN', value: 'BIN' },
                    { label: 'SAFE2PAY', value: 'SAFE2PAY' },
                    { label: 'VINDI', value: 'VINDI' }
                ]}
            />
            <Select
                label="Tipo"
                value={formData.tipo_origem || 'V'}
                onChange={(e) => setFormData({ ...formData, tipo_origem: e.target.value })}
                options={[
                    { label: 'Venda', value: 'V' },
                    { label: 'Lançamento', value: 'L' },
                    { label: 'Recebível', value: 'R' },
                ]}
            />
        </div>

        <div className="grid grid-cols-2 gap-4">
            <Select
                label="Destino (Sistema)"
                value={formData.destino_nome || ''}
                onChange={(e) => setFormData({ ...formData, destino_nome: e.target.value })}
                options={[
                    { label: 'Selecione...', value: '' },
                    ...systemColumns.map(c => ({ label: c, value: c }))
                ]}
            />
             <Select
                label="Preenchimento"
                value={formData.tipo_preenchimento || 'importado'}
                onChange={(e) => setFormData({ ...formData, tipo_preenchimento: e.target.value })}
                options={[
                    { label: 'Importado', value: 'importado' },
                    { label: 'Padrão', value: 'padrão' },
                    { label: 'Sistema', value: 'sistema' },
                    { label: 'Ignorar', value: 'ignorar' },
                ]}
            />
        </div>

        {/* Origem Row with File Upload */}
        <div className="flex gap-2 items-end">
             <div className="flex-1">
                 {fileHeaders.length > 0 ? (
                    <Select
                        label="Origem (Arquivo)"
                        value={formData.origem_nome || ''}
                        onChange={(e) => setFormData({ ...formData, origem_nome: e.target.value })}
                        options={[{ label: 'Selecione...', value: '' }, ...fileHeaders.map(h => ({ label: h, value: h }))]}
                    />
                 ) : (
                    <Input
                        label="Origem (Arquivo)"
                        placeholder="Ex: Dat. Venda"
                        value={formData.origem_nome || ''}
                        onChange={(e) => setFormData({ ...formData, origem_nome: e.target.value })}
                    />
                 )}
             </div>
             <div className="pb-1">
                <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    accept=".csv,.xls,.xlsx" 
                    onChange={handleFileUpload} 
                />
                <Button size="sm" variant="secondary" onClick={() => fileInputRef.current?.click()} loading={loading}>
                    📂 Ler
                </Button>
             </div>
        </div>

        <Input
            label="Valor Padrão"
            value={formData.valor_padrao || ''}
            onChange={(e) => setFormData({ ...formData, valor_padrao: e.target.value })}
            placeholder="Apenas se preenchimento = Padrão"
        />

        <div className="flex items-center gap-2">
            <Checkbox
                label="Ativo"
                checked={formData.ativo === 1}
                onChange={(checked) => setFormData({ ...formData, ativo: checked ? 1 : 0 })}
            />
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="secondary" onClick={onClose} disabled={loading}>
                Cancelar
            </Button>
            <Button onClick={handleSubmit} loading={loading}>
                Salvar
            </Button>
        </div>
      </div>
    </Modal>
  );
}
