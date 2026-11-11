import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Eye, ShieldCheck, Compass } from 'lucide-react';
import { ImageCapture } from '../components/ImageCapture';
import type { CoffeeProfileDraft } from '../types';

export const Home: React.FC = () => {
  const navigate = useNavigate();

  const handleScanSuccess = (draft: CoffeeProfileDraft) => {
    navigate(`/profile/${draft.id}`, { state: { draft } });
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '48px 20px 80px' }}>
      <div style={{ textAlign: 'center', marginBottom: '44px' }} className="animate-fade-in">
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '999px',
          background: 'var(--pastel-sage)',
          border: '1px solid var(--pastel-sage-border)',
          color: 'var(--pastel-sage-text)',
          fontSize: '0.82rem',
          fontWeight: 600,
          marginBottom: '18px',
        }}>
          <Sparkles size={14} />
          <span>Intelligent Pour-Over Precision</span>
        </div>

        <h1 style={{
          fontSize: 'clamp(2.2rem, 4.5vw, 3.4rem)',
          fontWeight: 700,
          letterSpacing: '-0.03em',
          lineHeight: 1.15,
          color: 'var(--text-primary)',
          marginBottom: '16px',
        }}>
          Dial in every bean.<br />
          <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>
            From bag photo to balanced cup.
          </span>
        </h1>

        <p style={{
          fontSize: '1.05rem',
          color: 'var(--text-secondary)',
          maxWidth: '540px',
          margin: '0 auto',
          lineHeight: 1.6,
        }}>
          Photograph any coffee bag to extract origin, roast, and process. BrewWise synthesises precision pour-over parameters tailored to your beans and gear.
        </p>
      </div>

      <div style={{ marginBottom: '60px' }}>
        <ImageCapture onScanSuccess={handleScanSuccess} />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '20px',
      }}>
        <div className="glass-panel" style={{ padding: '24px', background: '#ffffff' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'var(--pastel-sky)',
            border: '1px solid var(--pastel-sky-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--pastel-sky-text)',
            marginBottom: '14px',
          }}>
            <Eye size={18} />
          </div>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>Vision Bag OCR</h4>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Token-optimised Gemini Flash vision extracts roaster, varietals, process method, and notes with high precision.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '24px', background: '#ffffff' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'var(--pastel-sage)',
            border: '1px solid var(--pastel-sage-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--pastel-sage-text)',
            marginBottom: '14px',
          }}>
            <ShieldCheck size={18} />
          </div>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>Strict Verification</h4>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Mathematical validation ensures water ratios, pour steps, temperature thresholds, and drawdown timings always sum correctly.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '24px', background: '#ffffff' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'var(--pastel-lavender)',
            border: '1px solid var(--pastel-lavender-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--pastel-lavender-text)',
            marginBottom: '14px',
          }}>
            <Compass size={18} />
          </div>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>Equipment Aware</h4>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Flow dynamics and grind settings adjusted specifically for your conical or flat dripper and precision hand/electric grinder.
          </p>
        </div>
      </div>
    </div>
  );
};
