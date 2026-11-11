import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Coffee, Sparkles, BookOpen, Settings as SettingsIcon } from 'lucide-react';
import { getMe } from '../api';
import type { User } from '../types';

export const Navbar: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const location = useLocation();

  useEffect(() => {
    getMe().then(setUser).catch(() => setUser(null));
  }, [location.pathname]);

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 24px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(15, 13, 12, 0.85)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
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
            Dial-In AI
          </span>
        </div>
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <Link
          to="/"
          style={{
            fontSize: '0.88rem',
            color: isActive('/') ? 'var(--accent-gold)' : 'var(--text-secondary)',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            textDecoration: 'none',
          }}
        >
          <Sparkles size={16} color={isActive('/') ? 'var(--accent-gold)' : 'currentColor'} />
          Scan Bag
        </Link>

        <Link
          to="/history"
          style={{
            fontSize: '0.88rem',
            color: isActive('/history') ? 'var(--accent-gold)' : 'var(--text-secondary)',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            textDecoration: 'none',
          }}
        >
          <BookOpen size={16} color={isActive('/history') ? 'var(--accent-gold)' : 'currentColor'} />
          History
        </Link>

        <Link
          to="/settings"
          style={{
            fontSize: '0.88rem',
            color: isActive('/settings') ? 'var(--accent-gold)' : 'var(--text-secondary)',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            textDecoration: 'none',
          }}
        >
          <SettingsIcon size={16} color={isActive('/settings') ? 'var(--accent-gold)' : 'currentColor'} />
          {user ? user.display_name.split(' ')[0] : 'Settings'}
        </Link>
      </div>
    </nav>
  );
};
