import React, { useEffect, useState } from 'react';
import { getBrews } from '../api';
import type { BrewLog } from '../types';
import { RecipeComparison } from '../components/RecipeComparison';

export const BrewHistory: React.FC = () => {
  const [brews, setBrews] = useState<BrewLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBrews, setSelectedBrews] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState(false);

  useEffect(() => {
    loadBrews();
  }, []);

  const loadBrews = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getBrews();
      setBrews(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load brew history');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectBrew = (brewId: string) => {
    if (selectedBrews.includes(brewId)) {
      setSelectedBrews(selectedBrews.filter(id => id !== brewId));
    } else {
      if (selectedBrews.length < 2) {
        setSelectedBrews([...selectedBrews, brewId]);
      } else {
        setSelectedBrews([selectedBrews[1], brewId]);
      }
    }
  };

  const getBrewById = (id: string) => brews.find(b => b.id === id);

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', padding: '36px 20px 80px' }} className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '28px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.8rem', color: 'var(--text-primary)', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Brew History & Dialing Journal
          </h1>
          <p style={{ margin: '4px 0 0 0', color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Review past extractions, sensory evaluations, and barista adjustments.
          </p>
        </div>

        {selectedBrews.length === 2 && (
          <button
            onClick={() => setShowComparison(true)}
            className="btn-pastel-sky"
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.88rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <span>⚖️</span> Compare 2 Selected Brews
          </button>
        )}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Loading your brews...</div>
        </div>
      )}

      {error && (
        <div style={{
          background: 'var(--badge-low-bg)',
          border: '1px solid var(--badge-low)',
          color: 'var(--badge-low)',
          padding: '14px',
          borderRadius: '8px',
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {!loading && !error && brews.length === 0 && (
        <div style={{
          background: '#ffffff',
          border: '1px dashed var(--border-subtle)',
          borderRadius: '12px',
          padding: '48px 24px',
          textAlign: 'center',
          color: 'var(--text-secondary)'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>☕</div>
          <h3 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1.2rem', fontWeight: 600 }}>No Brews Logged Yet</h3>
          <p style={{ margin: '8px 0 20px 0', fontSize: '0.9rem', maxWidth: '440px', marginLeft: 'auto', marginRight: 'auto' }}>
            Brew a cup using our interactive pour timer, then submit your sensory feedback to dial in your recipe.
          </p>
          <a
            href="/"
            className="btn-pastel-sage"
            style={{
              display: 'inline-block',
              padding: '10px 22px',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.9rem'
            }}
          >
            Scan a Coffee Bag to Start
          </a>
        </div>
      )}

      {/* Brews List */}
      <div style={{ display: 'grid', gap: '16px' }}>
        {brews.map((brew) => {
          const isSelected = selectedBrews.includes(brew.id);
          const dateStr = new Date(brew.brewed_at).toLocaleString();
          const diagnosis = brew.adjustments?.diagnosis || 'Standard Extraction';
          const isDialedIn = diagnosis.includes('Dialed-In');

          return (
            <div
              key={brew.id}
              className="glass-panel"
              style={{
                background: isSelected ? 'var(--pastel-sand)' : '#ffffff',
                border: isSelected ? '1px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                borderRadius: '12px',
                padding: '20px',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {brew.dripper}
                    </span>
                    {brew.grinder && (
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        with {brew.grinder}
                      </span>
                    )}
                    <span style={{
                      background: isDialedIn ? 'var(--badge-high-bg)' : 'var(--badge-med-bg)',
                      color: isDialedIn ? 'var(--badge-high)' : 'var(--badge-med)',
                      padding: '2px 8px',
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      border: '1px solid currentColor'
                    }}>
                      {diagnosis}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {dateStr}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ fontSize: '1rem', color: '#f59e0b', fontWeight: 700 }}>
                    {'★'.repeat(brew.overall_satisfaction)}{'☆'.repeat(5 - brew.overall_satisfaction)}
                  </div>
                  <button
                    onClick={() => toggleSelectBrew(brew.id)}
                    className={isSelected ? 'btn-pastel-sage' : 'btn-pastel-sand'}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {isSelected ? '✓ Selected' : '+ Compare'}
                  </button>
                </div>
              </div>

              {/* Brew Metrics Pill Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                gap: '8px',
                background: '#fafafa',
                border: '1px solid var(--border-subtle)',
                padding: '12px',
                borderRadius: '8px',
                marginBottom: '14px',
                fontSize: '0.85rem'
              }}>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>DOSE</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{brew.actual_dose_g}g</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>WATER</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{brew.actual_water_g}g</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>TEMP</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{brew.actual_temp_c}°C</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>GRIND</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{brew.actual_grind_setting || 'Medium'}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>TIME</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{Math.floor(brew.actual_brew_time_seconds / 60)}m {brew.actual_brew_time_seconds % 60}s</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>FLOW</span>
                  <strong style={{ color: 'var(--text-primary)', textTransform: 'capitalize' }}>{brew.drawdown_speed}</strong>
                </div>
              </div>

              {/* Barista Adjustments */}
              {brew.adjustments && (
                <div style={{
                  background: 'var(--pastel-sand)',
                  borderLeft: '3px solid var(--pastel-sage-text)',
                  padding: '8px 12px',
                  borderRadius: '0 6px 6px 0',
                  fontSize: '0.85rem'
                }}>
                  <span style={{ color: 'var(--pastel-sage-text)', fontWeight: 600 }}>Next Iteration: </span>
                  <span style={{ color: 'var(--text-primary)' }}>{brew.adjustments.primary_adjustment}</span>
                </div>
              )}

              {brew.flavour_notes && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '10px', fontStyle: 'italic' }}>
                  "{brew.flavour_notes}"
                </div>
              )}
            </div>
          );
        })}
      </div>

      {showComparison && selectedBrews.length === 2 && (
        <RecipeComparison
          brewA={getBrewById(selectedBrews[0])!}
          brewB={getBrewById(selectedBrews[1])!}
          onClose={() => setShowComparison(false)}
        />
      )}
    </div>
  );
};
