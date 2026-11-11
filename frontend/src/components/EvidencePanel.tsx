import React, { useState } from 'react';
import type { EvidencePackage } from '../types';
import { MatchTypeBadge } from './MatchTypeBadge';

interface EvidencePanelProps {
  evidence: EvidencePackage | null;
  loading?: boolean;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence, loading }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (loading) {
    return (
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '12px',
          padding: '1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          color: '#a3a3a3',
          fontSize: '0.9rem',
        }}
      >
        <span className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#f59e0b', borderRadius: '50%', display: 'inline-block', animation: 'spin 1s linear infinite' }}></span>
        Searching curated knowledge base & evaluating recipe evidence...
      </div>
    );
  }

  if (!evidence) {
    return null;
  }

  const outcomeColors = {
    A: {
      border: 'rgba(16, 185, 129, 0.35)',
      badgeBg: 'rgba(16, 185, 129, 0.15)',
      badgeText: '#10b981',
      title: 'Direct Evidence Grounding (Outcome A)',
    },
    B: {
      border: 'rgba(139, 92, 246, 0.35)',
      badgeBg: 'rgba(139, 92, 246, 0.15)',
      badgeText: '#a78bfa',
      title: 'Analogous Reference Adaptation (Outcome B)',
    },
    C: {
      border: 'rgba(245, 158, 11, 0.35)',
      badgeBg: 'rgba(245, 158, 11, 0.15)',
      badgeText: '#f59e0b',
      title: 'Principles-Based Synthesis (Outcome C)',
    },
  };

  const outcomeConfig = outcomeColors[evidence.match_outcome] || outcomeColors.B;

  return (
    <div
      style={{
        background: 'rgba(20, 20, 24, 0.75)',
        backdropFilter: 'blur(12px)',
        border: `1px solid ${outcomeConfig.border}`,
        borderRadius: '14px',
        padding: '1.25rem',
        marginBottom: '1.75rem',
        transition: 'all 0.2s ease',
      }}
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span
            style={{
              padding: '0.25rem 0.65rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              backgroundColor: outcomeConfig.badgeBg,
              color: outcomeConfig.badgeText,
            }}
          >
            {evidence.match_outcome === 'A'
              ? '🎯 EXACT EVIDENCE'
              : evidence.match_outcome === 'B'
              ? '🌿 RELATED SOURCES'
              : '🔬 PHYSICS ENGINE'}
          </span>
          <h4 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 600, color: '#f3f4f6' }}>
            Knowledge Base Evidence ({evidence.matched_recipes.length} matches)
          </h4>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>
            {isExpanded ? 'Hide' : 'Show Details'}
          </span>
          <span style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
            ▼
          </span>
        </div>
      </div>

      <p style={{ margin: '0.6rem 0 0', fontSize: '0.86rem', color: '#9ca3af', lineHeight: 1.45 }}>
        {evidence.coverage_summary}
      </p>

      {isExpanded && (
        <div style={{ marginTop: '1.2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Parameter Conflicts Alert */}
          {evidence.conflicts && evidence.conflicts.length > 0 && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '8px',
                padding: '0.85rem 1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#f87171', fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                <span>⚠️ Detected Parameter Conflicts Between Sources</span>
              </div>
              {evidence.conflicts.map((c, i) => (
                <div key={i} style={{ fontSize: '0.8rem', color: '#d1d5db', marginTop: '0.35rem' }}>
                  <span style={{ fontWeight: 600, color: '#fca5a5' }}>{c.parameter}: </span>
                  {c.difference} — <em style={{ color: '#93c5fd' }}>Resolution: {c.resolution_guidance}</em>
                </div>
              ))}
            </div>
          )}

          {/* Matched Sources Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {evidence.matched_recipes.map((match) => {
              const r = match.extracted_recipe;
              return (
                <div
                  key={match.source_id}
                  style={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    borderRadius: '10px',
                    padding: '0.9rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div>
                      <a
                        href={match.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          fontSize: '0.92rem',
                          fontWeight: 600,
                          color: '#60a5fa',
                          textDecoration: 'none',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                        }}
                      >
                        {match.title}
                        <span style={{ fontSize: '0.75rem' }}>↗</span>
                      </a>
                      <div style={{ fontSize: '0.78rem', color: '#9ca3af', marginTop: '0.15rem' }}>
                        By {match.author || match.site_name || 'Specialty Roaster'}
                      </div>
                    </div>
                    <MatchTypeBadge type={match.match_type} score={match.relevance_score} />
                  </div>

                  {/* Recipe Parameters */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                      gap: '0.5rem',
                      background: 'rgba(0, 0, 0, 0.25)',
                      padding: '0.6rem 0.75rem',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                    }}
                  >
                    <div>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Dripper</span>
                      <strong style={{ color: '#f3f4f6' }}>{r.dripper || 'V60'}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Dose / Water</span>
                      <strong style={{ color: '#f3f4f6' }}>{r.dose_g}g / {r.water_g}g</strong>
                    </div>
                    <div>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Ratio</span>
                      <strong style={{ color: '#f3f4f6' }}>{r.ratio || '1:16'}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Temperature</span>
                      <strong style={{ color: '#f3f4f6' }}>{r.water_temperature_c}°C</strong>
                    </div>
                  </div>

                  {/* Match Reasons */}
                  {match.match_reasons && match.match_reasons.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.2rem' }}>
                      {match.match_reasons.map((reason, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: '0.72rem',
                            padding: '0.15rem 0.45rem',
                            borderRadius: '4px',
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: '#d1d5db',
                          }}
                        >
                          ✓ {reason}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
