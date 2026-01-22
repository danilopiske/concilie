/**
 * Badge Component - Design System
 * Paleta: Verde (success), Vermelho (error), Dourado (warning), Azul (info)
 */
'use client';

import { ReactNode } from 'react';

export type BadgeVariant = 'success' | 'error' | 'warning' | 'info' | 'default' | 'gold';

export interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-green-100 text-green-800 border border-green-200',
  error: 'bg-red-100 text-red-800 border border-red-200',
  warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
  info: 'bg-blue-100 text-blue-800 border border-blue-200',
  default: 'bg-gray-100 text-gray-700 border border-gray-200',
  gold: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-amber-800 border border-amber-300',
};

export function Badge({ variant = 'default', children, className = '' }: BadgeProps) {
  return (
    <span
      className={`
        px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
}
