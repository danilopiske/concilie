import { Edit, Trash2 } from 'lucide-react';
import { Usuario } from '@/lib/api/usuarios';

interface UsuariosTableProps {
  usuarios: Usuario[];
  onEdit: (usuario: Usuario) => void;
  onDelete: (usuario: Usuario) => void;
}

export function UsuariosTable({ usuarios, onEdit, onDelete }: UsuariosTableProps) {
  return (
    <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-gray-200">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-600">
          <thead className="bg-gray-50 text-xs uppercase font-medium text-gray-500">
            <tr>
              <th className="px-6 py-3">ID</th>
              <th className="px-6 py-3">Usuário</th>
              <th className="px-6 py-3">Nome</th>
              <th className="px-6 py-3">Empresa</th>
              <th className="px-6 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 divide-gray-700">
            {usuarios.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  Nenhum usuário cadastrado.
                </td>
              </tr>
            ) : (
              usuarios.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 hover:bg-gray-750 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs">{user.id}</td>
                  <td className="px-6 py-4 font-medium text-gray-900">{user.usuario}</td>
                  <td className="px-6 py-4">{user.nome || '-'}</td>
                  <td className="px-6 py-4">{user.empresa || '-'}</td>
                  <td className="px-6 py-4 text-right flex justify-end gap-2">
                    <button
                      onClick={() => onEdit(user)}
                      className="p-1 text-blue-600 hover:text-blue-800 text-blue-400 hover:text-blue-300 transition-colors"
                      title="Editar"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => onDelete(user)}
                      className="p-1 text-red-600 hover:text-red-800 text-red-400 hover:text-red-300 transition-colors"
                      title="Excluir"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
