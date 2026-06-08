'use client';

import { usePermissoes } from '@/hooks/usePermissoes';
import type { Perfil } from '@/lib/api/permissoes';

interface ProtectedRouteProps {
  modulo?: string;
  children: React.ReactNode;
  /** Perfis permitidos (override da tabela padrão) */
  roles?: Perfil[];
  /** Tela liberada individualmente por usuário (conversor, ia) */
  telaEspecifica?: string;
}

export function ProtectedRoute({ modulo, children, roles, telaEspecifica }: ProtectedRouteProps) {
  const { permissao, loading, podeAcessar, podeAcessarTela } = usePermissoes();

  if (loading) return null;

  let permitido: boolean;
  if (telaEspecifica) {
    permitido = podeAcessarTela(telaEspecifica);
  } else if (roles) {
    permitido = !!(permissao && roles.includes(permissao.perfil));
  } else {
    permitido = podeAcessar(modulo ?? '');

  }

  if (!permitido) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[60vh] gap-4 text-center px-6">
        <div className="text-5xl">🔒</div>
        <h2 className="text-xl font-semibold text-gray-800">Acesso não autorizado</h2>
        <p className="text-gray-500 max-w-sm">
          Seu perfil <strong>{permissao?.perfil ?? 'desconhecido'}</strong> não tem permissão
          para acessar este módulo. Contate o administrador do sistema.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
