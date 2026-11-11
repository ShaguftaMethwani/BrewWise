import React, { useEffect, useState } from 'react';
import type { BrewLog } from '../types';
import { getBrews } from '../api';
import { RecipeComparison } from '../components/RecipeComparison';

export const BrewHistory: React.FC = () => {
  const [brews, setBrews] = useState<BrewLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Compare mode
  const [selectedBrews, setSelectedBrews] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState<boolean>(false);

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

  const toggleSelectBrew = (id: string) => {
    if (selectedBrews.includes(id)) {
      setSelectedBrews(selectedBrews.filter((bId) => bId !== id));
    } else {
      if (selectedBrews.length >= 2) {
        // Keep the latest and add new
        setSelectedBrews([selectedBrews[1], id]);
      } else {
        setSelectedBrews([...selectedBrews, id]);
      }
    }
  };

  const getBrewById = (id: string) => brews.find((b) => b.id === id);

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 16px', color: '#f5f5f4' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>📜</span> Brew History & Iterative Dialing
          </h1>
          <p style={{ margin: '6px 0 0 0', color: '#a8a29e', fontSize: '0.95rem' }}>
            Review past extractions, sensory evaluations, and barista adjustments.
          </p>
        </div>

        {selectedBrews.length === 2 && (
          <button
            onClick={() => setShowComparison(true)}
            style={{
              background: 'linear-gradient(135deg, #38bdf8, #0284c7)',
              color: '#ffffff',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '10px',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(56, 189, 248, 0.4)',
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
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#a8a29e' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>⏳ Loading your brews...</div>
        </div>
      )}

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          padding: '16px',
          borderRadius: '12px',
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {!loading && !error && brews.length === 0 && (
        <div style={{
          background: 'rgba(28, 25, 23, 0.6)',
          border: '1px dashed rgba(255, 255, 255, 0.15)',
          borderRadius: '16px',
          padding: '48px 24px',
          textAlign: 'center',
          color: '#a8a29e'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '12px' }}>☕</div>
          <h3 style={{ margin: 0, color: '#fafaf9', fontSize: '1.25rem' }}>No Brews Logged Yet</h3>
          <p style={{ margin: '8px 0 20px 0', fontSize: '0.9rem', maxWidth: '440px', marginLeft: 'auto', marginRight: 'auto' }}>
            Brew a cup using our interactive pour timer, then submit your sensory feedback to dial in your recipe.
          </p>
          <a
            href="/"
            style={{
              display: 'inline-block',
              background: 'linear-gradient(135deg, #d97706, #b45309)',
              color: '#ffffff',
              textDecoration: 'none',
              padding: '10px 24px',
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
          const diagnosis = brew.adjustments?.diagnosis || 'Standard Extractions';
          const isDialedIn = diagnosis.includes('Dialed-In');

          return (
            <div
              key={brew.id}
              style={{
                background: isSelected ? 'rgba(217, 119, 6, 0.08)' : 'rgba(28, 25, 23, 0.75)',
                border: isSelected ? '1px solid #f59e0b' : '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '14px',
                padding: '20px',
                transition: 'all 0.2s ease',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.25)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fafaf9' }}>
                      {brew.dripper}
                    </span>
                    {brew.grinder && (
                      <span style={{ fontSize: '0.85rem', color: '#a8a29e' }}>
                        with {brew.grinder}
                      </span>
                    )}
                    <span style={{
                      background: isDialedIn ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                      color: isDialedIn ? '#34d399' : '#fbbf24',
                      padding: '2px 8px',
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      border: '1px solid currentColor'
                    }}>
                      {diagnosis}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#78716c', marginTop: '4px' }}>
                    {dateStr}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ fontSize: '1rem', color: '#fbbf24', fontWeight: 700 }}>
                    {'★'.repeat(brew.overall_satisfaction)}{'☆'.repeat(5 - brew.overall_satisfaction)}
                  </div>
                  <button
                    onClick={() => toggleSelectBrew(brew.id)}
                    style={{
                      background: isSelected ? '#f59e0b' : 'rgba(255, 255, 255, 0.08)',
                      color: isSelected ? '#1c1917' : '#d6d3d1',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
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
                background: 'rgba(0, 0, 0, 0.3)',
                padding: '12px',
                borderRadius: '8px',
                marginBottom: '14px',
                fontSize: '0.85rem'
              }}>
                <div>
                  <span style={{ color: '#78716c', display: 'block', fontSize: '0.7rem' }}>DOSE</span>
                  <strong>{brew.actual_dose_g}g</strong>
                </div>
                <div>
                  <span style={{ color: '#78716c', display: 'block', fontSize: '0.7rem' }}>WATER</span>
                  <strong>{brew.actual_water_g}g</strong>
                </div>
                <div>
                  <span style={{ color: '#78716c', display: 'block', fontSize: '0.7rem' }}>TEMP</span>
                  <strong>{brew.actual_temp_c}°C</strong>
                </div>
                <div>
                  <span style={{ color: '#78716c', display: 'block', fontSize: '0.7rem' }}>GRIND</span>
                  <strong>{brew.actual_grind_setting || 'Medium'}</strong>
                </div>
                <div>
                  <span style={{ color: '#78716c', display: 'block', fontSize: '0.7rem' }}>TIME</span>
                  <strong>{Math.floor(brew.actual_brew_time_seconds / 60)}m {brew.actual_brew_time_seconds % 60}s</strong>
                </div>
                <div>
                  <span style={{ color: '#78716c', display: 'block', fontSize: '0.7rem' }}>FLOW</span>
                  <strong style={{ textTransform: 'capitalize' }}>{brew.drawdown_speed}</strong>
                </div>
              </div>

              {/* Barista Adjustments */}
              {brew.adjustments && (
                <div style={{
                  background: 'rgba(217, 119, 6, 0.05)',
                  borderLeft: '3px solid #f59e0b',
                  padding: '8px 12px',
                  borderRadius: '0 6px 6px 0',
                  fontSize: '0.85rem'
                }}>
                  <span style={{ color: '#f59e0b', fontWeight: 600 }}>Next Iteration: </span>
                  <span style={{ color: '#e7e5e4' }}>{brew.adjustments.primary_adjustment}</span>
                </div>
              )}

              {brew.flavour_notes && (
                <div style={{ fontSize: '0.8rem', color: '#a8a29e', marginTop: '10px', fontStyle: 'italic' }}>
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
