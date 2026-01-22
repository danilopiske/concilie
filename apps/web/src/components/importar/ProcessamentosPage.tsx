"use client";
// ProcessamentosPage.tsx
// Tela de Gestão de Processamentos de Importação

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';

// TODO: Integrar com backend real para listar e deletar processamentos

export default function ProcessamentosPage() {
  // Estados de exemplo
  const [processamentos, setProcessamentos] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<number[]>([]);

  // Exemplo de colunas
  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'arquivo', label: 'Arquivo' },
    { key: 'data', label: 'Data' },
    { key: 'usuario', label: 'Usuário' },
    { key: 'status', label: 'Status' },
  ];

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      <h1 className="font-title text-xl mb-2">Gestão de Processamentos</h1>
      {/* TODO: Implementar tabela de processamentos */}
      <Card>
        <div className="text-info">Em breve: gestão de processamentos de importação.</div>
      </Card>
    </div>
  );
}
