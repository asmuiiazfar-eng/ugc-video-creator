import { useEffect, useState } from 'react';
import { Image, Wand2, Loader2, Check } from 'lucide-react';
import { getBackgrounds, generateBackground } from '../lib/api';
import type { Background } from '../lib/types';
import { useWizard } from './WizardContainer';

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'nature', label: 'Nature' },
  { value: 'urban', label: 'Urban' },
  { value: 'indoor', label: 'Indoor' },
  { value: 'studio', label: 'Studio' },
  { value: 'abstract', label: 'Abstract' },
  { value: 'lifestyle', label: 'Lifestyle' },
];

const LOCATIONS = [
  'Living Room', 'Office', 'Cafe', 'Park', 'City Street',
  'Beach', 'Kitchen', 'Bedroom', 'Gym', 'Studio',
];

const MOODS = [
  'Bright', 'Warm', 'Cool', 'Dark', 'Minimal',
  'Cozy', 'Professional', 'Vibrant', 'Calm',
];

const TRANSITIONS = [
  'fade', 'dissolve', 'slide_left', 'slide_right', 'zoom_in', 'zoom_out',
];

interface SceneBgProps {
  sceneNumber: number;
  label: string;
}

export default function StepBackground() {
  const { scenes, setBackground } = useWizard();

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">Backgrounds Per Scene</h2>
      <p className="text-sm text-gray-500 mb-6">
        Pick a background and transition for each scene.
      </p>

      {scenes.length === 0 ? (
        <p className="text-sm text-gray-400">No scenes yet. Go back and generate a script first.</p>
      ) : (
        <div className="space-y-8">
          {scenes.map((scene, idx) => (
            <SceneBackgroundPicker
              key={scene.id || idx}
              sceneNumber={scene.scene_number}
              label={scene.section_label || `Scene ${scene.scene_number}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SceneBackgroundPicker({ sceneNumber, label }: SceneBgProps) {
  const { state, setBackground } = useWizard();
  const [tab, setTab] = useState<'library' | 'generate'>('library');
  const [bgs, setBgs] = useState<Background[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [generating, setGenerating] = useState(false);
  const [location, setLocation] = useState('Living Room');
  const [mood, setMood] = useState('Bright');

  const current = state.backgrounds[sceneNumber];

  useEffect(() => {
    setLoading(true);
    getBackgrounds(category || undefined)
      .then(setBgs)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [category]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const bg = await generateBackground({ location, mood });
      setBackground(sceneNumber, bg, current?.transition || 'fade');
    } catch {
      // ignore
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
            {sceneNumber}
          </div>
          <h3 className="font-semibold text-gray-900">{label}</h3>
        </div>
        {current?.background && (
          <span className="badge-green">Background set</span>
        )}
      </div>

      {/* Tabs */}
      <div className="mb-4 flex rounded-lg bg-gray-100 p-1">
        <button
          onClick={() => setTab('library')}
          className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            tab === 'library' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'
          }`}
        >
          <Image className="h-3.5 w-3.5" />
          Library
        </button>
        <button
          onClick={() => setTab('generate')}
          className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            tab === 'generate' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'
          }`}
        >
          <Wand2 className="h-3.5 w-3.5" />
          Generate
        </button>
      </div>

      {/* Library tab */}
      {tab === 'library' && (
        <div>
          <div className="flex flex-wrap gap-1.5 mb-4">
            {CATEGORIES.map((c) => (
              <button
                key={c.value}
                onClick={() => setCategory(c.value)}
                className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                  category === c.value
                    ? 'bg-brand-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="grid grid-cols-4 gap-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="aspect-video animate-pulse rounded-lg bg-gray-200" />
              ))}
            </div>
          ) : bgs.length === 0 ? (
            <p className="text-sm text-gray-400 py-4">No backgrounds found</p>
          ) : (
            <div className="grid grid-cols-4 gap-3">
              {bgs.map((bg) => {
                const selected = current?.background?.id === bg.id;
                return (
                  <button
                    key={bg.id}
                    onClick={() => setBackground(sceneNumber, bg, current?.transition || 'fade')}
                    className={`relative aspect-video overflow-hidden rounded-lg border-2 transition-all ${
                      selected
                        ? 'border-brand-600 ring-2 ring-brand-200'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <img
                      src={bg.thumbnail_url}
                      alt={bg.name}
                      className="h-full w-full object-cover"
                    />
                    {selected && (
                      <div className="absolute inset-0 flex items-center justify-center bg-brand-600/30">
                        <Check className="h-5 w-5 text-white" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Generate tab */}
      {tab === 'generate' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Location</label>
              <select
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="input-field text-sm"
              >
                {LOCATIONS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Mood</label>
              <select
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                className="input-field text-sm"
              >
                {MOODS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn-primary w-full"
          >
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4" />
                Generate Background
              </>
            )}
          </button>
        </div>
      )}

      {/* Transition */}
      <div className="mt-4">
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Transition
        </label>
        <select
          value={current?.transition || 'fade'}
          onChange={(e) =>
            setBackground(sceneNumber, current?.background, e.target.value)
          }
          className="input-field text-sm"
        >
          {TRANSITIONS.map((t) => (
            <option key={t} value={t}>
              {t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
