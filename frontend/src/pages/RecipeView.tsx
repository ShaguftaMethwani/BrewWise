import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Thermometer,
  Scale,
  Clock,
  Compass,
  Sparkles,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  Coffee,
  RefreshCw,
  ExternalLink,
  BookOpen,
} from 'lucide-react';
import { getRecipe, searchRecipes } from '../api';
import type { PersonalisedRecipe, EvidencePackage } from '../types';
import { BrewTimer } from '../components/BrewTimer';
import { EvidencePanel } from '../components/EvidencePanel';
import { FeedbackForm } from '../components/FeedbackForm';

export const RecipeView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [recipe, setRecipe] = useState<PersonalisedRecipe | null>(location.state?.recipe || null);
  const [evidence, setEvidence] = useState<EvidencePackage | null>(null);
  const [loading, setLoading] = useState(!recipe);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showTroubleshooting, setShowTroubleshooting] = useState(true);
  const [showRationale, setShowRationale] = useState(true);

  useEffect(() => {
    async function fetchRecipe() {
      if (!recipe && id) {
        try {
          const data = await getRecipe(id);
          setRecipe(data);
        } catch (err: any) {
          setError(err.message || 'Failed to load recipe');
        } finally {
          setLoading(false);
        }
      }
    }
    fetchRecipe();
  }, [id, recipe]);

  // Fetch retrieval evidence for this coffee
  useEffect(() => {
    async function loadEvidence() {
      if (recipe && recipe.coffee_profile_id) {
        setEvidenceLoading(true);
        try {
          const ev = await searchRecipes({
            coffee_profile_id: recipe.coffee_profile_id,
            dripper: recipe.dripper,
          });
          setEvidence(ev);
        } catch (e) {
          console.warn('Could not load evidence package:', e);
        } finally {
          setEvidenceLoading(false);
        }
      }
    }
    loadEvidence();
  }, [recipe?.coffee_profile_id, recipe?.dripper]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px' }}>
        <RefreshCw size={32} color="var(--accent-gold)" style={{ animation: 'spin 1.5s linear infinite' }} />
        <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>Loading dialled-in recipe...</p>
      </div>
    );
  }

  if (!recipe || error) {
    return (
      <div style={{ maxWidth: '600px', margin: '60px auto', textAlign: 'center' }}>
        <p style={{ color: 'var(--badge-low)' }}>{error || 'Recipe not found'}</p>
        <Link to="/" style={{ color: 'var(--accent-gold)', marginTop: '12px', display: 'inline-block' }}>
          Back to Home
        </Link>
      </div>
    );
  }

  const formatSeconds = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSourceBadge = () => {
    switch (recipe.source_type) {
      case 'exact_match':
        return {
          label: 'Exact Source Match',
          bg: 'rgba(16, 185, 129, 0.15)',
          color: '#10b981',
          border: 'rgba(16, 185, 129, 0.3)',
        };
      case 'adapted_from_related':
        return {
          label: 'Adapted from Related Coffee',
          bg: 'rgba(139, 92, 246, 0.15)',
          color: '#a78bfa',
          border: 'rgba(139, 92, 246, 0.3)',
        };
      case 'curated_baseline':
        return {
          label: 'Curated Expert Baseline',
          bg: 'rgba(59, 130, 246, 0.15)',
          color: '#3b82f6',
          border: 'rgba(59, 130, 246, 0.3)',
        };
      case 'ai_generated':
      default:
        return {
          label: 'AI Synthesized (Brewing Physics)',
          bg: 'rgba(245, 158, 11, 0.15)',
          color: '#f59e0b',
          border: 'rgba(245, 158, 11, 0.3)',
        };
    }
  };

  const badge = getSourceBadge();

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', padding: '30px 20px 80px' }} className="animate-fade-in">
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            background: 'transparent',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.9rem',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          <ArrowLeft size={16} />
          Back to Profile
        </button>
      </div>

      {/* Main Recipe Header Card */}
      <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px', background: '#ffffff' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
              <span style={{
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--accent-gold)',
                fontWeight: 600,
                background: 'rgba(229, 168, 82, 0.1)',
                padding: '3px 8px',
                borderRadius: '4px',
              }}>
                {recipe.dripper}
              </span>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '3px 8px',
                borderRadius: '4px',
                backgroundColor: badge.bg,
                color: badge.color,
                border: `1px solid ${badge.border}`,
              }}>
                {badge.label}
              </span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {recipe.grinder || 'Universal Setting'}
              </span>
            </div>
            <h1 style={{ fontSize: '2.4rem', fontFamily: 'var(--font-serif)', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
              Precision Dialed-In Recipe
            </h1>
            <p style={{ color: 'var(--accent-crema)', fontSize: '1rem', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={16} color="var(--accent-gold)" />
              {recipe.expected_flavour}
            </p>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block' }}>Recipe Accuracy</span>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              color: 'var(--badge-high)',
              fontWeight: 700,
              fontSize: '1.25rem',
            }}>
              <CheckCircle2 size={18} />
              {Math.round(recipe.confidence * 100)}%
            </span>
          </div>
        </div>

        {/* Recipe Key Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '12px',
          marginTop: '28px',
        }}>
          <div style={{ background: 'var(--bg-elevated)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Scale size={13} color="var(--accent-gold)" /> Dose
            </span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, marginTop: '2px' }}>
              {recipe.dose_g}g
            </p>
          </div>

          <div style={{ background: 'var(--bg-elevated)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Coffee size={13} color="var(--accent-gold)" /> Water
            </span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, marginTop: '2px' }}>
              {recipe.water_g}g
            </p>
          </div>

          <div style={{ background: 'var(--bg-elevated)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Ratio</span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, marginTop: '2px' }}>
              {recipe.ratio}
            </p>
          </div>

          <div style={{ background: 'var(--bg-elevated)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Thermometer size={13} color="var(--accent-gold)" /> Temp
            </span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, marginTop: '2px' }}>
              {recipe.water_temperature_c}°C
            </p>
          </div>

          <div style={{ background: 'var(--bg-elevated)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={13} color="var(--accent-gold)" /> Total Time
            </span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, marginTop: '2px' }}>
              {formatSeconds(recipe.target_brew_time_seconds)}
            </p>
          </div>
        </div>

        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(229, 168, 82, 0.08)',
          border: '1px solid rgba(229, 168, 82, 0.2)',
          borderRadius: 'var(--radius-sm)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <Compass size={18} color="var(--accent-gold)" />
          <span style={{ fontSize: '0.9rem' }}>
            <strong>Grind Setting:</strong> {recipe.grind_description}
            {recipe.grind_setting ? ` (${recipe.grind_setting})` : ''}
          </span>
        </div>
      </div>

      {/* Interactive Brew Timer */}
      <div style={{ marginBottom: '28px' }}>
        <BrewTimer
          pourSchedule={recipe.pour_schedule}
          targetBrewTimeSeconds={recipe.target_brew_time_seconds}
        />
      </div>

      {/* Pour Schedule Table */}
      <div className="glass-panel" style={{ padding: '28px', marginBottom: '28px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '16px' }}>
          Pour Schedule Breakdown
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.92rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '10px 12px' }}>STEP</th>
                <th style={{ padding: '10px 12px' }}>START</th>
                <th style={{ padding: '10px 12px' }}>POUR</th>
                <th style={{ padding: '10px 12px' }}>SCALE TOTAL</th>
                <th style={{ padding: '10px 12px' }}>POUR TECHNIQUE</th>
              </tr>
            </thead>
            <tbody>
              {recipe.pour_schedule.map((step) => (
                <tr key={step.step_number} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px', fontWeight: 600 }}>{step.step_number}</td>
                  <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', color: 'var(--accent-gold)' }}>
                    {formatSeconds(step.start_time_seconds)}
                  </td>
                  <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>+{step.water_g}g</td>
                  <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                    {step.cumulative_water_g}g
                  </td>
                  <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>
                    {step.technique}
                    {step.notes && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{step.notes}</div>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Step by Step Instructions */}
      <div className="glass-panel" style={{ padding: '28px', marginBottom: '28px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '16px' }}>
          Step-by-Step Instructions
        </h3>
        <ol style={{ paddingLeft: '20px', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
          {recipe.step_by_step_instructions.map((inst, index) => (
            <li key={index} style={{ marginBottom: '8px' }}>
              <span style={{ color: 'var(--text-primary)' }}>{inst}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Reasoning and Rationale */}
      {recipe.explanation && (
        <div className="glass-panel" style={{ padding: '24px', marginBottom: '28px' }}>
          <div
            onClick={() => setShowRationale(!showRationale)}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={18} color="var(--accent-gold)" />
              Why This Recipe? (Bean & Parameter Rationale)
            </h3>
            {showRationale ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>

          {showRationale && (
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
              <p style={{ color: 'var(--text-primary)', marginBottom: '14px', lineHeight: 1.6 }}>
                {recipe.explanation.reasoning_summary}
              </p>
              {Object.entries(recipe.explanation.parameter_rationale || {}).map(([param, rat]) => (
                <div key={param} style={{ marginBottom: '8px', fontSize: '0.9rem' }}>
                  <span style={{ color: 'var(--accent-gold)', textTransform: 'capitalize', fontWeight: 600 }}>
                    {param}:{' '}
                  </span>
                  <span style={{ color: 'var(--text-secondary)' }}>{rat}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sensory Feedback & Dial-In Barista Diagnosis */}
      <div style={{ marginBottom: '28px' }}>
        <FeedbackForm recipe={recipe} />
      </div>

      {/* Verified Provenance & Sources Section */}
      {recipe.source_recipes && recipe.source_recipes.length > 0 && (
        <div className="glass-panel" style={{ padding: '24px', marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <BookOpen size={18} color="#3b82f6" />
            Verified Source Provenance
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {recipe.source_recipes.map((src, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-elevated)', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{src.source_name}</span>
                {src.url && (
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: 'var(--accent-gold)',
                      fontSize: '0.82rem',
                      textDecoration: 'none',
                    }}
                  >
                    View Original <ExternalLink size={13} />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Troubleshooting Guide */}
      {recipe.troubleshooting && recipe.troubleshooting.length > 0 && (
        <div className="glass-panel" style={{ padding: '24px', marginBottom: '40px' }}>
          <div
            onClick={() => setShowTroubleshooting(!showTroubleshooting)}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} color="var(--badge-med)" />
              Barista Troubleshooting Guide
            </h3>
            {showTroubleshooting ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>

          {showTroubleshooting && (
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)', display: 'grid', gap: '14px' }}>
              {recipe.troubleshooting.map((tip, idx) => (
                <div key={idx} style={{ background: 'var(--bg-elevated)', padding: '14px', borderRadius: 'var(--radius-sm)' }}>
                  <p style={{ fontWeight: 600, color: 'var(--accent-crema)' }}>Symptom: {tip.symptom}</p>
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    <strong>Likely cause:</strong> {tip.likely_cause}
                  </p>
                  <p style={{ fontSize: '0.88rem', color: 'var(--accent-gold)', marginTop: '4px' }}>
                    <strong>Dial-in adjustment:</strong> {tip.adjustment}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Retrieved Grounding Evidence (Expandable on demand) */}
      <EvidencePanel evidence={evidence} loading={evidenceLoading} />

      <div style={{ textAlign: 'center', marginTop: '28px' }}>
        <Link
          to="/"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '14px 28px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          Scan Another Coffee Bag
        </Link>
      </div>
    </div>
  );
};
