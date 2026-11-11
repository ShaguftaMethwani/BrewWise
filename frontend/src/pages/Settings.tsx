import React, { useEffect, useState } from 'react';
import type { User, UserEquipmentProfile, UserEquipmentProfileCreate } from '../types';
import {
  getMe,
  login,
  register,
  clearToken,
  getEquipmentProfiles,
  createEquipmentProfile,
  deleteEquipmentProfile,
  setDefaultProfile,
  getBrews
} from '../api';

const DRIPPER_OPTIONS = [
  'Hario V60',
  'Kalita Wave',
  'Origami Dripper',
  'Chemex',
  'Fellow Stagg [X]',
  'April Dripper',
  'Clever Dripper',
  'AeroPress',
  'Kono Meimon',
  'Orea V3'
];

const GRINDER_OPTIONS = [
  'Comandante C40',
  '1Zpresso JX-Pro',
  '1Zpresso K-Ultra',
  '1Zpresso Q2',
  'Timemore C2',
  'Kingrinder K6',
  'Fellow Ode Gen 2',
  'Baratza Encore',
  'Baratza Encore ESP',
  'Baratza Sette 270',
  'Baratza Vario+',
  'Eureka Mignon Filtro',
  'Wilfa Svart Aroma',
  'Wilfa Uniform',
  'Mahlkönig EK43',
  'Mahlkönig X54',
  'Niche Zero',
  'Niche Duo',
  'DF64 Gen 2',
  'Option-O Lagom Mini'
];

