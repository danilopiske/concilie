'use client';

import React from 'react';

interface KpiCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'green' | 'yellow' | 'red' | 'blue';
  sublabel?: string;
}

const COLOR_MAP = {
  green: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: 'text-green-600 bg-green-100',
    value: 'text-green-700',
    label: 'text-green-600',
  },
  yellow: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    icon: 'text-yellow-600 bg-yellow-100',
    value: 'text-yellow-700',
    label: 'text-yellow-600',
  },
  red: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: 'text-red-600 bg-red-100',
    value: 'text-red-700',
    label: 'text-red-600',
  },
  blue: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: 'text-blue-600 bg-blue-100',
    value: 'text-blue-700',
    label: 'text-blue-600',
  },
};

export function KpiCard({ title, value, icon: Icon, color, sublabel }: KpiCardProps) {
  const c = COLOR_MAP[color];
  return (
    <div className={`rounded-xl border ${c.border} ${c.bg} p-5 flex items-start gap-4 shadow-sm`}>
      <div className={`p-3 rounded-lg ${c.icon} flex-shrink-0`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-600 truncate">{title}</p>
        <p className={`text-3xl font-bold mt-1 ${c.value}`}>{value}</p>
        {sublabel && <p className={`text-xs mt-1 ${c.label}`}>{sublabel}</p>}
      </div>
    </div>
  );
}
