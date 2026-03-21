import { apiClient } from './client';

export interface MeuPerfil {
  id: number | null;
  usuario: string;
  nome?: string;
  empresa?: string;
}

export const perfilApi = {
  getMeuPerfil: async (): Promise<MeuPerfil> => {
    const response = await apiClient.get<MeuPerfil>('/perfil/me');
    return response.data;
  },

  alterarSenha: async (senhaAtual: string, novaSenha: string): Promise<void> => {
    await apiClient.post('/perfil/me/alterar-senha', {
      senha_atual: senhaAtual,
      nova_senha: novaSenha,
    });
  },
};
