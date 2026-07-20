'use client';

import { useCallback, useState } from 'react';
import { Upload, X, FileText } from 'lucide-react';

interface Props {
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
}

export function RedeUploader({ onFilesChange, disabled }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);

  const addFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return;
    const novos = Array.from(incoming).filter(f => f.name.toLowerCase().endsWith('.txt'));
    setFiles(prev => {
      const merged = [...prev];
      novos.forEach(n => {
        if (!merged.find(e => e.name === n.name)) merged.push(n);
      });
      onFilesChange(merged);
      return merged;
    });
  }, [onFilesChange]);

  const remover = (nome: string) => {
    setFiles(prev => {
      const next = prev.filter(f => f.name !== nome);
      onFilesChange(next);
      return next;
    });
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const formatBytes = (b: number) =>
    b < 1024 ? `${b} B` : b < 1048576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1048576).toFixed(1)} MB`;

  return (
    <div className="space-y-4">
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-lg p-10 text-center transition-colors cursor-pointer
          ${dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}
          ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
        onClick={() => document.getElementById('rede-file-input')?.click()}
      >
        <Upload className="mx-auto mb-3 h-10 w-10 text-gray-400" />
        <p className="text-sm text-gray-600 font-medium">
          Arraste arquivos TXT aqui ou <span className="text-blue-600 underline">clique para selecionar</span>
        </p>
        <p className="text-xs text-gray-400 mt-1">Apenas extratos Rede (.txt) — múltiplos arquivos permitidos</p>
        <input
          id="rede-file-input"
          type="file"
          accept=".txt"
          multiple
          className="hidden"
          onChange={e => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map(f => (
            <li key={f.name} className="flex items-center justify-between bg-gray-50 border rounded px-3 py-2">
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="h-4 w-4 text-gray-400 shrink-0" />
                <span className="text-sm truncate text-gray-700">{f.name}</span>
                <span className="text-xs text-gray-400 shrink-0">{formatBytes(f.size)}</span>
              </div>
              <button
                onClick={() => remover(f.name)}
                disabled={disabled}
                className="ml-2 text-gray-400 hover:text-red-500 shrink-0"
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
