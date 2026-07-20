import { redirect } from 'next/navigation';

export default function RootDashboardPage() {
  // A raiz do dashboard (/) deve redirecionar para a página inicial do dashboard (/dashboard)
  // Mas isso não deve afetar sub-rotas como /importar/processamentos
  redirect('/dashboard');
}
