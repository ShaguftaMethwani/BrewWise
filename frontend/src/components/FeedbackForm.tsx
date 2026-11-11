import React, { useState } from 'react';
import type { BrewLog, BrewLogCreate, PersonalisedRecipe } from '../types';
import { logBrew } from '../api';

interface FeedbackFormProps {
  recipe: PersonalisedRecipe;
  onBrewLogged?: (brew: BrewLog) => void;
  onClose?: () => void;
}

export const FeedbackForm: React.FC<FeedbackFormProps> = ({ recipe, onBrewLogged, onClose }) => {
  const [sourness, setSourness] = useState<number>(3);
  const [bitterness, setBitterness] = useState<number>(3);
  const [sweetness, setSweetness] = useState<number>(3);
  const [body, setBody] = useState<number>(3);
  const [satisfaction, setSatisfaction] = useState<number>(4);
  const [drawdownSpeed, setDrawdownSpeed] = useState<'fast' | 'normal' | 'slow' | 'stalled'>('normal');
  const [flavourNotes, setFlavourNotes] = useState<string>('');

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [loggedBrew, setLoggedBrew] = useState<BrewLog | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const payload: BrewLogCreate = {
      recipe_id: recipe.id || recipe.recipe_id,
      coffee_profile_id: recipe.coffee_profile_id,
      dripper: recipe.dripper,
      grinder: recipe.grinder,
      actual_dose_g: recipe.dose_g,
      actual_water_g: recipe.water_g,
      actual_grind_setting: recipe.grind_setting || undefined,
      actual_temp_c: recipe.water_temperature_c,
      actual_brew_time_seconds: recipe.target_brew_time_seconds,
      sourness,
      bitterness,
      sweetness,
      body,
      overall_satisfaction: satisfaction,
      drawdown_speed: drawdownSpeed,
      flavour_notes: flavourNotes.trim() || undefined,
    };

    try {
      const brew = await logBrew(payload);
      setLoggedBrew(brew);
      if (onBrewLogged) {
        onBrewLogged(brew);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit brew feedback.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      background: 'rgba(28, 25, 23, 0.85)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(217, 119, 6, 0.25)',
      borderRadius: '16px',
      padding: '24px',
      color: '#f5f5f4',
      marginTop: '24px',
      boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.6)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>☕</span> Sensory Feedback & Barista Diagnosis
          </h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#a8a29e' }}>
            Rate your cup to receive deterministic brew adjustments for your next pour.
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#a8a29e',
              fontSize: '1.25rem',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        )}
      </div>

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          padding: '10px 14px',
          borderRadius: '8px',
          fontSize: '0.85rem',
          marginBottom: '16px'
        }}>
          {error}
        </div>
      )}

      {loggedBrew && loggedBrew.adjustments ? (
        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
          <div style={{
            background: 'rgba(217, 119, 6, 0.1)',
            border: '1px solid rgba(217, 119, 6, 0.35)',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{
                background: loggedBrew.adjustments.diagnosis.includes('Dialed-In')
                  ? 'rgba(16, 185, 129, 0.2)'
                  : 'rgba(245, 158, 11, 0.2)',
                color: loggedBrew.adjustments.diagnosis.includes('Dialed-In') ? '#34d399' : '#fbbf24',
                padding: '4px 10px',
                borderRadius: '999px',
                fontSize: '0.8rem',
                fontWeight: 600,
                border: '1px solid currentColor'
              }}>
                {loggedBrew.adjustments.diagnosis}
              </span>
              <span style={{ fontSize: '0.8rem', color: '#a8a29e' }}>
                Overall: {loggedBrew.overall_satisfaction}/5 ★
              </span>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#f59e0b', letterSpacing: '0.05em', fontWeight: 600 }}>
                Primary Action
              </div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#fafaf9', marginTop: '4px' }}>
                👉 {loggedBrew.adjustments.primary_adjustment}
              </div>
            </div>

            {loggedBrew.adjustments.secondary_adjustment && (
              <div style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#a8a29e', letterSpacing: '0.05em' }}>
                  Secondary Action
                </div>
                <div style={{ fontSize: '0.9rem', color: '#d6d3d1', marginTop: '2px' }}>
                  ⚡ {loggedBrew.adjustments.secondary_adjustment}
                </div>
              </div>
            )}

            <div style={{
              background: 'rgba(0, 0, 0, 0.25)',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '0.85rem',
              color: '#d6d3d1',
              lineHeight: 1.5
            }}>
              <strong>Barista Rationale:</strong> {loggedBrew.adjustments.rationale}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={() => setLoggedBrew(null)}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#fafaf9',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                padding: '8px 16px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              Re-evaluate
            </button>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: 'linear-gradient(135deg, #d97706, #b45309)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}
              >
                Done
              </button>
            )}
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '20px' }}>
            {/* Sourness */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <span style={{ color: '#e7e5e4' }}>Sourness / Acidity</span>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>{sourness}/5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={sourness}
                onChange={(e) => setSourness(parseInt(e.target.value, 10))}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#78716c' }}>
                <span>Flat (1)</span>
                <span>Tart/Sour (5)</span>
              </div>
            </div>

            {/* Bitterness */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <span style={{ color: '#e7e5e4' }}>Bitterness / Astringency</span>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>{bitterness}/5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={bitterness}
                onChange={(e) => setBitterness(parseInt(e.target.value, 10))}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#78716c' }}>
                <span>Clean (1)</span>
                <span>Harsh/Dry (5)</span>
              </div>
            </div>

            {/* Sweetness */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <span style={{ color: '#e7e5e4' }}>Sweetness</span>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>{sweetness}/5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={sweetness}
                onChange={(e) => setSweetness(parseInt(e.target.value, 10))}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#78716c' }}>
                <span>Muted (1)</span>
                <span>Syrupy (5)</span>
              </div>
            </div>

            {/* Body */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <span style={{ color: '#e7e5e4' }}>Body & Mouthfeel</span>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>{body}/5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={body}
                onChange={(e) => setBody(parseInt(e.target.value, 10))}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#78716c' }}>
                <span>Watery (1)</span>
                <span>Full/Velvety (5)</span>
              </div>
            </div>
          </div>

          {/* Drawdown & Overall Satisfaction */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#e7e5e4', marginBottom: '8px' }}>
                Drawdown Flow Speed
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {(['fast', 'normal', 'slow', 'stalled'] as const).map((speed) => (
                  <button
                    key={speed}
                    type="button"
                    onClick={() => setDrawdownSpeed(speed)}
                    style={{
                      flex: 1,
                      padding: '8px 4px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      textTransform: 'capitalize',
                      border: drawdownSpeed === speed ? '1px solid #f59e0b' : '1px solid rgba(255, 255, 255, 0.1)',
                      background: drawdownSpeed === speed ? 'rgba(245, 158, 11, 0.2)' : 'rgba(0, 0, 0, 0.3)',
                      color: drawdownSpeed === speed ? '#fbbf24' : '#a8a29e',
                      cursor: 'pointer'
                    }}
                  >
                    {speed}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <span style={{ color: '#e7e5e4' }}>Overall Satisfaction</span>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>{satisfaction}/5 ★</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={satisfaction}
                onChange={(e) => setSatisfaction(parseInt(e.target.value, 10))}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#78716c' }}>
                <span>Disappointing (1)</span>
                <span>Peak Cup (5)</span>
              </div>
            </div>
          </div>

          {/* Tasting Notes */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#e7e5e4', marginBottom: '6px' }}>
              Personal Tasting & Sensory Notes (optional)
            </label>
            <textarea
              value={flavourNotes}
              onChange={(e) => setFlavourNotes(e.target.value)}
              placeholder="e.g. Crisp green apple acidity, brown sugar sweetness, slightly dry finish..."
              rows={2}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '8px',
                padding: '10px 12px',
                color: '#fafaf9',
                fontSize: '0.85rem',
                resize: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: 'transparent',
                  color: '#a8a29e',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  padding: '10px 18px',
                  borderRadius: '8px',
                  fontSize: '0.9rem',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                background: 'linear-gradient(135deg, #d97706, #b45309)',
                color: '#ffffff',
                border: 'none',
                padding: '10px 22px',
                borderRadius: '8px',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                opacity: isSubmitting ? 0.7 : 1,
                boxShadow: '0 4px 14px rgba(217, 119, 6, 0.4)'
              }}
            >
              {isSubmitting ? 'Analysing Cup...' : 'Log Brew & Get Diagnosis 🚀'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
