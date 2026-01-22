/**
 * Componente Stepper (Design System)
 * Estados: pending, active, completed, error
 *
 * Props:
 * - steps: string[] (nomes das etapas)
 * - currentStep: number (índice da etapa atual)
 * - stepStatus?: Array<'pending' | 'active' | 'completed' | 'error'> (opcional, default: automático)
 */
'use client';

import React from 'react';

interface StepperProps {
  steps: string[];
  currentStep: number;
  stepStatus?: Array<'pending' | 'active' | 'completed' | 'error'>;
}

export const Stepper: React.FC<StepperProps> = ({ steps, currentStep, stepStatus }) => {
  // Gera status automático se não fornecido
  const getStatus = (idx: number): 'pending' | 'active' | 'completed' | 'error' => {
    if (stepStatus && stepStatus[idx]) return stepStatus[idx];
    if (idx < currentStep) return 'completed';
    if (idx === currentStep) return 'active';
    return 'pending';
  };

  return (
    <ol className="flex items-center w-full mb-4">
      {steps.map((label, idx) => {
        const status = getStatus(idx);
        return (
          <li key={label} className="flex-1 flex items-center">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full border-2
                ${status === 'completed' ? 'bg-success border-success text-white' : ''}
                ${status === 'active' ? 'bg-primary border-primary text-white' : ''}
                ${status === 'pending' ? 'bg-white border-info text-info' : ''}
                ${status === 'error' ? 'bg-error border-error text-white' : ''}
              `}
              aria-current={status === 'active' ? 'step' : undefined}
            >
              {status === 'completed' ? (
                <span aria-label="Concluído">✓</span>
              ) : status === 'error' ? (
                <span aria-label="Erro">!</span>
              ) : (
                idx + 1
              )}
            </div>
            <span className="ml-2 font-label text-sm">{label}</span>
            {idx < steps.length - 1 && (
              <div className="flex-1 h-0.5 mx-2 bg-info" />
            )}
          </li>
        );
      })}
    </ol>
  );
};
