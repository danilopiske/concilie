/**
 * ConfirmDialog Component - Design System
 * Modal de confirmação reutilizável
 */
import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

const variantStyles = {
  danger: {
    icon: '⚠️',
    confirmVariant: 'danger' as const,
  },
  warning: {
    icon: '⚡',
    confirmVariant: 'primary' as const,
  },
  info: {
    icon: 'ℹ️',
    confirmVariant: 'primary' as const,
  },
};

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  variant = 'danger',
  loading = false,
}: ConfirmDialogProps) {
  const [internalLoading, setInternalLoading] = React.useState(false);

  const handleConfirm = async () => {
    try {
      setInternalLoading(true);
      await onConfirm();
      if (!loading) {
        onClose();
      }
    } finally {
      if(mounted) setInternalLoading(false);
    }
  };

  const [mounted, setMounted] = React.useState(true);
  React.useEffect(() => {
    return () => setMounted(false);
  }, []);

  const isLoading = loading || internalLoading;

  const config = variantStyles[variant];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="text-3xl">{config.icon}</div>
          <p className="text-gray-700 flex-1">{message}</p>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 border-gray-700">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            {cancelText}
          </Button>
          <Button variant={config.confirmVariant} onClick={handleConfirm} loading={isLoading}>
            {confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
