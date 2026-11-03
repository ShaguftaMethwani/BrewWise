import React, { useState, useRef } from 'react';
import { Camera, UploadCloud, RefreshCw, AlertCircle } from 'lucide-react';
import { scanCoffeeBag } from '../api';
import type { CoffeeProfileDraft } from '../types';

interface Props {
  onScanSuccess: (draft: CoffeeProfileDraft) => void;
}

export const ImageCapture: React.FC<Props> = ({ onScanSuccess }) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const processAndUpload = async (file: File) => {
    setError(null);
    setIsScanning(true);

    try {
      const objectUrl = URL.createObjectURL(file);
      setPreview(objectUrl);

      const compressedBlob = await compressImage(file);
      const uploadFile = new File([compressedBlob], file.name, { type: 'image/jpeg' });

      const result = await scanCoffeeBag(uploadFile);
      onScanSuccess(result);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze coffee bag image');
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processAndUpload(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processAndUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '28px', maxWidth: '580px', margin: '0 auto', textAlign: 'center' }}>
      <input
        type="file"
        ref={fileInputRef}
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
      <input
        type="file"
        ref={cameraInputRef}
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      {preview ? (
        <div style={{ position: 'relative', borderRadius: 'var(--radius-sm)', overflow: 'hidden', marginBottom: '20px' }}>
          <img
            src={preview}
            alt="Coffee bag preview"
            style={{ width: '100%', maxHeight: '340px', objectFit: 'contain', background: '#0a0908' }}
          />
          {isScanning && (
            <div style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(15, 13, 12, 0.85)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '14px',
            }}>
              <RefreshCw size={36} color="var(--accent-gold)" style={{ animation: 'spin 1.5s linear infinite' }} />
              <div>
                <p style={{ fontWeight: 600, color: '#fff', fontSize: '1.05rem' }}>Analyzing Coffee Bag...</p>
                <p style={{ fontSize: '0.85rem', color: 'var(--accent-crema)', marginTop: '4px' }}>
                  Extracting roaster, process, and roast profile with Gemini Flash
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '48px 24px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            background: 'rgba(255, 255, 255, 0.02)',
            marginBottom: '20px',
          }}
          className="glow-hover"
        >
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(229, 168, 82, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            color: 'var(--accent-gold)',
          }}>
            <UploadCloud size={32} />
          </div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '6px' }}>Upload or Drop Coffee Bag Photo</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '380px', margin: '0 auto' }}>
            Take a clear photo of the front of your coffee bag showing roaster, origin, process, or tasting notes.
          </p>
        </div>
      )}

      {error && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '12px 16px',
          background: 'var(--badge-low-bg)',
          border: '1px solid var(--badge-low)',
          borderRadius: 'var(--radius-sm)',
          color: '#fca5a5',
          fontSize: '0.9rem',
          marginBottom: '20px',
          textAlign: 'left',
        }}>
          <AlertCircle size={20} color="var(--badge-low)" style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
        <button
          onClick={() => cameraInputRef.current?.click()}
          disabled={isScanning}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 20px',
            borderRadius: 'var(--radius-sm)',
            background: 'linear-gradient(135deg, var(--accent-gold), var(--accent-copper))',
            color: '#0f0d0c',
            fontWeight: 600,
            fontSize: '0.95rem',
            boxShadow: 'var(--shadow-glow)',
          }}
        >
          <Camera size={18} />
          Camera Scan
        </button>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isScanning}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 20px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)',
            fontWeight: 500,
            fontSize: '0.95rem',
          }}
        >
          <UploadCloud size={18} />
          Choose Photo
        </button>
      </div>
    </div>
  );
};

async function compressImage(file: File, maxDim = 2048, quality = 0.85): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          } else {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return resolve(file);
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (blob) resolve(blob);
            else resolve(file);
          },
          'image/jpeg',
          quality
        );
      };
      img.onerror = reject;
      img.src = e.target?.result as string;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
