import React, { useState } from 'react';
import type { EvidencePackage } from '../types';
import { MatchTypeBadge } from './MatchTypeBadge';

interface EvidencePanelProps {
  evidence: EvidencePackage | null;
  loading?: boolean;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence, loading }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  if (loading) {
    return (
      <div
        className="glass-panel"
        style={{
          background: '#ffffff',
          padding: '1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          color: 'var(--text-secondary)',
          fontSize: '0.9rem',
        }}
      >
        <span
          style={{
            width: '16px',
            height: '16px',
            border: '2px solid var(--border-subtle)',
            borderTopColor: 'var(--pastel-sage-text)',
            borderRadius: '50%',
            display: 'inline-block',
            animation: 'spin 1s linear infinite',
          }}
        ></span>
        Searching knowledge base & running live inline web discovery...
      </div>
    );
  }

  if (!evidence) {
    return null;
  }

  const outcomeColors = {
    A: {
      border: 'var(--pastel-sage-border)',
      badgeBg: 'var(--pastel-sage)',
      badgeText: 'var(--pastel-sage-text)',
      title: 'Direct Evidence Grounding (Outcome A)',
    },
    B: {
      border: 'var(--pastel-lavender-border)',
      badgeBg: 'var(--pastel-lavender)',
      badgeText: 'var(--pastel-lavender-text)',
      title: 'Analogous Reference Adaptation (Outcome B)',
    },
    C: {
      border: 'var(--pastel-butter-border)',
      badgeBg: 'var(--pastel-butter)',
      badgeText: 'var(--pastel-butter-text)',
      title: 'Principles-Based Synthesis (Outcome C)',
    },
  };

  const outcomeConfig = outcomeColors[evidence.match_outcome] || outcomeColors.B;

  return (
    <div
      className="glass-panel"
      style={{
        background: '#ffffff',
        border: `1px solid ${outcomeConfig.border}`,
        borderRadius: '12px',
        padding: '1.25rem',
        marginBottom: '1.75rem',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
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
          <h4 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Retrieved Evidence ({evidence.matched_recipes.length} sources)
          </h4>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {isExpanded ? 'Hide Details' : 'Expand Evidence'}
          </span>
          <span style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s', color: 'var(--text-muted)' }}>
            ▼
          </span>
        </div>
      </div>

      {isExpanded && (
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Live Web Discovery Status Notification */}
          {evidence.discovery_status && evidence.discovery_status !== 'disabled' && (
            <div
              style={{
                padding: '0.55rem 0.85rem',
                borderRadius: '6px',
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background:
                  evidence.discovery_status === 'skipped_sufficient_kb'
                    ? 'var(--pastel-sky)'
                    : evidence.discovery_status === 'success' && (evidence.recipes_discovered || 0) > 0
                    ? 'var(--pastel-sage)'
                    : 'var(--pastel-sand)',
                border:
                  evidence.discovery_status === 'skipped_sufficient_kb'
                    ? '1px solid var(--pastel-sky-border)'
                    : evidence.discovery_status === 'success' && (evidence.recipes_discovered || 0) > 0
                    ? '1px solid var(--pastel-sage-border)'
                    : '1px solid var(--border-subtle)',
                color:
                  evidence.discovery_status === 'skipped_sufficient_kb'
                    ? 'var(--pastel-sky-text)'
                    : evidence.discovery_status === 'success' && (evidence.recipes_discovered || 0) > 0
                    ? 'var(--pastel-sage-text)'
                    : 'var(--text-secondary)',
              }}
            >
              <span>
                {evidence.discovery_status === 'skipped_sufficient_kb'
                  ? '⚡'
                  : evidence.discovery_status === 'success'
                  ? '🌐'
                  : 'ℹ️'}
              </span>
              <span>
                {evidence.discovery_message ||
                  (evidence.discovery_status === 'skipped_sufficient_kb'
                    ? 'Skipped web crawler: High confidence recipes verified in knowledge base.'
                    : 'Inline web discovery completed.')}
              </span>
            </div>
          )}

          <p style={{ margin: '0', fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            {evidence.coverage_summary}
          </p>

          {/* Parameter Conflicts Alert */}
          {evidence.conflicts && evidence.conflicts.length > 0 && (
            <div
              style={{
                background: 'var(--badge-low-bg)',
                border: '1px solid var(--badge-low)',
                borderRadius: '8px',
                padding: '0.85rem',
              }}
            >
              <h5 style={{ margin: '0 0 0.5rem', fontSize: '0.88rem', color: 'var(--badge-low)', fontWeight: 600 }}>
                ⚠️ Noted Recipe Divergences Resolved
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.82rem' }}>
                {evidence.conflicts.map((conflict, idx) => (
                  <div key={idx} style={{ color: 'var(--text-secondary)' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>{conflict.parameter}:</strong> {conflict.difference}.{' '}
                    <span style={{ color: 'var(--pastel-sage-text)' }}>→ {conflict.resolution_guidance}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Source List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {evidence.matched_recipes.map((match) => {
              const r = match.extracted_recipe;
              return (
                <div
                  key={match.source_id}
                  style={{
                    background: '#fafafa',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '0.9rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            padding: '0.15rem 0.45rem',
                            borderRadius: '4px',
                            background: match.is_live_discovered ? 'var(--pastel-sky)' : 'var(--pastel-sand)',
                            color: match.is_live_discovered ? 'var(--pastel-sky-text)' : 'var(--text-secondary)',
                            border: match.is_live_discovered ? '1px solid var(--pastel-sky-border)' : '1px solid var(--border-subtle)',
                          }}
                        >
                          {match.is_live_discovered ? '🌐 DISCOVERED ONLINE' : '📚 KNOWLEDGE BASE'}
                        </span>
                      </div>
                      <a
                        href={match.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          fontSize: '0.92rem',
                          fontWeight: 600,
                          color: '#0369a1',
                          textDecoration: 'none',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                        }}
                      >
                        {match.title}
                        <span style={{ fontSize: '0.75rem' }}>↗</span>
                      </a>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
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
                      background: '#ffffff',
                      border: '1px solid var(--border-subtle)',
                      padding: '0.6rem 0.75rem',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                    }}
                  >
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Dripper</span>
                      <strong style={{ color: 'var(--text-primary)' }}>{r.dripper || 'V60'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Dose / Water</span>
                      <strong style={{ color: 'var(--text-primary)' }}>{r.dose_g}g / {r.water_g}g</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Ratio</span>
                      <strong style={{ color: 'var(--text-primary)' }}>{r.ratio || '1:16'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Temperature</span>
                      <strong style={{ color: 'var(--text-primary)' }}>{r.water_temperature_c}°C</strong>
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
                            background: 'var(--pastel-sand)',
                            color: 'var(--text-secondary)',
                            border: '1px solid var(--border-subtle)',
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
