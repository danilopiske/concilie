/**
 * Select Component
 * Campo de seleção padronizado
 */
'use client';

import { SelectHTMLAttributes } from 'react';

export interface SelectOption {
  value: string | number;
  label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options?: SelectOption[];
  placeholder?: string;
}

export function Select({ 
  label, 
  error, 
  options, 
  placeholder, 
  children, 
  className = '', 
  ...props 
}: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}
      <select
        className={`
          w-full px-3 py-2 
          border rounded-md
          ${error 
            ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
            : 'border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-blue-500'
          }
          bg-white dark:bg-gray-700
          text-gray-900 dark:text-white
          focus:outline-none focus:ring-2
          disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed
          ${className}
        `}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options ? (
          options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))
        ) : (
          children
        )}
      </select>
      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}
