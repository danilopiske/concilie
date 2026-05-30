/**
 * Checkbox Component - Design System
 * Checkbox com label associado e acessibilidade
 */
'use client';

import { useId } from 'react';

export interface CheckboxProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  error?: string;
}

export function Checkbox({
  label,
  checked,
  onChange,
  disabled = false,
  className = '',
  error,
}: CheckboxProps) {
  const id = useId();

  return (
    <div className={className}>
      <label
        htmlFor={id}
        className={`
          flex items-center text-sm font-medium
          ${disabled ? 'text-gray-400 cursor-not-allowed' : 'text-gray-700 cursor-pointer'}
        `}
      >
        <input
          id={id}
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className={`
            mr-2 h-4 w-4 rounded
            ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
            text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            ${error ? 'border-red-500' : 'border-gray-300'}
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${id}-error` : undefined}
        />
        {label}
      </label>
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-600 font-medium">
          {error}
        </p>
      )}
    </div>
  );
}
