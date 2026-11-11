import React from 'react';
import type { BrewLog } from '../types';

interface RecipeComparisonProps {
  brewA: BrewLog;
  brewB: BrewLog;
  onClose: () => void;
}

export const RecipeComparison: React.FC<RecipeComparisonProps> = ({ brewA, brewB, onClose }) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getDeltaBadge = (valA: number, valB: number, unit = '') => {
    const diff = valB - valA;
    if (diff === 0) return <span style={{ color: '#78716c', fontSize: '0.8rem' }}>No change</span>;
    const sign = diff > 0 ? '+' : '';
    const color = diff > 0 ? '#34d399' : '#f87171';
    return (
      <span style={{ color, fontSize: '0.8rem', fontWeight: 600 }}>
        {sign}{diff}{unit}
      </span>
    );
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        background: '#1c1917',
        border: '1px solid rgba(217, 119, 6, 0.3)',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '840px',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '24px',
        color: '#f5f5f4',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.4rem', color: '#f59e0b' }}>
              ⚖️ Side-by-Side Brew Comparison
            </h2>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#a8a29e' }}>
              Compare how parameter tweaks shifted cup quality and sensory extraction.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#a8a29e',
              fontSize: '1.4rem',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        </div>

        {/* Table of parameters */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#a8a29e' }}>
                <th style={{ padding: '10px 12px' }}>Parameter</th>
                <th style={{ padding: '10px 12px', color: '#f59e0b' }}>
                  Attempt A ({new Date(brewA.brewed_at).toLocaleDateString()})
                </th>
                <th style={{ padding: '10px 12px', color: '#38bdf8' }}>
                  Attempt B ({new Date(brewB.brewed_at).toLocaleDateString()})
                </th>
                <th style={{ padding: '10px 12px' }}>Shift (B vs A)</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>Equipment</td>
                <td style={{ padding: '10px 12px' }}>{brewA.dripper} ({brewA.grinder || 'Standard'})</td>
                <td style={{ padding: '10px 12px' }}>{brewB.dripper} ({brewB.grinder || 'Standard'})</td>
                <td style={{ padding: '10px 12px', color: '#78716c' }}>-</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>Dose & Water</td>
                <td style={{ padding: '10px 12px' }}>{brewA.actual_dose_g}g / {brewA.actual_water_g}g</td>
                <td style={{ padding: '10px 12px' }}>{brewB.actual_dose_g}g / {brewB.actual_water_g}g</td>
                <td style={{ padding: '10px 12px' }}>{getDeltaBadge(brewA.actual_water_g, brewB.actual_water_g, 'g water')}</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>Grind Setting</td>
                <td style={{ padding: '10px 12px' }}>{brewA.actual_grind_setting || 'Medium-fine'}</td>
                <td style={{ padding: '10px 12px' }}>{brewB.actual_grind_setting || 'Medium-fine'}</td>
                <td style={{ padding: '10px 12px', color: '#e7e5e4' }}>
                  {brewA.actual_grind_setting !== brewB.actual_grind_setting ? 'Adjusted' : 'Same'}
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>Water Temp</td>
                <td style={{ padding: '10px 12px' }}>{brewA.actual_temp_c}°C</td>
                <td style={{ padding: '10px 12px' }}>{brewB.actual_temp_c}°C</td>
                <td style={{ padding: '10px 12px' }}>{getDeltaBadge(brewA.actual_temp_c, brewB.actual_temp_c, '°C')}</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>Total Brew Time</td>
                <td style={{ padding: '10px 12px' }}>{formatTime(brewA.actual_brew_time_seconds)}</td>
                <td style={{ padding: '10px 12px' }}>{formatTime(brewB.actual_brew_time_seconds)}</td>
                <td style={{ padding: '10px 12px' }}>{getDeltaBadge(brewA.actual_brew_time_seconds, brewB.actual_brew_time_seconds, 's')}</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>Drawdown Speed</td>
                <td style={{ padding: '10px 12px', textTransform: 'capitalize' }}>{brewA.drawdown_speed}</td>
                <td style={{ padding: '10px 12px', textTransform: 'capitalize' }}>{brewB.drawdown_speed}</td>
                <td style={{ padding: '10px 12px', color: '#78716c' }}>-</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', background: 'rgba(255, 255, 255, 0.02)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 600 }}>Sweetness (1-5)</td>
                <td style={{ padding: '10px 12px' }}>{brewA.sweetness}/5</td>
                <td style={{ padding: '10px 12px' }}>{brewB.sweetness}/5</td>
                <td style={{ padding: '10px 12px' }}>{getDeltaBadge(brewA.sweetness, brewB.sweetness)}</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', background: 'rgba(255, 255, 255, 0.02)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 600 }}>Sourness (1-5)</td>
                <td style={{ padding: '10px 12px' }}>{brewA.sourness}/5</td>
                <td style={{ padding: '10px 12px' }}>{brewB.sourness}/5</td>
                <td style={{ padding: '10px 12px' }}>{getDeltaBadge(brewA.sourness, brewB.sourness)}</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', background: 'rgba(255, 255, 255, 0.02)' }}>
                <td style={{ padding: '10px 12px', fontWeight: 600 }}>Bitterness (1-5)</td>
                <td style={{ padding: '10px 12px' }}>{brewA.bitterness}/5</td>
                <td style={{ padding: '10px 12px' }}>{brewB.bitterness}/5</td>
                <td style={{ padding: '10px 12px' }}>{getDeltaBadge(brewA.bitterness, brewB.bitterness)}</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', background: 'rgba(217, 119, 6, 0.08)' }}>
                <td style={{ padding: '12px', fontWeight: 700, color: '#f59e0b' }}>Overall Satisfaction</td>
                <td style={{ padding: '12px', fontWeight: 700 }}>{brewA.overall_satisfaction}/5 ★</td>
                <td style={{ padding: '12px', fontWeight: 700 }}>{brewB.overall_satisfaction}/5 ★</td>
                <td style={{ padding: '12px' }}>{getDeltaBadge(brewA.overall_satisfaction, brewB.overall_satisfaction, '★')}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Sensory notes */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '20px' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px 16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 600, marginBottom: '4px' }}>Attempt A Notes</div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#d6d3d1', fontStyle: brewA.flavour_notes ? 'normal' : 'italic' }}>
              {brewA.flavour_notes || 'No sensory notes recorded.'}
            </p>
          </div>
          <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px 16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600, marginBottom: '4px' }}>Attempt B Notes</div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#d6d3d1', fontStyle: brewB.flavour_notes ? 'normal' : 'italic' }}>
              {brewB.flavour_notes || 'No sensory notes recorded.'}
            </p>
          </div>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              background: 'linear-gradient(135deg, #d97706, #b45309)',
              color: '#ffffff',
              border: 'none',
              padding: '10px 24px',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};
