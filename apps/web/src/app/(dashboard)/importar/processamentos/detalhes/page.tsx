'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ProcessamentoDetalhesClient } from './_client';

function DetalhesInner() {
  const params = useSearchParams();
  const id = params.get('id') ?? '';
  return <ProcessamentoDetalhesClient processamentoId={id} />;
}

export default function DetalhesPage() {
  return (
    <Suspense fallback={<div className="p-6 text-gray-400 text-sm">Carregando...</div>}>
      <DetalhesInner />
    </Suspense>
  );
}
