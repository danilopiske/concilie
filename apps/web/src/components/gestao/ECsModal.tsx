/**
 * ECs Modal
 * Modal para visualização e gestão de ECs do cliente
 * Migrado de modules/ui_gestao.py - visualização de ECs
 */
'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { gestaoApi } from '@/lib/api/gestao';

interface ECsModalProps {
  isOpen: boolean;
  onClose: () => void;
  clienteId: number | null;
  clienteNome: string;
}

export function ECsModal({ isOpen, onClose, clienteId, clienteNome }: ECsModalProps) {
  const [loading, setLoading] = useState(false);
  const [ecs, setEcs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && clienteId) {
      loadECs();
    }
  }, [isOpen, clienteId]);

  const loadECs = async () => {
    if (!clienteId) return;

    try {
      setLoading(true);
      setError(null);
      const detalhes = await gestaoApi.clientes.obter(clienteId);
      setEcs(detalhes.ecs || []);
    } catch (err) {
      setError('Erro ao carregar ECs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Estabelecimentos Comerciais - ${clienteNome}`}
      size="md"
      footer={
        <Button onClick={onClose}>Fechar</Button>
      }
    >
      {loading && (
        <div className="text-center py-8 text-gray-600 text-gray-400">
          Carregando...
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-100 bg-red-900 text-red-800 text-red-200 rounded">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div>
          {ecs.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-gray-400">
              Nenhum EC cadastrado para este cliente
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-600 text-gray-400 mb-4">
                Total de ECs: {ecs.length}
              </p>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {ecs.map((ec, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 bg-gray-700 rounded border border-gray-200 border-gray-600"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sm text-gray-900 text-white">
                        {ec}
                      </span>
                      <span className="text-xs text-gray-500 text-gray-400">
                        EC #{index + 1}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
