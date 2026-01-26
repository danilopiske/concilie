import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { Usuario, UsuarioCreate, UsuarioUpdate } from '@/lib/api/usuarios';
import { Button } from '../ui/Button';

interface UsuarioFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (dados: UsuarioCreate | UsuarioUpdate) => Promise<void>;
  usuarioEdit?: Usuario | null;
}

export function UsuarioFormModal({ isOpen, onClose, onSave, usuarioEdit }: UsuarioFormModalProps) {
  const [formData, setFormData] = useState({
    usuario: '',
    nome: '',
    empresa: '',
    senha: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (usuarioEdit) {
      setFormData({
        usuario: usuarioEdit.usuario,
        nome: usuarioEdit.nome || '',
        empresa: usuarioEdit.empresa || '',
        senha: '', // Password not shown
      });
    } else {
      setFormData({
        usuario: '',
        nome: '',
        empresa: '',
        senha: '',
      });
    }
  }, [usuarioEdit, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload: any = {
        usuario: formData.usuario,
        nome: formData.nome || undefined,
        empresa: formData.empresa || undefined,
      };
      
      // Only include password if set (always required for create, optional for update)
      if (formData.senha) {
        payload.senha = formData.senha;
      }

      await onSave(payload);
      onClose();
    } catch (error) {
      console.error('Error saving user:', error);
      alert('Erro ao salvar usuário.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900">
            {usuarioEdit ? 'Editar Usuário' : 'Novo Usuário'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Usuário (Login) *
            </label>
            <input
              type="text"
              required
              value={formData.usuario}
              onChange={(e) => setFormData({ ...formData, usuario: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome
            </label>
            <input
              type="text"
              value={formData.nome}
              onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Empresa
            </label>
            <input
              type="text"
              value={formData.empresa}
              onChange={(e) => setFormData({ ...formData, empresa: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Senha {usuarioEdit && '(deixe em branco para manter)'} {!usuarioEdit && '*'}
            </label>
            <input
              type="password"
              required={!usuarioEdit}
              value={formData.senha}
              onChange={(e) => setFormData({ ...formData, senha: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md disabled:opacity-50"
            >
              Cancelar
            </button>
            <Button
              type="submit"
              loading={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Salvar
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
