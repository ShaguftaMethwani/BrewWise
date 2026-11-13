import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, Sliders, AlertCircle, RefreshCw } from 'lucide-react';
import { getProfile, updateProfile, getDrippers, getGrinders, generateRecipe } from '../api';
import type { CoffeeProfileDraft, EquipmentItem } from '../types';
import { ConfidenceBadge } from '../components/ConfidenceBadge';

const KNOWN_PROCESSES = ['washed', 'natural', 'honey', 'anaerobic_natural', 'anaerobic_washed', 'carbonic_maceration', 'thermal_shock'];
const KNOWN_ROASTS = ['light', 'medium_light', 'medium', 'medium_dark', 'dark', 'omni'];

// Turns a stored value such as "natural_-_carbonic_maceration" into "Natural Carbonic Maceration"
const prettify = (value: string) =>
  value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');

// Typed-in profiles have nothing "extracted", so confidence badges are hidden for them
const FieldBadge: React.FC<{ manual: boolean; confidence: number; source: string }> = ({ manual, confidence, source }) =>
  manual ? null : <ConfidenceBadge confidence={confidence} source={source as any} />;

export const ProfileEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [draft, setDraft] = useState<CoffeeProfileDraft | null>(location.state?.draft || null);
  const [loading, setLoading] = useState(!draft);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [drippers, setDrippers] = useState<EquipmentItem[]>([]);
  const [grinders, setGrinders] = useState<EquipmentItem[]>([]);

  const [selectedDripper, setSelectedDripper] = useState<string>('Hario V60 (02)');
  const [selectedGrinder, setSelectedGrinder] = useState<string>('');
  const [isCustomGrinder, setIsCustomGrinder] = useState<boolean>(false);
  const [customGrinder, setCustomGrinder] = useState<string>('');
  const [dose, setDose] = useState<number>(15);
  const [strength, setStrength] = useState<'light' | 'balanced' | 'strong'>('balanced');

  const [formData, setFormData] = useState({
    brand: '',
    product_name: '',
    estate: '',
    country: '',
    region: '',
    varietal: '',
    process: '',
    roast_level: '',
    tasting_notes: '',
    altitude: '',
  });

  const isManual = draft?.extraction_model === 'manual_entry';
  const hasAnyDetail = Object.values(formData).some((v) => v.trim() !== '');

  useEffect(() => {
    async function loadData() {
      try {
        if (!draft && id) {
          const fetchedDraft = await getProfile(id);
          setDraft(fetchedDraft);
        }
        const [dList, gList] = await Promise.all([getDrippers(), getGrinders()]);
        setDrippers(dList);
        setGrinders(gList);
      } catch (err: any) {
        setError(err.message || 'Failed to load details');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id, draft]);

  useEffect(() => {
    if (draft) {
      setFormData({
        brand: draft.brand.value || '',
        product_name: draft.product_name.value || '',
        estate: draft.estate.value || '',
        country: draft.country.value || '',
        region: draft.region.value || '',
        varietal: draft.varietal.value || '',
        process: draft.process.value || '',
        roast_level: draft.roast_level.value || '',
        tasting_notes: draft.tasting_notes.value || '',
        altitude: draft.altitude.value || '',
      });
    }
  }, [draft]);

  const handleFieldChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleGenerate = async () => {
    if (!draft) return;
    setGenerating(true);
    setError(null);

    try {
      await updateProfile(draft.id, formData);

      const finalGrinder = isCustomGrinder ? customGrinder.trim() : selectedGrinder;

      const recipe = await generateRecipe({
        coffee_profile_id: draft.id,
        dripper: selectedDripper,
        grinder: finalGrinder || undefined,
        dose_preference_g: dose,
        target_strength: strength,
      });

      navigate(`/recipe/${recipe.recipe_id}`, { state: { recipe } });
    } catch (err: any) {
      setError(err.message || 'Failed to generate recipe');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px' }}>
        <RefreshCw size={32} color="var(--accent-gold)" style={{ animation: 'spin 1.5s linear infinite' }} />
        <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>Loading coffee profile...</p>
      </div>
    );
  }

  if (!draft) {
    return (
      <div style={{ maxWidth: '600px', margin: '60px auto', textAlign: 'center' }}>
        <p style={{ color: 'var(--badge-low)' }}>Coffee profile not found.</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', padding: '30px 20px 80px' }} className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <span style={{ fontSize: '0.85rem', color: 'var(--accent-gold)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {isManual ? 'Step 2 of 3 · Coffee Details' : 'Step 2 of 3 · Extraction Review'}
          </span>
          <h2 style={{ fontSize: '2rem', fontFamily: 'var(--font-serif)', marginTop: '4px' }}>
            {isManual ? 'Enter Your Coffee Details' : 'Review Extracted Coffee Profile'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            {isManual
              ? 'Fill in what you know. Leave anything you are unsure of blank — it is treated as unknown, not guessed.'
              : 'Verify the extracted bag data below. You can refine any field before generating your recipe.'}
          </p>
        </div>
      </div>

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
          marginBottom: '20px',
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="glass-panel" style={{ padding: '28px', marginBottom: '32px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>ROASTER / BRAND</label>
              <FieldBadge manual={isManual} confidence={draft.brand.confidence} source={draft.brand.source} />
            </div>
            <input
              type="text"
              value={formData.brand}
              onChange={(e) => handleFieldChange('brand', e.target.value)}
              placeholder="e.g. Subko, Blue Tokai"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>COFFEE / PRODUCT NAME</label>
              <FieldBadge manual={isManual} confidence={draft.product_name.confidence} source={draft.product_name.source} />
            </div>
            <input
              type="text"
              value={formData.product_name}
              onChange={(e) => handleFieldChange('product_name', e.target.value)}
              placeholder="e.g. Project Sankalp, Attikan"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>ESTATE / FARM</label>
              <FieldBadge manual={isManual} confidence={draft.estate.confidence} source={draft.estate.source} />
            </div>
            <input
              type="text"
              value={formData.estate}
              onChange={(e) => handleFieldChange('estate', e.target.value)}
              placeholder="e.g. Attikan Estate, Riverdale"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>ORIGIN COUNTRY</label>
              <FieldBadge manual={isManual} confidence={draft.country.confidence} source={draft.country.source} />
            </div>
            <input
              type="text"
              value={formData.country}
              onChange={(e) => handleFieldChange('country', e.target.value)}
              placeholder="e.g. Ethiopia, India, Colombia"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>PROCESS METHOD</label>
              <FieldBadge manual={isManual} confidence={draft.process.confidence} source={draft.process.source} />
            </div>
            <select
              value={formData.process}
              onChange={(e) => handleFieldChange('process', e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="">Not stated / unknown</option>
              <option value="washed">Washed</option>
              <option value="natural">Natural</option>
              <option value="honey">Honey</option>
              <option value="anaerobic_natural">Anaerobic Natural</option>
              <option value="anaerobic_washed">Anaerobic Washed</option>
              <option value="carbonic_maceration">Carbonic Maceration</option>
              <option value="thermal_shock">Thermal Shock</option>
              {/* A value read from the bag that is not in the list is kept and shown, not replaced */}
              {formData.process && !KNOWN_PROCESSES.includes(formData.process) && (
                <option value={formData.process}>{prettify(formData.process)}</option>
              )}
            </select>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>ROAST LEVEL</label>
              <FieldBadge manual={isManual} confidence={draft.roast_level.confidence} source={draft.roast_level.source} />
            </div>
            <select
              value={formData.roast_level}
              onChange={(e) => handleFieldChange('roast_level', e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="">Not stated / unknown</option>
              <option value="light">Light Roast</option>
              <option value="medium_light">Medium-Light</option>
              <option value="medium">Medium</option>
              <option value="medium_dark">Medium-Dark</option>
              <option value="dark">Dark Roast</option>
              <option value="omni">Omni Roast</option>
              {formData.roast_level && !KNOWN_ROASTS.includes(formData.roast_level) && (
                <option value={formData.roast_level}>{prettify(formData.roast_level)}</option>
              )}
            </select>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>VARIETAL</label>
              <FieldBadge manual={isManual} confidence={draft.varietal.confidence} source={draft.varietal.source} />
            </div>
            <input
              type="text"
              value={formData.varietal}
              onChange={(e) => handleFieldChange('varietal', e.target.value)}
              placeholder="e.g. Geisha, Heirloom, SLN 795"
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>TASTING NOTES</label>
            <FieldBadge manual={isManual} confidence={draft.tasting_notes.confidence} source={draft.tasting_notes.source} />
          </div>
          <input
            type="text"
            value={formData.tasting_notes}
            onChange={(e) => handleFieldChange('tasting_notes', e.target.value)}
            placeholder="e.g. Jasmine, Peach, Bergamot, Honeycomb"
            style={{ width: '100%' }}
          />
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '28px', marginBottom: '32px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={20} color="var(--accent-gold)" />
          Brewing Setup & Preferences
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              POUR-OVER DRIPPER
            </label>
            <select
              value={selectedDripper}
              onChange={(e) => setSelectedDripper(e.target.value)}
              style={{ width: '100%' }}
            >
              {drippers.map((d) => (
                <option key={d.id} value={`${d.brand} ${d.model}`}>
                  {d.brand} {d.model} ({d.geometry})
                </option>
              ))}
            </select>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                GRINDER (OPTIONAL)
              </label>
              <button
                type="button"
                onClick={() => {
                  setIsCustomGrinder(!isCustomGrinder);
                  if (!isCustomGrinder && !customGrinder) {
                    setCustomGrinder(selectedGrinder);
                  }
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--pastel-sky-text)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline'
                }}
              >
                {isCustomGrinder ? '← Choose from dropdown' : '+ Type other grinder'}
              </button>
            </div>

            {isCustomGrinder ? (
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  placeholder="Type your grinder (e.g. Kingrinder K6, 1Zpresso K-Ultra, Ode Gen 2)..."
                  value={customGrinder}
                  onChange={(e) => setCustomGrinder(e.target.value)}
                  style={{ width: '100%', paddingRight: '30px' }}
                  autoFocus
                />
              </div>
            ) : (
              <select
                value={selectedGrinder}
                onChange={(e) => {
                  if (e.target.value === '__custom__') {
                    setIsCustomGrinder(true);
                  } else {
                    setSelectedGrinder(e.target.value);
                  }
                }}
                style={{ width: '100%' }}
              >
                <option value="">Standard Hand/Electric Grinder</option>
                {grinders.map((g) => (
                  <option key={g.id} value={`${g.brand} ${g.model}`}>
                    {g.brand} {g.model}
                  </option>
                ))}
                <option value="__custom__">✏️ Other / Custom Grinder (Type name)...</option>
              </select>
            )}
          </div>

          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              COFFEE DOSE (GRAMS)
            </label>
            <input
              type="number"
              min={10}
              max={30}
              step={0.5}
              value={dose}
              onChange={(e) => setDose(parseFloat(e.target.value) || 15)}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              STRENGTH PREFERENCE
            </label>
            <select
              value={strength}
              onChange={(e: any) => setStrength(e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="light">Light & Delicate (1:17)</option>
              <option value="balanced">Balanced & Sweet (1:16)</option>
              <option value="strong">Rich & Heavy (1:15)</option>
            </select>
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center' }}>
        <button
          onClick={handleGenerate}
          disabled={generating || (isManual && !hasAnyDetail)}
          className="btn-pastel-sage"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            padding: '15px 36px',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 700,
            fontSize: '1.05rem',
            cursor: generating || (isManual && !hasAnyDetail) ? 'not-allowed' : 'pointer',
            opacity: isManual && !hasAnyDetail ? 0.55 : 1,
          }}
        >
          {generating ? (
            <>
              <RefreshCw size={20} style={{ animation: 'spin 1.5s linear infinite' }} />
              Dialing In Precision Recipe...
            </>
          ) : (
            <>
              <Sparkles size={20} />
              Generate Dialed-In Recipe
              <ArrowRight size={20} />
            </>
          )}
        </button>
        {isManual && !hasAnyDetail && (
          <p style={{ marginTop: '10px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Enter at least one coffee detail above to generate a recipe.
          </p>
        )}
      </div>
    </div>
  );
};
