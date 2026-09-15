import React from 'react';
import { RiskPriority } from '../../types';

interface RiskBadgeProps {
  priority: RiskPriority;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ priority, score, size = 'md' }) => {
  const getColors = () => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-[#991B1B] text-white border-[#7F1D1D]';
      case 'HIGH':
        return 'bg-[#C2410C] text-white border-[#9A3412]';
      case 'MEDIUM':
        return 'bg-[#B45309] text-white border-[#92400E]';
      case 'LOW':
      default:
        return 'bg-[#15803D] text-white border-[#166534]';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'text-[10px] px-2 py-0.5';
      case 'lg':
        return 'text-xs px-3 py-1 font-bold';
      case 'md':
      default:
        return 'text-[11px] px-2.5 py-1 font-bold';
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-xs border uppercase tracking-wider font-mono font-bold ${getColors()} ${getSizeClasses()}`}
    >
      <span>{priority} RISK</span>
      {score !== undefined && (
        <span className="opacity-90 font-mono text-[10px]">
          ({score.toFixed(1)}/100)
        </span>
      )}
    </span>
  );
};
