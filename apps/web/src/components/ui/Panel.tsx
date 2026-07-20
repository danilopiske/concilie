import React from 'react';
import { cn } from '@/lib/utils'; // Assuming you have a utils file for class merging, or use standard className logic

interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function Panel({ children, className, ...props }: PanelProps) {
  return (
    <div className={cn("border border-gray-300 rounded-sm bg-white shadow-sm mb-4", className)} {...props}>
      {children}
    </div>
  );
}

interface PanelHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
}

export function PanelHeader({ children, className, icon: Icon, ...props }: PanelHeaderProps) {
  return (
    <div className={cn("bg-gray-100 px-4 py-2 border-b border-gray-300 flex items-center gap-2", className)} {...props}>
      {Icon && <Icon className="w-4 h-4 text-gray-600" />}
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide">
        {children}
      </h3>
    </div>
  );
}

interface PanelBodyProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function PanelBody({ children, className, ...props }: PanelBodyProps) {
  return (
    <div className={cn("p-4", className)} {...props}>
      {children}
    </div>
  );
}
