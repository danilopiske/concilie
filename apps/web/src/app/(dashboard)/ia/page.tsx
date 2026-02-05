import { AIChat } from '@/components/ai/ai-chat';

export default function AIAnalysisPage() {
  return (
    <div className="space-y-6 h-full">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Análise de Dados IA</h1>
        <p className="text-slate-500">
          Use a inteligência artificial para explorar seus dados financeiros e operacionais.
        </p>
      </div>

      <AIChat />
    </div>
  );
}
