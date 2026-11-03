import React from 'react';
import { Link } from 'react-router-dom';
import { Coffee, Sparkles } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 24px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(15, 13, 12, 0.8)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, var(--accent-gold), var(--accent-copper))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: 'var(--shadow-glow)',
        }}>
          <Coffee size={20} color="#0f0d0c" />
        </div>
        <div>
          <span style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            background: 'linear-gradient(to right, #fff, var(--accent-crema))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            BrewWise
          </span>
          <span style={{
            fontSize: '0.65rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: 'var(--accent-gold)',
            marginLeft: '6px',
            padding: '2px 6px',
            background: 'rgba(229, 168, 82, 0.1)',
            borderRadius: '4px',
            border: '1px solid rgba(229, 168, 82, 0.25)',
          }}>
            Phase 1 MVP
          </span>
        </div>
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <Link
          to="/"
          style={{
            fontSize: '0.9rem',
            color: 'var(--text-secondary)',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Sparkles size={16} color="var(--accent-gold)" />
          New Scan
        </Link>
      </div>
    </nav>
  );
};
