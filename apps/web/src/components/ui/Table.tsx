/**
 * Table Component - Design System
 * Tabela reutilizável com formatação automática
 */
'use client';

import { ReactNode } from 'react';
import { Badge } from '@/components/ui/Badge';

export type TableColumn<T = any> = {
  key: string;
  label: string;
  sortable?: boolean;
  format?: 'currency' | 'date' | 'boolean' | 'badge';
  render?: (value: any, row: T) => ReactNode;
  width?: string;
};

export type TableVariant = 'simple' | 'info';

export interface TableProps<T = any> {
  variant?: TableVariant;
  columns: TableColumn<T>[];
  data: T[];
  onSort?: (key: string) => void;
  emptyMessage?: string;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
}

const formatters = {
  currency: (value: any) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(Number(value) || 0);
  },
  date: (value: any) => {
    if (!value) return '-';
    const date = typeof value === 'string' ? new Date(value) : value;
    return new Intl.DateTimeFormat('pt-BR').format(date);
  },
  boolean: (value: any) => {
    return value ? 'Sim' : 'Não';
  },
  badge: (value: any) => {
    if (typeof value === 'boolean') {
      return value ? (
        <Badge variant="success">Sim</Badge>
      ) : (
        <Badge variant="error">Não</Badge>
      );
    }
    return <Badge>{String(value)}</Badge>;
  },
};

export function Table<T extends Record<string, any>>({
  variant = 'simple',
  columns,
  data,
  onSort,
  emptyMessage = 'Nenhum registro encontrado',
  sortKey,
  sortDirection,
}: TableProps<T>) {
  const handleSort = (columnKey: string, sortable?: boolean) => {
    if (sortable && onSort) {
      onSort(columnKey);
    }
  };

  const renderCell = (column: TableColumn<T>, row: T) => {
    const value = row[column.key];

    // Custom render
    if (column.render) {
      return column.render(value, row);
    }

    // Auto format
    if (column.format && formatters[column.format]) {
      return formatters[column.format](value);
    }

    // Default
    return value ?? '-';
  };

  const baseClasses = 'min-w-full divide-y divide-gray-200';
  const variantClasses = {
    simple: '',
    info: 'text-sm',
  };

  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow-sm border border-gray-200">
      <table className={`${baseClasses} ${variantClasses[variant]}`}>
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider ${
                  column.sortable ? 'cursor-pointer hover:bg-gray-100 transition-colors' : ''
                }`}
                onClick={() => handleSort(column.key, column.sortable)}
                style={column.width ? { width: column.width } : undefined}
              >
                <div className="flex items-center gap-2">
                  {column.label}
                  {column.sortable && sortKey === column.key && (
                    <span className="text-blue-600 font-bold">
                      {sortDirection === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-6 py-8 text-center text-gray-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="hover:bg-gray-50 transition-colors"
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                  >
                    {renderCell(column, row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
