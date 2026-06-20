import { useEffect, useState, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack } from 'lucide-react';
import { getVoices, getVoicePreview } from '../lib/api';
import type { Voice } from '../lib/types';
import { useWizard } from './WizardContainer';

export default function StepVoice() {
  const { state, setVoice, setVoiceSpeed, setVoicePitch } = useWizard();
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    getVoices()
      .then(setVoices)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handlePreview = async (voice: Voice) => {
    if (previewId === voice.id && playing) {
      audioRef.current?.pause();
      setPlaying(false);
      return;
    }

    try {
      const url = await getVoicePreview(voice.id);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => setPlaying(false);
      audio.play();
      setPreviewId(voice.id);
      setPlaying(true);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
    };
  }, []);

  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-200" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">Choose a Voice</h2>
      <p className="text-sm text-gray-500 mb-6">
        Pick from our library of AI voices. Preview each voice before selecting.
      </p>

      {/* Speed & Pitch controls */}
      <div className="mb-6 flex flex-wrap gap-6 rounded-xl border border-gray-200 bg-gray-50 p-4">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Speed: {state.voiceSpeed.toFixed(1)}x
          </label>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={state.voiceSpeed}
            onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
            className="w-full accent-brand-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>0.5x</span>
            <span>2.0x</span>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pitch
          </label>
          <div className="flex gap-1">
            {['low', 'normal', 'high'].map((p) => (
              <button
                key={p}
                onClick={() => setVoicePitch(p)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                  state.voicePitch === p
                    ? 'bg-brand-600 text-white'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Voice grid */}
      <div className="grid gap-4 sm:grid-cols-2">
        {voices.map((voice) => {
          const selected = state.voice?.id === voice.id;
          const isPreviewing = previewId === voice.id && playing;
          return (
            <button
              key={voice.id}
              onClick={() => setVoice(voice)}
              className={`flex items-center gap-4 rounded-xl border-2 p-4 text-left transition-all ${
                selected
                  ? 'border-brand-600 bg-brand-50 shadow-sm'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  handlePreview(voice);
                }}
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-colors ${
                  isPreviewing
                    ? 'bg-brand-600 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }`}
              >
                {isPreviewing ? (
                  <Pause className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4 ml-0.5" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{voice.name}</p>
                <p className="text-xs text-gray-500">
                  {voice.accent && `${voice.accent} · `}
                  {voice.gender && `${voice.gender} · `}
                  {voice.category || 'General'}
                </p>
              </div>
              {selected && (
                <div className="h-3 w-3 rounded-full bg-brand-600 shrink-0" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
