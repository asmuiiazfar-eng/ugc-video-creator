import { useState } from 'react';
import { Sparkles, Loader2, Clock, Edit3 } from 'lucide-react';
import { generateScript } from '../lib/api';
import { useWizard } from './WizardContainer';
import type { ScriptScene } from '../lib/types';

const AUDIENCES = [
  { value: 'general', label: 'General Audience' },
  { value: 'youth', label: 'Teens & Young Adults' },
  { value: 'professionals', label: 'Professionals' },
  { value: 'parents', label: 'Parents' },
  { value: 'gamers', label: 'Gamers' },
  { value: 'fitness', label: 'Fitness Enthusiasts' },
];

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'enthusiastic', label: 'Enthusiastic' },
  { value: 'educational', label: 'Educational' },
  { value: 'humorous', label: 'Humorous' },
];

const DURATIONS = [
  { value: '15-30', label: '15-30 sec' },
  { value: '30-60', label: '30-60 sec' },
  { value: '60-90', label: '60-90 sec' },
  { value: '90-120', label: '90-120 sec' },
];

export default function StepScript() {
  const { state, setProductName, setProductDescription, setTargetAudience, setTone, setVideoDuration, setScriptScenes, setGenerating } = useWizard();
  const [generating, setLocalGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!state.productName.trim() || !state.productDescription.trim()) return;
    setLocalGenerating(true);
    setGenerating(true);
    try {
      const scenes = await generateScript({
        product_name: state.productName,
        product_description: state.productDescription,
        target_audience: state.targetAudience,
        tone: state.tone,
        duration: state.videoDuration,
      });
      setScriptScenes(scenes);
    } catch {
      // ignore
    } finally {
      setLocalGenerating(false);
      setGenerating(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">Generate Your Script</h2>
      <p className="text-sm text-gray-500 mb-6">
        Enter your product details and let AI create a scene-by-scene script.
      </p>

      <div className="space-y-5">
        {/* Product Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product Name
          </label>
          <input
            type="text"
            value={state.productName}
            onChange={(e) => setProductName(e.target.value)}
            className="input-field"
            placeholder="e.g. GlowBiotic Skin Serum"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product Description
          </label>
          <textarea
            rows={4}
            value={state.productDescription}
            onChange={(e) => setProductDescription(e.target.value)}
            className="input-field resize-none"
            placeholder="Describe what makes this product unique, key benefits, target audience, etc."
          />
        </div>

        {/* Audience */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Audience
          </label>
          <select
            value={state.targetAudience}
            onChange={(e) => setTargetAudience(e.target.value)}
            className="input-field"
          >
            {AUDIENCES.map((a) => (
              <option key={a.value} value={a.value}>{a.label}</option>
            ))}
          </select>
        </div>

        {/* Tone */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tone
          </label>
          <div className="flex flex-wrap gap-2">
            {TONES.map((t) => (
              <button
                key={t.value}
                onClick={() => setTone(t.value)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  state.tone === t.value
                    ? 'bg-brand-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Video Duration
          </label>
          <div className="flex flex-wrap gap-2">
            {DURATIONS.map((d) => (
              <button
                key={d.value}
                onClick={() => setVideoDuration(d.value)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  state.videoDuration === d.value
                    ? 'bg-brand-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={generating || !state.productName.trim() || !state.productDescription.trim()}
          className="btn-primary w-full"
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating Script...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Generate Script
            </>
          )}
        </button>

        {/* Generated scenes */}
        {state.scriptScenes.length > 0 && (
          <div className="mt-6 space-y-3">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Edit3 className="h-4 w-4" />
              Generated Scenes ({state.scriptScenes.length})
            </h3>
            {state.scriptScenes.map((scene) => (
              <div
                key={scene.scene_number}
                className="rounded-xl border border-gray-200 bg-gray-50 p-4"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-brand-600 uppercase tracking-wide">
                    {scene.section_label || `Scene ${scene.scene_number}`}
                  </span>
                  <span className="flex items-center gap-1 text-xs text-gray-400">
                    <Clock className="h-3 w-3" />
                    {scene.duration_seconds}s
                  </span>
                </div>
                <p className="text-sm text-gray-700">{scene.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
