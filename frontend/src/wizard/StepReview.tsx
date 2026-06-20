import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  Loader2,
  Sparkles,
  Film,
  Mic,
  FileText,
  Image,
  Coins,
} from 'lucide-react';
import { useWizard } from './WizardContainer';
import { createProject } from '../lib/api';

export default function StepReview() {
  const navigate = useNavigate();
  const { state, scenes, setTotalCreditCost } = useWizard();
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const totalDuration = scenes.reduce((sum, s) => sum + (s.duration_seconds || 10), 0);
  const creditCost = Math.max(10, scenes.length * 5 + (totalDuration > 60 ? 5 : 0));

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    setTotalCreditCost(creditCost);

    try {
      const project = await createProject({
        title: state.productName || 'Untitled Project',
        avatar_id: state.avatar?.id,
        voice_id: state.voice?.id,
        voice_speed: state.voiceSpeed,
        voice_pitch: state.voicePitch,
        script_raw: JSON.stringify(state.scriptScenes),
        scenes: scenes.map((s) => ({
          scene_number: s.scene_number,
          section_label: s.section_label,
          text: s.text,
          duration_seconds: s.duration_seconds,
          background_id: state.backgrounds[s.scene_number]?.background?.id,
          transition: state.backgrounds[s.scene_number]?.transition || 'fade',
        })),
      });
      setSubmitted(true);
      setTimeout(() => navigate(`/projects/${project.id}`), 1500);
    } catch (err: any) {
      setError(err?.response?.data?.message || err?.message || 'Failed to create project');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
          <CheckCircle className="h-8 w-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900">Project Created!</h2>
        <p className="mt-1 text-sm text-gray-500">Redirecting to your project...</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">Review & Render</h2>
      <p className="text-sm text-gray-500 mb-6">
        Review your video configuration before submitting for rendering.
      </p>

      {/* Summary cards */}
      <div className="space-y-4 mb-6">
        {/* Avatar */}
        <SummaryCard icon={Film} label="Avatar" value={state.avatar?.name || 'None selected'} />

        {/* Voice */}
        <SummaryCard icon={Mic} label="Voice" value={state.voice?.name || 'None selected'}>
          {state.voice && (
            <div className="flex gap-3 text-xs text-gray-500 mt-1">
              <span>Speed: {state.voiceSpeed}x</span>
              <span>Pitch: {state.voicePitch}</span>
            </div>
          )}
        </SummaryCard>

        {/* Script */}
        <div className="rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="h-4 w-4 text-brand-500" />
            <span className="text-sm font-medium text-gray-700">Script — {scenes.length} scenes</span>
          </div>
          <div className="space-y-2">
            {scenes.map((scene, idx) => (
              <div key={scene.id || idx} className="flex items-start gap-3 text-sm">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-brand-100 text-[10px] font-bold text-brand-700">
                  {scene.scene_number}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-brand-600 font-medium">{scene.section_label}</p>
                  <p className="text-gray-600 truncate">{scene.text}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {state.backgrounds[scene.scene_number]?.background && (
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Image className="h-3 w-3" /> BG
                    </span>
                  )}
                  <span className="text-xs text-gray-400">{scene.duration_seconds}s</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Credits */}
        <SummaryCard icon={Coins} label="Estimated Cost" value={`${creditCost} credits`}>
          <div className="text-xs text-gray-500 mt-1">
            {scenes.length} scenes · {totalDuration}s total duration
          </div>
        </SummaryCard>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="btn-primary w-full text-base py-3"
      >
        {submitting ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Creating Project...
          </>
        ) : (
          <>
            <Sparkles className="h-5 w-5" />
            Create & Submit for Rendering
          </>
        )}
      </button>
    </div>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-200 p-4">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-brand-500" />
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="ml-auto text-sm text-gray-900 font-medium">{value}</span>
      </div>
      {children}
    </div>
  );
}