export const Settings: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  // Equipment profiles
  const [profiles, setProfiles] = useState<UserEquipmentProfile[]>([]);
  const [profileLoading, setProfileLoading] = useState(false);
  const [showAddProfile, setShowAddProfile] = useState(false);

  // New profile form
  const [profileName, setProfileName] = useState('');
  const [selectedDripper, setSelectedDripper] = useState(DRIPPER_OPTIONS[0]);
  const [selectedGrinder, setSelectedGrinder] = useState(GRINDER_OPTIONS[0]);
  const [isCustomGrinder, setIsCustomGrinder] = useState(false);
  const [customGrinder, setCustomGrinder] = useState('');
  const [filterType, setFilterType] = useState('Tabbed Paper');
  const [defaultDose, setDefaultDose] = useState(15.0);
  const [defaultRatio, setDefaultRatio] = useState('1:16.67');

  useEffect(() => {
    init();
  }, []);

  const init = async () => {
    try {
      const u = await getMe();
      setUser(u);
      if (u) {
        loadProfiles();
      }
    } catch {
      // not logged in
    }
  };

  const loadProfiles = async () => {
    setProfileLoading(true);
    try {
      const data = await getEquipmentProfiles();
      setProfiles(data);
    } catch (err) {
      console.error(err);
    } finally {
      setProfileLoading(false);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);

    try {
      if (authMode === 'login') {
        const res = await login(email, password);
        setUser(res.user);
      } else {
        const res = await register(email, password, displayName);
        setUser(res.user);
      }
      setEmail('');
      setPassword('');
      setDisplayName('');
      loadProfiles();
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSignOut = () => {
    clearToken();
    setUser(null);
    setProfiles([]);
  };

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profileName.trim()) return;

    try {
      const finalGrinder = (isCustomGrinder ? customGrinder.trim() : selectedGrinder) || 'Standard Grinder';
      const payload: UserEquipmentProfileCreate = {
        name: profileName.trim(),
        dripper: selectedDripper,
        grinder: finalGrinder,
        filter_type: filterType,
        default_dose_g: defaultDose,
        default_ratio: defaultRatio,
        is_default: profiles.length === 0
      };
      await createEquipmentProfile(payload);
      setProfileName('');
      setShowAddProfile(false);
      loadProfiles();
    } catch (err: any) {
      alert(err.message || 'Failed to create profile');
    }
  };

  const handleDeleteProfile = async (id: string) => {
    if (!confirm('Are you sure you want to delete this equipment profile?')) return;
    try {
      await deleteEquipmentProfile(id);
      loadProfiles();
    } catch (err: any) {
      alert(err.message || 'Failed to delete profile');
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await setDefaultProfile(id);
      loadProfiles();
    } catch (err: any) {
      alert(err.message || 'Failed to set default profile');
    }
  };

  const handleExportData = async () => {
    try {
      const brews = await getBrews();
      const exportObject = {
        exported_at: new Date().toISOString(),
        user: user ? { id: user.id, email: user.email, display_name: user.display_name } : null,
        equipment_profiles: profiles,
        brews: brews
      };
      const blob = new Blob([JSON.stringify(exportObject, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `brewwise-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert('Failed to export data: ' + err.message);
    }
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', padding: '32px 16px', color: '#f5f5f4' }}>
      <h1 style={{ margin: '0 0 8px 0', fontSize: '2rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span>⚙️</span> Equipment Profiles & Settings
      </h1>
      <p style={{ margin: '0 0 28px 0', color: '#a8a29e', fontSize: '0.95rem' }}>
        Manage your pour-over equipment setups, accounts, and brewing preferences.
      </p>

      {/* Account Section */}
      <div style={{
        background: 'rgba(28, 25, 23, 0.75)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '28px'
      }}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: '1.25rem', color: '#fafaf9', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>👤</span> User Account
        </h2>

        {user ? (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fafaf9' }}>
                {user.display_name}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#a8a29e' }}>
                {user.email}
              </div>
            </div>
            <button
              onClick={handleSignOut}
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#fca5a5',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                padding: '8px 18px',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              Sign Out
            </button>
          </div>
        ) : (
          <div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <button
                type="button"
                onClick={() => setAuthMode('login')}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: authMode === 'login' ? '#f59e0b' : 'rgba(255, 255, 255, 0.08)',
                  color: authMode === 'login' ? '#1c1917' : '#d6d3d1',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer'
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setAuthMode('register')}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: authMode === 'register' ? '#f59e0b' : 'rgba(255, 255, 255, 0.08)',
                  color: authMode === 'register' ? '#1c1917' : '#d6d3d1',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer'
                }}
              >
                Create Account
              </button>
            </div>

            {authError && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#fca5a5',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                marginBottom: '16px'
              }}>
                {authError}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} style={{ display: 'grid', gap: '14px', maxWidth: '420px' }}>
              {authMode === 'register' && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#e7e5e4', marginBottom: '4px' }}>
                    Display Name
                  </label>
                  <input
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="e.g. Elena Barista"
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      background: 'rgba(0, 0, 0, 0.4)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: '#fafaf9',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#e7e5e4', marginBottom: '4px' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@example.com"
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    background: 'rgba(0, 0, 0, 0.4)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    color: '#fafaf9',
                    fontSize: '0.9rem'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#e7e5e4', marginBottom: '4px' }}>
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    background: 'rgba(0, 0, 0, 0.4)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    color: '#fafaf9',
                    fontSize: '0.9rem'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="btn-pastel-sage"
                style={{
                  padding: '10px 22px',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  cursor: authLoading ? 'not-allowed' : 'pointer',
                  marginTop: '4px'
                }}
              >
                {authLoading ? 'Authenticating...' : authMode === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            </form>
          </div>
        )}
      </div>

      {/* Equipment Profiles Section */}
      <div style={{
        background: 'rgba(28, 25, 23, 0.75)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '28px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#fafaf9', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>☕</span> Equipment Presets
            </h2>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#a8a29e' }}>
              Set your default dripper and grinder for 1-click recipe generation.
            </p>
          </div>
          {user && (
            <button
              onClick={() => setShowAddProfile(!showAddProfile)}
              style={{
                background: showAddProfile ? 'rgba(255, 255, 255, 0.1)' : '#f59e0b',
                color: showAddProfile ? '#fafaf9' : '#1c1917',
                border: 'none',
                padding: '8px 14px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              {showAddProfile ? 'Cancel' : '+ Add Setup'}
            </button>
          )}
        </div>

        {!user ? (
          <div style={{ fontSize: '0.9rem', color: '#a8a29e' }}>
            Please sign in or create an account above to save and sync custom equipment profiles.
          </div>
        ) : (
          <div>
            {showAddProfile && (
              <form onSubmit={handleCreateProfile} style={{
                background: 'rgba(0, 0, 0, 0.3)',
                padding: '16px',
                borderRadius: '12px',
                marginBottom: '20px',
                display: 'grid',
                gap: '14px'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: '#a8a29e', marginBottom: '4px' }}>
                      Profile Name
                    </label>
                    <input
                      type="text"
                      required
                      value={profileName}
                      onChange={(e) => setProfileName(e.target.value)}
                      placeholder="e.g. Morning V60"
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '6px',
                        padding: '8px 10px',
                        color: '#fafaf9'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: '#a8a29e', marginBottom: '4px' }}>
                      Dripper Model
                    </label>
                    <select
                      value={selectedDripper}
                      onChange={(e) => setSelectedDripper(e.target.value)}
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        background: 'rgba(0, 0, 0, 0.5)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '6px',
                        padding: '8px 10px',
                        color: '#fafaf9'
                      }}
                    >
                      {DRIPPER_OPTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <label style={{ fontSize: '0.8rem', color: '#a8a29e' }}>
                        Grinder Model
                      </label>
                      <button
                        type="button"
                        onClick={() => {
                          setIsCustomGrinder(!isCustomGrinder);
                          if (!isCustomGrinder && !customGrinder) {
                            setCustomGrinder(selectedGrinder);
                          }
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#38bdf8',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          padding: 0,
                          textDecoration: 'underline'
                        }}
                      >
                        {isCustomGrinder ? '← Pick from list' : '+ Type other grinder'}
                      </button>
                    </div>

                    {isCustomGrinder ? (
                      <input
                        type="text"
                        placeholder="e.g. Kingrinder K6, 1Zpresso K-Ultra, Ode Gen 2"
                        value={customGrinder}
                        onChange={(e) => setCustomGrinder(e.target.value)}
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          background: 'rgba(0, 0, 0, 0.5)',
                          border: '1px solid rgba(255, 255, 255, 0.15)',
                          borderRadius: '6px',
                          padding: '8px 10px',
                          color: '#fafaf9'
                        }}
                        autoFocus
                      />
                    ) : (
                      <select
                        value={selectedGrinder}
                        onChange={(e) => {
                          if (e.target.value === '__custom__') {
                            setIsCustomGrinder(true);
                          } else {
                            setSelectedGrinder(e.target.value);
                          }
                        }}
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          background: 'rgba(0, 0, 0, 0.5)',
                          border: '1px solid rgba(255, 255, 255, 0.15)',
                          borderRadius: '6px',
                          padding: '8px 10px',
                          color: '#fafaf9'
                        }}
                      >
                        {GRINDER_OPTIONS.map((g) => <option key={g} value={g}>{g}</option>)}
                        <option value="__custom__">✏️ Other / Custom Grinder (Type name)...</option>
                      </select>
                    )}
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: '#a8a29e', marginBottom: '4px' }}>
                      Filter Paper Type
                    </label>
                    <input
                      type="text"
                      value={filterType}
                      onChange={(e) => setFilterType(e.target.value)}
                      placeholder="e.g. Tabbed Paper, Kalita Wave 185"
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '6px',
                        padding: '8px 10px',
                        color: '#fafaf9'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: '#a8a29e', marginBottom: '4px' }}>
                      Default Dose (g)
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="8"
                      max="40"
                      value={defaultDose}
                      onChange={(e) => setDefaultDose(parseFloat(e.target.value) || 15.0)}
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '6px',
                        padding: '8px 10px',
                        color: '#fafaf9'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: '#a8a29e', marginBottom: '4px' }}>
                      Default Ratio
                    </label>
                    <input
                      type="text"
                      value={defaultRatio}
                      onChange={(e) => setDefaultRatio(e.target.value)}
                      placeholder="e.g. 1:16.67"
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '6px',
                        padding: '8px 10px',
                        color: '#fafaf9'
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  <button
                    type="submit"
                    style={{
                      background: '#f59e0b',
                      color: '#1c1917',
                      border: 'none',
                      padding: '8px 18px',
                      borderRadius: '6px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Save Profile
                  </button>
                </div>
              </form>
            )}

            {profileLoading ? (
              <div style={{ fontSize: '0.85rem', color: '#a8a29e', padding: '12px 0' }}>
                Loading saved equipment presets...
              </div>
            ) : profiles.length === 0 ? (
              <div style={{ fontSize: '0.85rem', color: '#78716c' }}>
                No equipment profiles created yet. Add one above!
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '10px' }}>
                {profiles.map((p) => (
                  <div
                    key={p.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: 'rgba(0, 0, 0, 0.3)',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      border: p.is_default ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid rgba(255, 255, 255, 0.05)'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 600, color: '#fafaf9' }}>{p.name}</span>
                        {p.is_default && (
                          <span style={{
                            background: 'rgba(245, 158, 11, 0.2)',
                            color: '#fbbf24',
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            padding: '2px 6px',
                            borderRadius: '4px'
                          }}>
                            DEFAULT
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#a8a29e', marginTop: '2px' }}>
                        {p.dripper} • {p.grinder || 'No grinder specified'} • {p.default_dose_g}g
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      {!p.is_default && (
                        <button
                          onClick={() => handleSetDefault(p.id)}
                          style={{
                            background: 'transparent',
                            color: '#fbbf24',
                            border: '1px solid rgba(251, 191, 36, 0.3)',
                            padding: '4px 10px',
                            borderRadius: '6px',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          Set Default
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteProfile(p.id)}
                        style={{
                          background: 'transparent',
                          color: '#f87171',
                          border: 'none',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          fontSize: '0.9rem'
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Data Export & Privacy */}
      <div style={{
        background: 'rgba(28, 25, 23, 0.75)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '24px'
      }}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: '1.25rem', color: '#fafaf9', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>📦</span> Data & Offline Storage
        </h2>
        <p style={{ margin: '0 0 16px 0', fontSize: '0.85rem', color: '#a8a29e' }}>
          Export your complete brewing logs and configurations into an offline portable JSON file.
        </p>

        <button
          onClick={handleExportData}
          style={{
            background: 'rgba(255, 255, 255, 0.08)',
            color: '#fafaf9',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            padding: '10px 18px',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '0.85rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <span>📥</span> Export Brew Logs & Profiles (JSON)
        </button>
      </div>
    </div>
  );
};
