import { useState, useRef } from 'react';
import {
  GripVertical,
  Plus,
  Trash2,
  SplitSquareVertical,
  Combine,
  Edit3,
  ChevronUp,
  ChevronDown,
  AlertCircle,
} from 'lucide-react';
import { useWizard } from './WizardContainer';
import type { Scene } from '../lib/types';

let tempIdCounter = 999;

function makeTempScene(num: number, text = ''): Scene {
  tempIdCounter += 1;
  return {
    id: `temp-${tempIdCounter}`,
    project_id: '',
    scene_number: num,
    section_label: `Scene ${num}`,
    text: text || `[Scene ${num} text]`,
    duration_seconds: 10,
  };
}

export default function StepScenes() {
  const { state, setScenes } = useWizard();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [dragIdx, setDragIdx] = useState<number | null>(null);
  const dragOverIdx = useRef<number | null>(null);

  // Convert scriptScenes to Scene[] on first view
  const scenes = state.scenes.length > 0
    ? state.scenes
    : state.scriptScenes.map((s, i) => ({
        id: `scene-${i + 1}`,
        project_id: '',
        scene_number: i + 1,
        section_label: s.section_label,
        text: s.text,
        duration_seconds: s.duration_seconds,
      }));

  const updateScenes = (list: Scene[]) => {
    const renumbered = list.map((s, i) => ({ ...s, scene_number: i + 1 }));
    setScenes(renumbered);
  };

  const handleEdit = (scene: Scene) => {
    setEditingId(scene.id);
    setEditText(scene.text);
  };

  const saveEdit = () => {
    if (!editingId) return;
    const updated = scenes.map((s) =>
      s.id === editingId ? { ...s, text: editText } : s
    );
    updateScenes(updated);
    setEditingId(null);
  };

  const handleSplit = (scene: Scene) => {
    const idx = scenes.findIndex((s) => s.id === scene.id);
    if (idx === -1) return;
    const half = Math.ceil(scene.text.length / 2);
    const part1 = scene.text.slice(0, half).trim();
    const part2 = scene.text.slice(half).trim();

    const before = scenes.slice(0, idx);
    const after = scenes.slice(idx + 1);
    const newList = [
      ...before,
      { ...scene, text: part1, section_label: `${scene.section_label} (1)` },
      { ...scene, id: `temp-${Date.now()}`, text: part2 || '[text]', section_label: `${scene.section_label} (2)` },
      ...after,
    ];
    updateScenes(newList);
  };

  const handleMergeDown = (scene: Scene) => {
    const idx = scenes.findIndex((s) => s.id === scene.id);
    if (idx === -1 || idx >= scenes.length - 1) return;
    const next = scenes[idx + 1];
    const merged = {
      ...scene,
      text: scene.text + ' ' + next.text,
      duration_seconds: scene.duration_seconds + next.duration_seconds,
    };
    const newList = [...scenes.slice(0, idx), merged, ...scenes.slice(idx + 2)];
    updateScenes(newList);
  };

  const handleAddBefore = (scene: Scene) => {
    const idx = scenes.findIndex((s) => s.id === scene.id);
    if (idx === -1) return;
    const newList = [...scenes.slice(0, idx), makeTempScene(0), ...scenes.slice(idx)];
    updateScenes(newList);
  };

  const handleAddAfter = (scene: Scene) => {
    const idx = scenes.findIndex((s) => s.id === scene.id);
    if (idx === -1) return;
    const newList = [...scenes.slice(0, idx + 1), makeTempScene(0), ...scenes.slice(idx + 1)];
    updateScenes(newList);
  };

  const handleDelete = (scene: Scene) => {
    if (scenes.length <= 3) return;
    const newList = scenes.filter((s) => s.id !== scene.id);
    updateScenes(newList);
  };

  const handleAddEnd = () => {
    if (scenes.length >= 10) return;
    updateScenes([...scenes, makeTempScene(scenes.length + 1)]);
  };

  /* ── Drag & Drop (state-based) ────────────────────────── */
  const handleDragStart = (idx: number) => {
    setDragIdx(idx);
  };

  const handleDragOver = (e: React.DragEvent, idx: number) => {
    e.preventDefault();
    dragOverIdx.current = idx;
  };

  const handleDrop = () => {
    if (dragIdx === null || dragOverIdx.current === null || dragIdx === dragOverIdx.current) {
      setDragIdx(null);
      dragOverIdx.current = null;
      return;
    }
    const list = [...scenes];
    const [moved] = list.splice(dragIdx, 1);
    list.splice(dragOverIdx.current, 0, moved);
    updateScenes(list);
    setDragIdx(null);
    dragOverIdx.current = null;
  };

  const valid = scenes.length >= 3 && scenes.length <= 10;

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">Edit Scenes</h2>
      <p className="text-sm text-gray-500 mb-6">
        Reorder, split, merge, or edit scene text. Min 3, max 10 scenes.
      </p>

      {/* Validation */}
      {!valid && (
        <div className={`mb-4 flex items-center gap-2 rounded-lg px-4 py-2 text-sm ${
          scenes.length < 3 ? 'bg-red-50 text-red-600' : 'bg-yellow-50 text-yellow-700'
        }`}>
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>
            {scenes.length < 3
              ? `Need at least 3 scenes (${scenes.length} selected)`
              : `Maximum 10 scenes (${scenes.length} selected)`}
          </span>
        </div>
      )}

      {/* Scene list */}
      <div className="space-y-3">
        {scenes.map((scene, idx) => {
          const isEditing = editingId === scene.id;
          const isDragging = dragIdx === idx;
          return (
            <div
              key={scene.id}
              draggable
              onDragStart={() => handleDragStart(idx)}
              onDragOver={(e) => handleDragOver(e, idx)}
              onDrop={handleDrop}
              onDragEnd={() => { setDragIdx(null); dragOverIdx.current = null; }}
              className={`rounded-xl border-2 p-4 transition-all ${
                isDragging
                  ? 'border-brand-400 bg-brand-50 opacity-60 shadow-md'
                  : isEditing
                  ? 'border-brand-300 bg-white shadow-sm'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Drag handle */}
                <div className="drag-handle mt-1 text-gray-300 hover:text-gray-500 transition-colors">
                  <GripVertical className="h-5 w-5" />
                </div>

                {/* Number badge */}
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
                  {scene.scene_number}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-brand-600 uppercase tracking-wide">
                      {scene.section_label}
                    </span>
                    <span className="text-xs text-gray-400">{scene.duration_seconds}s</span>
                  </div>

                  {isEditing ? (
                    <div className="space-y-2">
                      <textarea
                        rows={3}
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="input-field resize-none text-sm"
                        autoFocus
                      />
                      <div className="flex gap-2">
                        <button onClick={saveEdit} className="btn-primary text-xs !py-1.5 !px-3">
                          Save
                        </button>
                        <button onClick={() => setEditingId(null)} className="btn-secondary text-xs !py-1.5 !px-3">
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-700">{scene.text}</p>
                  )}
                </div>

                {/* Actions */}
                {!isEditing && (
                  <div className="flex shrink-0 flex-wrap gap-1">
                    <ActionBtn icon={Edit3} label="Edit" onClick={() => handleEdit(scene)} />
                    <ActionBtn icon={SplitSquareVertical} label="Split" onClick={() => handleSplit(scene)} />
                    <ActionBtn
                      icon={Combine}
                      label="Merge"
                      onClick={() => handleMergeDown(scene)}
                      disabled={idx >= scenes.length - 1}
                    />
                    <ActionBtn icon={Plus} label="Before" onClick={() => handleAddBefore(scene)} />
                    <ActionBtn icon={Plus} label="After" onClick={() => handleAddAfter(scene)} />
                    <ActionBtn
                      icon={Trash2}
                      label="Del"
                      onClick={() => handleDelete(scene)}
                      disabled={scenes.length <= 3}
                      danger
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add scene button */}
      {scenes.length < 10 && (
        <button onClick={handleAddEnd} className="btn-secondary mt-4 w-full">
          <Plus className="h-4 w-4" />
          Add Scene to End
        </button>
      )}
    </div>
  );
}

function ActionBtn({
  icon: Icon,
  label,
  onClick,
  disabled,
  danger,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={label}
      className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-30 ${
        danger
          ? 'text-red-600 hover:bg-red-50'
          : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
      }`}
    >
      <Icon className="h-3 w-3" />
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
}
