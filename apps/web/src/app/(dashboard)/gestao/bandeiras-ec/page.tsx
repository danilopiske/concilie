/**
 * Página de Gestão de Bandeiras por EC
 * Migrado de modules/ui_gestao.py - aba "Bandeiras por EC"
 */
'use client';

import { useState, useEffect } from 'react';
import { useBandeiras } from '@/lib/hooks/useBandeiras';
import { useClientes } from '@/lib/hooks/useClientes';
import { useECs } from '@/lib/hooks/useECs';
import { useBandeirasPorEC } from '@/lib/hooks/useBandeirasPorEC';
import { Card, Button, Select, Checkbox, Alert } from '@/components/ui';
import { Loading } from '@/components/shared/Loading';
import { Breadcrumb } from '@/components/layout';

export default function BandeirasECPage() {
  // Hooks
  const { clientes, loading: loadingClientes } = useClientes();
  const { bandeiras, loading: loadingBandeiras } = useBandeiras();
  
  // State local
  const [selectedCliente, setSelectedCliente] = useState<string>('');
  const [selectedEC, setSelectedEC] = useState<string>('');
  const [localBandeirasState, setLocalBandeirasState] = useState<Record<string, boolean>>({});
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Carregar ECs quando cliente muda
    const clienteId = selectedCliente ? parseInt(selectedCliente, 10) : null;
    const { ecs, loading: loadingECs } = useECs(clienteId);

  const { 
    fetchBandeirasEC, 
    salvarBandeirasEC, 
    bandeirasEC, 
    loading: loadingSalvar,
    error 
  } = useBandeirasPorEC();

  // Carregar bandeiras do EC quando selecionado
  useEffect(() => {
    if (selectedEC) {
      fetchBandeirasEC(selectedEC);
    }
  }, [selectedEC, fetchBandeirasEC]);

  // Sincronizar estado local com dados vindos da API
  useEffect(() => {
    if (bandeirasEC && bandeiras.length > 0) {
      const newState: Record<string, boolean> = {};

      bandeiras.forEach(b => {
        // Se a bandeira existe no dict do EC, usar valor (1=true, 0=false)
        // Se não existe, usar o padrão da bandeira
        if (b.nome in bandeirasEC) {
          newState[b.nome] = bandeirasEC[b.nome] === 1;
        } else {
          newState[b.nome] = b.padrao; // Assumindo b.padrao como boolean
        }
      });

      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLocalBandeirasState(newState);
    }
  }, [bandeirasEC, bandeiras]);

  const handleClienteChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCliente(e.target.value);
    setSelectedEC(''); // Resetar EC ao mudar cliente
    setSuccessMsg(null);
  };

  const handleECChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newEC = e.target.value;
    setSelectedEC(newEC);
    if (!newEC) setLocalBandeirasState({});
    setSuccessMsg(null);
  };

  const handleCheckboxChange = (nomeBandeira: string, checked: boolean) => {
    setLocalBandeirasState(prev => ({
      ...prev,
      [nomeBandeira]: checked
    }));
    setSuccessMsg(null);
  };

  const handleSalvar = async () => {
    if (!selectedEC) return;
    
    // Converter booleanos para 0/1
    const payload: Record<string, number> = {};
    Object.entries(localBandeirasState).forEach(([key, value]) => {
      payload[key] = value ? 1 : 0;
    });

    try {
      await salvarBandeirasEC(selectedEC, payload);
      setSuccessMsg('Configuração salva com sucesso!');
    } catch (e) {
      // Erro já tratado no hook
    }
  };

  if (loadingClientes || loadingBandeiras) {
    return <Loading />;
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <Breadcrumb
        items={[
          { label: 'Gestão', href: '/gestao' },
          { label: 'Bandeiras por EC' },
        ]}
      />

      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Bandeiras por EC
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Selecione quais bandeiras cada estabelecimento aceita
          </p>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}
      {successMsg && <Alert variant="success" onClose={() => setSuccessMsg(null)}>{successMsg}</Alert>}

      <Card>
        <div className="space-y-6">
          {/* Seletores */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Cliente"
              value={selectedCliente}
              onChange={handleClienteChange}
              placeholder="Selecione um cliente"
              options={clientes.map(c => ({
                label: `${c.cliente_id} - ${c.nome_fantasia || c.razao_social}`,
                value: String(c.cliente_id)
              }))}
            />

            <Select
              label="Estabelecimento (EC)"
              value={selectedEC}
              onChange={handleECChange}
              disabled={!selectedCliente || loadingECs}
              placeholder={
                !selectedCliente 
                  ? "Selecione um cliente primeiro" 
                  : loadingECs 
                    ? "Carregando..." 
                    : "Selecione um EC"
              }
              options={ecs.map(ec => ({
                label: ec,
                value: ec
              }))}
            />
          </div>

          <hr className="border-gray-200" />

          {/* Lista de Bandeiras */}
          {!selectedEC ? (
            <div className="text-center py-8 text-gray-500">
              Selecione um EC para configurar as bandeiras
            </div>
          ) : (
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Bandeiras Disponíveis</h3>
              
              {bandeiras.length === 0 ? (
                <Alert variant="warning">
                  Nenhuma bandeira cadastrada no sistema. Vá em <a href="/gestao/bandeiras" className="underline">Gestão de Bandeiras</a> para cadastrar.
                </Alert>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {bandeiras.map(bandeira => (
                    <div key={bandeira.id} className="flex items-center space-x-2 p-2 border rounded hover:bg-gray-50">
                      <Checkbox
                        label={bandeira.nome}
                        checked={localBandeirasState[bandeira.nome] || false}
                        onChange={(checked) => handleCheckboxChange(bandeira.nome, checked)}
                      />
                    </div>
                  ))}
                </div>
              )}

              <div className="flex justify-end pt-4">
                <Button 
                  variant="primary" 
                  onClick={handleSalvar}
                  loading={loadingSalvar}
                  disabled={loadingSalvar}
                >
                  Salvar Configuração
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
