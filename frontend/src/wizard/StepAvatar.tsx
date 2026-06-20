import { useEffect, useState, useRef } from 'react';
import { Upload, Loader2, Check, ImagePlus } from 'lucide-react';
import { getAvatars, uploadAvatar, generateAvatar } from '../lib/api';
import type { Avatar } from '../lib/types';
import { useWizard } from './WizardContainer';

export default function StepAvatar() {
  const { state, setAvatar } = useWizard();
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getAvatars()
      .then(setAvatars)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { file_id } = await uploadAvatar(file);
      setGenerating(true);
      const avatar = await generateAvatar(file_id);
      setAvatar(avatar);
      setGenerating(false);
      setAvatars((prev) => [avatar, ...prev]);
    } catch {
      // ignore
    } finally {
      setUploading(false);
      setGenerating(false);
    }
  };

  const presets = avatars.filter((a) => a.preset);
  const customAvatars = avatars.filter((a) => !a.preset);

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">Choose Your Avatar</h2>
      <p className="text-sm text-gray-500 mb-6">
        Select a preset avatar or upload your own photo to generate a custom one.
      </p>

      {/* Upload area */}
      <div className="mb-8">
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleUpload}
        />
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading || generating}
          className="flex w-full items-center justify-center gap-3 rounded-xl border-2 border-dashed border-gray-300 px-6 py-5 text-sm text-gray-500 transition-colors hover:border-brand-400 hover:text-brand-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {uploading || generating ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin text-brand-500" />
              <span>{uploading ? 'Uploading...' : 'Generating avatar...'}</span>
            </>
          ) : (
            <>
              <ImagePlus className="h-5 w-5" />
              <span>Upload a photo to generate your avatar</span>
            </>
          )}
        </button>
      </div>

      {/* Presets */}
      {loading ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="aspect-square animate-pulse rounded-xl bg-gray-200" />
          ))}
        </div>
      ) : (
        <>
          {customAvatars.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Your Avatars</h3>
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-4">
                {customAvatars.map((a) => (
                  <AvatarCard
                    key={a.id}
                    avatar={a}
                    selected={state.avatar?.id === a.id}
                    onSelect={setAvatar}
                  />
                ))}
              </div>
            </div>
          )}

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Preset Avatars</h3>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-4">
              {presets.map((a) => (
                <AvatarCard
                  key={a.id}
                  avatar={a}
                  selected={state.avatar?.id === a.id}
                  onSelect={setAvatar}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function AvatarCard({
  avatar,
  selected,
  onSelect,
}: {
  avatar: Avatar;
  selected: boolean;
  onSelect: (a: Avatar) => void;
}) {
  return (
    <button
      onClick={() => onSelect(avatar)}
      className={`relative aspect-square overflow-hidden rounded-xl border-2 transition-all ${
        selected
          ? 'border-brand-600 ring-2 ring-brand-200 shadow-md scale-105'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
      }`}
    >
      <img
        src={avatar.thumbnail_url || avatar.generated_url}
        alt={avatar.name}
        className="h-full w-full object-cover"
      />
      {selected && (
        <div className="absolute inset-0 flex items-center justify-center bg-brand-600/20">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white shadow">
            <Check className="h-4 w-4" />
          </div>
        </div>
      )}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
        <p className="text-xs font-medium text-white truncate">{avatar.name}</p>
      </div>
    </button>
  );
}
