// DeParaPage.tsx
// Tela de De-Para de Colunas para importação

"use client";
import React from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';

// TODO: Integrar com backend real para buscar e salvar mapeamentos

export default function DeParaPage() {
  // Estados de exemplo
  const [mapeamentos, setMapeamentos] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Exemplo de colunas
  const columns = [
    { key: 'coluna_origem', label: 'Coluna Origem' },
    { key: 'coluna_destino', label: 'Coluna Destino' },
    { key: 'tipo', label: 'Tipo' },
  ];

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
      <h1 className="font-title text-xl mb-2">De-Para de Colunas</h1>
      {/* TODO: Implementar tabela de mapeamento de colunas */}
      <Card>
        <div className="text-info">Em breve: mapeamento de colunas para importação.</div>
      </Card>
    </div>
  );
}
