import { createContext, useContext, useState, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ArrowLeft, ArrowRight, Sparkles } from 'lucide-react';
import type { WizardState, Avatar, Voice, ScriptScene, Scene, Background } from '../lib/types';
import StepAvatar from './StepAvatar';
import StepVoice from './StepVoice';
import StepScript from './StepScript';
import StepScenes from './StepScenes';
import StepBackground from './StepBackground';
import StepReview from './StepReview';

/* ─── Context ────────────────────────────────────────────── */

interface WizardContextValue {
  state: WizardState;
  scenes: Scene[];
  scriptScenes: ScriptScene[];
  setStep: (s: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  setAvatar: (a: Avatar | null) => void;
  setVoice: (v: Voice | null) => void;
  setVoiceSpeed: (s: number) => void;
  setVoicePitch: (p: string) => void;
  setProductName: (n: string) => void;
  setProductDescription: (d: string) => void;
  setTargetAudience: (a: string) => void;
  setTone: (t: string) => void;
  setVideoDuration: (d: string) => void;
  setScriptScenes: (s: ScriptScene[]) => void;
  setScenes: (s: Scene[]) => void;
  setBackground: (num: number, bg: Background | null, transition?: string) => void;
  setGenerating: (g: boolean) => void;
  setTotalCreditCost: (c: number) => void;
}

const defaultWizard: WizardState = {
  step: 0,
  avatar: null,
  voice: null,
  voiceSpeed: 1.0,
  voicePitch: 'normal',
  productName: '',
  productDescription: '',
  targetAudience: 'general',
  tone: 'professional',
  videoDuration: '30-60',
  scriptScenes: [],
  scenes: [],
  backgrounds: {},
  generating: false,
  totalCreditCost: 0,
};

const WizardContext = createContext<WizardContextValue>(null!);

export function useWizard() {
  return useContext(WizardContext);
}

/* ─── Steps config ───────────────────────────────────────── */

const STEPS = [
  { label: 'Avatar', icon: '🤖' },
  { label: 'Voice', icon: '🎤' },
  { label: 'Script', icon: '📝' },
  { label: 'Scenes', icon: '🎬' },
  { label: 'Background', icon: '🏞️' },
  { label: 'Review', icon: '✅' },
];

const STEP_COMPONENTS = [
  StepAvatar,
  StepVoice,
  StepScript,
  StepScenes,
  StepBackground,
  StepReview,
];

/* ─── Container ──────────────────────────────────────────── */

export default function WizardContainer() {
  const navigate = useNavigate();
  const [state, setState] = useState<WizardState>({ ...defaultWizard });

  const patch = (partial: Partial<WizardState>) =>
    setState((prev) => ({ ...prev, ...partial }));

  const ctx: WizardContextValue = {
    state,
    scenes: state.scenes.length > 0 ? state.scenes : state.scriptScenes.map((s, i) => ({
      id: `scene-${i + 1}`,
      project_id: '',
      scene_number: i + 1,
      section_label: s.section_label,
      text: s.text,
      duration_seconds: s.duration_seconds,
    })),
    scriptScenes: state.scriptScenes,
    setStep: (step) => patch({ step }),
    nextStep: () => patch({ step: Math.min(state.step + 1, 5) }),
    prevStep: () => patch({ step: Math.max(state.step - 1, 0) }),
    setAvatar: (a) => patch({ avatar: a }),
    setVoice: (v) => patch({ voice: v }),
    setVoiceSpeed: (s) => patch({ voiceSpeed: s }),
    setVoicePitch: (p) => patch({ voicePitch: p }),
    setProductName: (n) => patch({ productName: n }),
    setProductDescription: (d) => patch({ productDescription: d }),
    setTargetAudience: (a) => patch({ targetAudience: a }),
    setTone: (t) => patch({ tone: t }),
    setVideoDuration: (d) => patch({ videoDuration: d }),
    setScriptScenes: (s) => patch({ scriptScenes: s }),
    setScenes: (s) => patch({ scenes: s }),
    setBackground: (num, bg, transition) =>
      patch({
        backgrounds: {
          ...state.backgrounds,
          [num]: { background: bg, transition: transition || state.backgrounds[num]?.transition || 'fade' },
        },
      }),
    setGenerating: (g) => patch({ generating: g }),
    setTotalCreditCost: (c) => patch({ totalCreditCost: c }),
  };

  const StepComponent = STEP_COMPONENTS[state.step];

  const canNext = (): boolean => {
    switch (state.step) {
      case 0: return !!state.avatar;
      case 1: return !!state.voice;
      case 2: return state.scriptScenes.length > 0;
      case 3: return state.scenes.length >= 3 && state.scenes.length <= 10;
      case 4: return Object.keys(state.backgrounds).length >= state.scenes.length;
      case 5: return true;
      default: return false;
    }
  };

  return (
    <WizardContext.Provider value={ctx}>
      <div className="mx-auto max-w-4xl">
        {/* Close / Exit */}
        <button
          onClick={() => navigate('/')}
          className="mb-4 text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          ← Exit wizard
        </button>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((s, i) => (
              <div key={s.label} className="flex items-center">
                <div
                  onClick={() => i < state.step && ctx.setStep(i)}
                  className={`flex items-center gap-1.5 text-xs font-medium transition-colors ${
                    i <= state.step
                      ? 'text-brand-600 cursor-pointer'
                      : 'text-gray-300 cursor-default'
                  }`}
                >
                  <div
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-all ${
                      i < state.step
                        ? 'bg-brand-600 text-white'
                        : i === state.step
                        ? 'border-2 border-brand-600 bg-white text-brand-600'
                        : 'border-2 border-gray-200 bg-white text-gray-300'
                    }`}
                  >
                    {i < state.step ? <Check className="h-3.5 w-3.5" /> : i + 1}
                  </div>
                  <span className="hidden sm:inline">{s.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    className={`mx-2 h-px w-8 sm:w-12 transition-colors ${
                      i < state.step ? 'bg-brand-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step content */}
        <div className="card min-h-[400px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={state.step}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
            >
              <StepComponent />
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={ctx.prevStep}
            disabled={state.step === 0}
            className="btn-secondary"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>

          {state.step < 5 ? (
            <button
              onClick={ctx.nextStep}
              disabled={!canNext()}
              className="btn-primary"
            >
              Next
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              disabled={!canNext()}
              className="btn-primary"
            >
              <Sparkles className="h-4 w-4" />
              Render Video
            </button>
          )}
        </div>
      </div>
    </WizardContext.Provider>
  );
}
