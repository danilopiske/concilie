/**
 * Alert Component - Design System
 * Mensagens de feedback para o usuário
 */
'use client';

import { ReactNode } from 'react';

export type AlertVariant = 'info' | 'success' | 'error' | 'warning';

export interface AlertProps {
  variant?: AlertVariant;
  children: ReactNode;
  onClose?: () => void;
  className?: string;
}

const variantStyles: Record<AlertVariant, { bg: string; border: string; text: string; icon: string }> = {
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-300',
    text: 'text-blue-900',
    icon: 'ℹ️',
  },
  success: {
    bg: 'bg-green-50',
    border: 'border-green-300',
    text: 'text-green-900',
    icon: '✓',
  },
  error: {
    bg: 'bg-red-50',
    border: 'border-red-300',
    text: 'text-red-900',
    icon: '⚠️',
  },
  warning: {
    bg: 'bg-yellow-50',
    border: 'border-amber-400',
    text: 'text-amber-900',
    icon: '⚡',
  },
};

export function Alert({ variant = 'info', children, onClose, className = '' }: AlertProps) {
  const styles = variantStyles[variant];

  return (
    <div
      className={`
        p-4 rounded-lg border-l-4
        ${styles.bg} ${styles.border} ${styles.text}
        ${className}
      `}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <div className="text-xl flex-shrink-0">{styles.icon}</div>
        <div className="flex-1">{children}</div>
        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 text-current opacity-50 hover:opacity-100 transition-opacity"
            aria-label="Fechar alerta"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
