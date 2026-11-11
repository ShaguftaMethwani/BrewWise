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
      padding: '16px 28px',
      borderBottom: '1px solid var(--border-subtle)',
      background: '#ffffff',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'var(--pastel-sage)',
          border: '1px solid var(--pastel-sage-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Coffee size={18} color="var(--pastel-sage-text)" />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontSize: '1.2rem',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            color: 'var(--text-primary)',
          }}>
            BrewWise
          </span>
          <span style={{
            fontSize: '0.7rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--pastel-sage-text)',
            padding: '2px 8px',
            background: 'var(--pastel-sage)',
            borderRadius: '999px',
            border: '1px solid var(--pastel-sage-border)',
          }}>
            Dial-In
          </span>
        </div>
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Link
          to="/"
          style={{
            fontSize: '0.88rem',
            color: isActive('/') ? 'var(--text-primary)' : 'var(--text-secondary)',
            background: isActive('/') ? 'var(--pastel-sand)' : 'transparent',
            borderRadius: '8px',
            padding: '8px 14px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            textDecoration: 'none',
          }}
        >
          <Sparkles size={15} color={isActive('/') ? 'var(--text-primary)' : 'currentColor'} />
          Scan Bag
        </Link>

        <Link
          to="/history"
          style={{
            fontSize: '0.88rem',
            color: isActive('/history') ? 'var(--text-primary)' : 'var(--text-secondary)',
            background: isActive('/history') ? 'var(--pastel-sand)' : 'transparent',
            borderRadius: '8px',
            padding: '8px 14px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            textDecoration: 'none',
          }}
        >
          <BookOpen size={15} color={isActive('/history') ? 'var(--text-primary)' : 'currentColor'} />
          History
        </Link>

        <Link
          to="/settings"
          style={{
            fontSize: '0.88rem',
            color: isActive('/settings') ? 'var(--text-primary)' : 'var(--text-secondary)',
            background: isActive('/settings') ? 'var(--pastel-sand)' : 'transparent',
            borderRadius: '8px',
            padding: '8px 14px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            textDecoration: 'none',
          }}
        >
          <SettingsIcon size={15} color={isActive('/settings') ? 'var(--text-primary)' : 'currentColor'} />
          {user ? user.display_name.split(' ')[0] : 'Settings'}
        </Link>
      </div>
    </nav>
  );
};
