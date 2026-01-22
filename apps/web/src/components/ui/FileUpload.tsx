/**
 * Componente FileUpload (Design System)
 * Estados: empty, selected, loading, error
 *
 * Props:
 * - accept: string (tipos aceitos, ex: '.csv,.xlsx')
 * - onFileSelect: (file: File | null) => void
 * - loading: boolean
 * - error: string | null
 * - selectedFile: File | null
 */
'use client';

import React, { useRef } from 'react';

interface FileUploadProps {
  accept: string;
  onFileSelect: (file: File | null) => void;
  loading?: boolean;
  error?: string | null;
  selectedFile?: File | null;
  disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  accept,
  onFileSelect,
  loading = false,
  error = null,
  selectedFile = null,
  disabled = false,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    } else {
      onFileSelect(null);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="font-label" htmlFor="file-upload">
        Selecione um arquivo
      </label>
      <input
        id="file-upload"
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        disabled={loading || disabled}
        className="hidden"
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="Button variant-secondary"
          onClick={() => inputRef.current?.click()}
          disabled={loading || disabled}
          aria-label="Selecionar arquivo"
        >
          {loading ? 'Carregando...' : 'Escolher arquivo'}
        </button>
        <span className="text-sm text-info">
          {selectedFile ? selectedFile.name : 'Nenhum arquivo selecionado'}
        </span>
        <span className="text-xs text-info">({accept})</span>
      </div>
      {error && (
        <div className="Alert variant-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};
