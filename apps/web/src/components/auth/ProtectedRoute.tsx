'use client';

import { usePermissoes } from '@/hooks/usePermissoes';
import type { Perfil } from '@/lib/api/permissoes';

interface ProtectedRouteProps {
  modulo: string;
  children: React.ReactNode;
  /** Perfis permitidos (override da tabela padrão) */
  roles?: Perfil[];
}

export function ProtectedRoute({ modulo, children, roles }: ProtectedRouteProps) {
  const { permissao, loading, podeAcessar } = usePermissoes();

  if (loading) return null;

  const permitido = roles
    ? permissao && roles.includes(permissao.perfil)
    : podeAcessar(modulo);

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
