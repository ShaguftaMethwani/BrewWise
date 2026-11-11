import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX, Smartphone } from 'lucide-react';
import type { PourStep } from '../types';

interface Props {
  pourSchedule: PourStep[];
  targetBrewTimeSeconds: number;
}

export const BrewTimer: React.FC<Props> = ({ pourSchedule, targetBrewTimeSeconds }) => {
  const [seconds, setSeconds] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [wakeLockActive, setWakeLockActive] = useState(false);

  const wakeLockRef = useRef<any>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const lastStepIndexRef = useRef<number>(-1);

  // Play audio chime using standard Web Audio API
  const playChime = (freq = 587.33, duration = 0.3) => {
    if (!soundEnabled) return;
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioCtx();
      }
      if (audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume();
      }
      const ctx = audioCtxRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(freq * 1.5, ctx.currentTime + duration);

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch {
      // AudioContext unavailable or blocked
    }
  };

  // Screen Wake Lock API
  useEffect(() => {
    async function requestWakeLock() {
      if ('wakeLock' in navigator && isActive) {
        try {
          wakeLockRef.current = await (navigator as any).wakeLock.request('screen');
          setWakeLockActive(true);
          wakeLockRef.current.addEventListener('release', () => {
            setWakeLockActive(false);
          });
        } catch {
          setWakeLockActive(false);
        }
      }
    }

    if (isActive) {
      requestWakeLock();
    } else if (wakeLockRef.current) {
      wakeLockRef.current.release().catch(() => {});
      wakeLockRef.current = null;
      setWakeLockActive(false);
    }

    return () => {
      if (wakeLockRef.current) {
        wakeLockRef.current.release().catch(() => {});
      }
    };
  }, [isActive]);

  // Timer Tick
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

  // Step transition detection & audio / haptic cue
  useEffect(() => {
    if (!isActive) return;

    let currentStepIndex = -1;
    for (let i = 0; i < pourSchedule.length; i++) {
      if (seconds >= pourSchedule[i].start_time_seconds) {
        currentStepIndex = i;
      }
    }

    if (currentStepIndex !== lastStepIndexRef.current && currentStepIndex >= 0) {
      lastStepIndexRef.current = currentStepIndex;
      playChime(659.25, 0.4); // E5 note
      if ('vibrate' in navigator) {
        navigator.vibrate([80, 40, 80]);
      }
    }

    if (seconds === targetBrewTimeSeconds) {
      playChime(880, 0.8); // A5 finish note
      if ('vibrate' in navigator) {
        navigator.vibrate([200, 100, 200, 100, 300]);
      }
    }
  }, [seconds, isActive, pourSchedule, targetBrewTimeSeconds]);

  const toggleTimer = () => setIsActive(!isActive);
  const resetTimer = () => {
    setIsActive(false);
    setSeconds(0);
    lastStepIndexRef.current = -1;
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⏱️</span> Live Interactive Pour Timer
          </h3>
          {wakeLockActive && (
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.7rem',
              color: '#34d399',
              background: 'rgba(16, 185, 129, 0.1)',
              padding: '2px 8px',
              borderRadius: '999px',
              border: '1px solid rgba(16, 185, 129, 0.3)'
            }}>
              <Smartphone size={11} /> Screen Stay-Awake Active
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '4px 8px',
              color: soundEnabled ? 'var(--accent-gold)' : 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.75rem'
            }}
            title={soundEnabled ? 'Mute Chimes' : 'Enable Chimes'}
          >
            {soundEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
            {soundEnabled ? 'Audio Cues On' : 'Muted'}
          </button>

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
      </div>

      <div style={{
        textAlign: 'center',
        padding: '24px 0',
        background: '#fafafa',
        border: '1px solid var(--border-subtle)',
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
          background: '#e4e4e7',
          borderRadius: 'var(--radius-full)',
          margin: '12px auto 0',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${progressPercent}%`,
            background: 'var(--pastel-sage-text)',
            transition: 'width 0.4s ease',
          }} />
        </div>
      </div>

      <div style={{
        background: '#fafafa',
        border: '1px solid var(--border-subtle)',
        padding: '16px',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '20px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--pastel-sage-text)', fontWeight: 600 }}>
              Current Pour Action (Step {activeStep?.step_number})
            </span>
            <p style={{ fontSize: '1rem', fontWeight: 600, marginTop: '2px', color: 'var(--text-primary)' }}>
              {activeStep?.technique}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Scale Target</span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
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
          className={isActive ? 'btn-pastel-peach' : 'btn-pastel-sage'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 28px',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 600,
            fontSize: '1rem',
            cursor: 'pointer'
          }}
        >
          {isActive ? <Pause size={18} /> : <Play size={18} />}
          {isActive ? 'Pause' : seconds > 0 ? 'Resume' : 'Start Brew'}
        </button>

        <button
          onClick={resetTimer}
          className="btn-pastel-sand"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 500,
            cursor: 'pointer'
          }}
        >
          <RotateCcw size={16} />
          Reset
        </button>
      </div>
    </div>
  );
};
