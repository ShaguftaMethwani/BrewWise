import React from 'react';
import type { MatchType } from '../types';

interface MatchTypeBadgeProps {
  type: MatchType;
  score?: number;
}

export const MatchTypeBadge: React.FC<MatchTypeBadgeProps> = ({ type, score }) => {
  const configs: Record<MatchType, { bg: string; text: string; label: string; border: string }> = {
    exact: {
      bg: 'rgba(16, 185, 129, 0.15)',
      text: '#10b981',
      border: 'rgba(16, 185, 129, 0.3)',
      label: 'Exact Match',
    },
    strong: {
      bg: 'rgba(59, 130, 246, 0.15)',
      text: '#3b82f6',
      border: 'rgba(59, 130, 246, 0.3)',
      label: 'Strong Match',
    },
    related: {
      bg: 'rgba(139, 92, 246, 0.15)',
      text: '#a78bfa',
      border: 'rgba(139, 92, 246, 0.3)',
      label: 'Related Coffee',
    },
    analogous: {
      bg: 'rgba(245, 158, 11, 0.15)',
      text: '#f59e0b',
      border: 'rgba(245, 158, 11, 0.3)',
      label: 'Analogous Profile',
    },
    general: {
      bg: 'rgba(156, 163, 175, 0.15)',
      text: '#9ca3af',
      border: 'rgba(156, 163, 175, 0.3)',
      label: 'General Reference',
    },
  };

  const cfg = configs[type] || configs.general;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: '0.2rem 0.55rem',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        backgroundColor: cfg.bg,
        color: cfg.text,
        border: `1px solid ${cfg.border}`,
        letterSpacing: '0.02em',
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: cfg.text,
        }}
      />
      {cfg.label}
      {score !== undefined && (
        <span style={{ opacity: 0.8, fontSize: '0.7rem' }}>
          ({Math.round(score * 100)}%)
        </span>
      )}
    </span>
  );
};
