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
  onFileSelect: (files: File[] | null) => void;
  loading?: boolean;
  error?: string | null;
  selectedFile?: File | File[] | null;
  disabled?: boolean;
  multiple?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  accept,
  onFileSelect,
  loading = false,
  error = null,
  selectedFile = null,
  disabled = false,
  multiple = false,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(Array.from(e.target.files));
    } else {
      onFileSelect(null);
    }
  };

  const getFileName = () => {
    if (!selectedFile) return 'Nenhum arquivo selecionado';
    if (Array.isArray(selectedFile)) {
      if (selectedFile.length === 1) return selectedFile[0].name;
      return `${selectedFile.length} arquivos selecionados`;
    }
    return (selectedFile as File).name;
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="font-label" htmlFor="file-upload">
        {multiple ? 'Selecione um ou mais arquivos' : 'Selecione um arquivo'}
      </label>
      <input
        id="file-upload"
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        disabled={loading || disabled}
        multiple={multiple}
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
        <div className="flex flex-col">
          <span className="text-sm text-info">
            {getFileName()}
          </span>
          <span className="text-xs text-info">({accept})</span>
        </div>
      </div>
      {error && (
        <div className="Alert variant-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};
