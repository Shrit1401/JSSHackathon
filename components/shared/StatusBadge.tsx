'use client';

import { RiskLevel } from '@/lib/types';

interface Props {
  level: RiskLevel;
  size?: 'sm' | 'md';
}

const config = {
  'safe': {
    label: 'SAFE',
    className: 'bg-cyber-safe-dim text-cyber-safe border border-cyber-safe/30',
  },
  'suspicious': {
    label: 'SUSPICIOUS',
    className: 'bg-cyber-suspicious-dim text-cyber-suspicious border border-cyber-suspicious/30',
  },
  'high-risk': {
    label: 'HIGH RISK',
    className: 'bg-cyber-danger-dim text-cyber-danger border border-cyber-danger/30 animate-pulse',
  },
};

export default function StatusBadge({ level, size = 'md' }: Props) {
  const { label, className } = config[level];
  const sizeClass = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';
  return (
    <span className={`inline-block rounded font-bold tracking-wider ${sizeClass} ${className}`}>
      {label}
    </span>
  );
}
