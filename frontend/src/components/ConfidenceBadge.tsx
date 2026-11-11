import React from 'react';
import { CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';

interface Props {
  confidence: number;
  source?: string;
}

export const ConfidenceBadge: React.FC<Props> = ({ confidence, source }) => {
  let color = 'var(--badge-low)';
  let bg = 'var(--badge-low-bg)';
  let icon = <HelpCircle size={13} color={color} />;
  let label = `${Math.round(confidence * 100)}%`;

  if (confidence >= 0.9) {
    color = 'var(--badge-high)';
    bg = 'var(--badge-high-bg)';
    icon = <CheckCircle2 size={13} color={color} />;
  } else if (confidence >= 0.6) {
    color = 'var(--badge-med)';
    bg = 'var(--badge-med-bg)';
    icon = <AlertTriangle size={13} color={color} />;
  }

  if (source === 'user_override') {
    label = 'Edited';
    color = 'var(--pastel-sky-text)';
    bg = 'var(--pastel-sky)';
  }

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      fontSize: '0.75rem',
      fontWeight: 600,
      color,
      background: bg,
      padding: '2px 8px',
      borderRadius: 'var(--radius-full)',
      border: `1px solid ${color}40`,
    }}>
      {icon}
      <span>{label}</span>
    </span>
  );
};
