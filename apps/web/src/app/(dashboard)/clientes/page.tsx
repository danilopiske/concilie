'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Users, FileText } from 'lucide-react';
import { clientesApi, Cliente } from '@/lib/api/clientes';

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    clientesApi.listar()
      .then(setClientes)
      .catch(() => setError('Erro ao carregar clientes'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto pb-10 space-y-6">
      <div className="border-b pb-4 flex items-center gap-2">
        <Users className="w-6 h-6 text-gray-700" />
        <h1 className="text-2xl font-bold text-gray-800">Clientes</h1>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      {loading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">ID</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Nome Fantasia</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">CNPJ</th>
                <th className="px-4 py-3 text-center font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {clientes.map((c) => (
                <tr key={c.cliente_id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500">{c.cliente_id}</td>
                  <td className="px-4 py-3 font-medium">{c.nome_fantasia}</td>
                  <td className="px-4 py-3 text-gray-500">{c.cnpj}</td>
                  <td className="px-4 py-3 text-center">
                    <Link
                      href={`/clientes/${c.cliente_id}/extratos`}
                      className="inline-flex items-center gap-1 text-blue-600 hover:underline text-xs"
                    >
                      <FileText className="w-3 h-3" /> Extratos
                    </Link>
                  </td>
                </tr>
              ))}
              {clientes.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                    Nenhum cliente cadastrado
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
