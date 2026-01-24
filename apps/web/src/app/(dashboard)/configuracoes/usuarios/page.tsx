'use client';

import { useEffect, useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { UsuariosTable } from '@/components/configuracoes/UsuariosTable';
import { UsuarioFormModal } from '@/components/configuracoes/UsuarioFormModal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Usuario, UsuarioCreate, UsuarioUpdate, usuariosApi } from '@/lib/api/usuarios';

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<Usuario | null>(null);

  // Delete State
  const [userToDelete, setUserToDelete] = useState<Usuario | null>(null);

  const fetchUsuarios = async () => {
    setLoading(true);
    try {
      const data = await usuariosApi.listar();
      setUsuarios(data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      // alert('Erro ao carregar usuários.'); // Optional: Toast notification
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsuarios();
  }, []);

  const handleSave = async (dados: UsuarioCreate | UsuarioUpdate) => {
    try {
      if (editingUser) {
        await usuariosApi.atualizar(editingUser.id, dados);
      } else {
        await usuariosApi.criar(dados as UsuarioCreate);
      }
      await fetchUsuarios();
    } catch (error) {
      throw error; // Let modal handle error display
    }
  };

  const handleDelete = async () => {
    if (!userToDelete) return;
    try {
      await usuariosApi.deletar(userToDelete.id);
      await fetchUsuarios();
      setUserToDelete(null);
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Erro ao excluir usuário.');
    }
  };

  const filteredUsuarios = usuarios.filter(u => 
    u.usuario.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.nome && u.nome.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (u.empresa && u.empresa.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 text-white">Gerenciar Usuários</h1>
          <p className="text-gray-500 text-gray-400">Cadastre e gerencie o acesso ao sistema</p>
        </div>
        
        <Button onClick={() => { setEditingUser(null); setIsModalOpen(true); }}>
          <Plus size={20} className="mr-2" />
          Novo Usuário
        </Button>
      </div>

      <div className="flex items-center bg-white bg-gray-800 border rounded-md px-3 py-2 max-w-md">
        <Search className="text-gray-400 mr-2" size={20} />
        <input
          type="text"
          placeholder="Buscar por nome, login ou empresa..."
          className="bg-transparent border-none outline-none w-full text-gray-700 text-gray-200 placeholder-gray-400"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-500">Carregando usuários...</p>
        </div>
      ) : (
        <UsuariosTable
          usuarios={filteredUsuarios}
          onEdit={(u) => { setEditingUser(u); setIsModalOpen(true); }}
          onDelete={(u) => setUserToDelete(u)}
        />
      )}

      <UsuarioFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        usuarioEdit={editingUser}
      />

      <ConfirmDialog
        isOpen={!!userToDelete}
        title="Excluir Usuário"
        message={`Tem certeza que deseja excluir o usuário "${userToDelete?.usuario}"? Esta ação não pode ser desfeita.`}
        confirmLabel="Excluir"
        type="danger"
        onConfirm={handleDelete}
        onCancel={() => setUserToDelete(null)}
      />
    </div>
  );
}
