'use client';

import { useState } from 'react';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { History, RefreshCw, FileText } from 'lucide-react';
import { RelatorioHistory } from '../RelatorioHistory';

export default function GestaoRelatoriosPage() {
  const [refreshHistory, setRefreshHistory] = useState(0);

  return (
    <div className="max-w-7xl mx-auto pb-10 space-y-6">
      <div className="border-b pb-4">
        <div className="flex items-center gap-2 text-gray-700 mb-1">
            <History className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Gestão de Relatórios</h1>
        </div>
        <p className="text-sm text-gray-500">
            Visualize e faça download de todos os relatórios gerados anteriormente.
        </p>
      </div>

      <Panel>
        <PanelHeader icon={FileText}>
           <div className="flex justify-between items-center w-full pr-4">
              <span>Histórico de Relatórios</span>
              <Button variant="secondary" size="sm" onClick={() => setRefreshHistory(prev => prev + 1)}>
                  <RefreshCw className="w-4 h-4" />
              </Button>
          </div>
        </PanelHeader>
        <PanelBody>
          <RelatorioHistory refreshTrigger={refreshHistory} />
        </PanelBody>
      </Panel>
    </div>
  );
}
