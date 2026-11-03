import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Volume2 } from 'lucide-react';
import type { PourStep } from '../types';

interface Props {
  pourSchedule: PourStep[];
  targetBrewTimeSeconds: number;
}

export const BrewTimer: React.FC<Props> = ({ pourSchedule, targetBrewTimeSeconds }) => {
  const [seconds, setSeconds] = useState(0);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let interval: any = null;
    if (isActive) {
      interval = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isActive]);

  const toggleTimer = () => setIsActive(!isActive);
  const resetTimer = () => {
    setIsActive(false);
    setSeconds(0);
  };

  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  let currentStepIndex = -1;
  for (let i = 0; i < pourSchedule.length; i++) {
    if (seconds >= pourSchedule[i].start_time_seconds) {
      currentStepIndex = i;
    }
  }

  const activeStep = currentStepIndex >= 0 ? pourSchedule[currentStepIndex] : pourSchedule[0];
  const nextStep = currentStepIndex + 1 < pourSchedule.length ? pourSchedule[currentStepIndex + 1] : null;
  const isFinished = seconds >= targetBrewTimeSeconds;

  const progressPercent = Math.min(100, Math.round((seconds / targetBrewTimeSeconds) * 100));

  return (
    <div className="glass-panel" style={{ padding: '24px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glow)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Volume2 size={18} color="var(--accent-gold)" />
          Live Interactive Brew Mode
        </h3>
        <span style={{
          fontSize: '0.8rem',
          color: isFinished ? 'var(--badge-high)' : 'var(--text-secondary)',
          background: isFinished ? 'var(--badge-high-bg)' : 'var(--bg-elevated)',
          padding: '4px 10px',
          borderRadius: 'var(--radius-full)',
          fontWeight: 600,
        }}>
          {isFinished ? 'Brew Complete 🎉' : `Target: ${formatTime(targetBrewTimeSeconds)}`}
        </span>
      </div>

      <div style={{
        textAlign: 'center',
        padding: '20px 0',
        background: 'rgba(0, 0, 0, 0.25)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '20px',
      }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '3.5rem',
          fontWeight: 700,
          color: isFinished ? 'var(--badge-high)' : 'var(--text-primary)',
          letterSpacing: '2px',
        }}>
          {formatTime(seconds)}
        </div>

        <div style={{
          width: '80%',
          height: '6px',
          background: 'rgba(255, 255, 255, 0.08)',
          borderRadius: 'var(--radius-full)',
          margin: '12px auto 0',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${progressPercent}%`,
            background: 'linear-gradient(90deg, var(--accent-copper), var(--accent-gold))',
            transition: 'width 0.4s ease',
          }} />
        </div>
      </div>

      <div style={{
        background: 'var(--bg-elevated)',
        padding: '16px',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '20px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent-gold)' }}>
              Current Pour Action (Step {activeStep?.step_number})
            </span>
            <p style={{ fontSize: '1rem', fontWeight: 600, marginTop: '2px' }}>
              {activeStep?.technique}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Scale Target</span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-crema)' }}>
              {activeStep?.cumulative_water_g}g
            </p>
          </div>
        </div>

        {nextStep && (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            Next: Step {nextStep.step_number} ({nextStep.water_g}g) at {formatTime(nextStep.start_time_seconds)}
          </p>
        )}
      </div>

      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
        <button
          onClick={toggleTimer}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 28px',
            borderRadius: 'var(--radius-sm)',
            background: isActive ? 'var(--bg-elevated)' : 'linear-gradient(135deg, var(--accent-gold), var(--accent-copper))',
            color: isActive ? 'var(--text-primary)' : '#0f0d0c',
            fontWeight: 600,
            fontSize: '1rem',
            boxShadow: isActive ? 'none' : 'var(--shadow-glow)',
          }}
        >
          {isActive ? <Pause size={18} /> : <Play size={18} />}
          {isActive ? 'Pause' : seconds > 0 ? 'Resume' : 'Start Brew'}
        </button>

        <button
          onClick={resetTimer}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            fontWeight: 500,
          }}
        >
          <RotateCcw size={16} />
          Reset
        </button>
      </div>
    </div>
  );
};
