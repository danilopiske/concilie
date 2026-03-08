/**
 * Table Component - Design System
 * Tabela reutilizável com formatação automática
 */
'use client';
import { useState, useEffect } from 'react';
import { ReactNode } from 'react';
import { Badge } from '@/components/ui/Badge';

export type TableColumn<T = any> = {
  key: string;
  label: string | ReactNode;
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
  pagination?: boolean;
  pageSize?: number;
  rowKey?: string | ((row: T) => string);
  loading?: boolean;
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
  pagination = false,
  pageSize = 10,
  rowKey,
  loading = false,
}: TableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);

  // Reset/Adjust page when data changes
  useEffect(() => {
    if (pagination) {
       const totalPages = Math.ceil(data.length / pageSize);
       if (currentPage > totalPages && totalPages > 0) {
           setCurrentPage(totalPages);
       } else if (totalPages === 0) {
           setCurrentPage(1);
       }
    }
  }, [data.length, pagination, pageSize]);

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
          {loading ? (
             <tr>
               <td
                 colSpan={columns.length}
                 className="px-6 py-8 text-center text-gray-500"
               >
                 <div className="flex justify-center items-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Carregando dados...
                 </div>
               </td>
             </tr>
          ) : (pagination 
              ? data.slice((currentPage - 1) * pageSize, currentPage * pageSize) 
              : data
           ).length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-6 py-8 text-center text-gray-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            (pagination 
                ? data.slice((currentPage - 1) * pageSize, currentPage * pageSize) 
                : data
             ).map((row, rowIndex) => {
              const key = rowKey 
                ? (typeof rowKey === 'function' ? rowKey(row) : row[rowKey as string]) 
                : rowIndex;
              
              return (
              <tr
                key={key}
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
              );
             })
          )}
        </tbody>
      </table>
      
      {pagination && data.length > pageSize && (
        <div className="px-6 py-3 flex items-center justify-between border-t border-gray-200">
           <div className="text-sm text-gray-500">
              Mostrando <span className="font-medium">{((currentPage - 1) * pageSize) + 1}</span> a <span className="font-medium">{Math.min(currentPage * pageSize, data.length)}</span> de <span className="font-medium">{data.length}</span> resultados
           </div>
           <div className="flex gap-2">
              <button 
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 hover:bg-gray-50 disabled:hover:bg-white"
              >
                  Anterior
              </button>
              <button 
                  onClick={() => setCurrentPage(p => Math.min(Math.ceil(data.length / pageSize), p + 1))}
                  disabled={currentPage >= Math.ceil(data.length / pageSize)}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 hover:bg-gray-50 disabled:hover:bg-white"
              >
                  Próxima
              </button>
           </div>
        </div>
      )}
    </div>
  );
}
