/**
 * Componente Card - Executive Style
 * Design sofisticado com sombras e bordas refinadas
 */
import React from 'react';

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
  variant?: 'default' | 'highlighted';
}

export function Card({ title, children, className = '', actions, variant = 'default' }: CardProps) {
  return (
    <div className={`bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200 border border-gray-100 ${className}`}>
      {(title || actions) && (
        <div className={`
          px-6 py-4 border-b border-gray-100 flex justify-between items-center
          ${variant === 'highlighted' 
            ? 'bg-gradient-to-r from-[#1e3a8a]/5 to-transparent' 
            : 'bg-white'
          }
        `}>
          {title && (
            <h3 className="text-lg font-semibold text-[#1e3a8a]" style={{ fontFamily: '"Poppins", sans-serif' }}>
              {title}
            </h3>
          )}
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
