import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  RefreshCw,
  Play,
  Pause,
  List,
  Film,
  Loader2,
} from 'lucide-react';
import { getProject, submitRender } from '../lib/api';
import type { Project } from '../lib/types';
import LoadingSkeleton from '../components/LoadingSkeleton';

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [rendering, setRendering] = useState(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!id) return;
    getProject(id)
      .then(setProject)
      .catch(() => navigate('/'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleRender = async () => {
    if (!id) return;
    setRendering(true);
    try {
      await submitRender(id);
      const updated = await getProject(id);
      setProject(updated);
    } catch {
      // ignore
    } finally {
      setRendering(false);
    }
  };

  if (loading) {
    return (
      <div>
        <div className="h-8 w-48 rounded bg-gray-200 animate-pulse mb-6" />
        <LoadingSkeleton type="card" />
      </div>
    );
  }

  if (!project) return null;

  const statusColors: Record<string, string> = {
    draft: 'badge-gray',
    generating: 'badge-yellow',
    ready: 'badge-blue',
    rendering: 'badge-yellow',
    completed: 'badge-green',
    failed: 'badge-red',
  };

  return (
    <div>
      {/* Back */}
      <Link
        to="/"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to projects
      </Link>

      {/* Title row */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
            <span className={statusColors[project.status] || 'badge-gray'}>
              {project.status}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Created {new Date(project.created_at).toLocaleDateString()}
            {project.credit_cost !== undefined && ` · ${project.credit_cost} credits used`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {project.video_url && (
            <a
              href={project.video_url}
              download
              className="btn-secondary"
            >
              <Download className="h-4 w-4" />
              Download
            </a>
          )}
          <button
            onClick={handleRender}
            disabled={rendering || project.status === 'rendering'}
            className="btn-primary"
          >
            {rendering ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {project.status === 'completed' ? 'Re-render' : 'Render'}
          </button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-5">
        {/* Preview */}
        <div className="lg:col-span-3">
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Film className="h-4 w-4" />
              Preview
            </h2>
            <div className="relative aspect-video overflow-hidden rounded-lg bg-gray-900">
              {project.video_url ? (
                <>
                  <video
                    src={project.video_url}
                    className="h-full w-full object-contain"
                    controls={false}
                  />
                  <button
                    onClick={() => setPlaying(!playing)}
                    className="absolute inset-0 flex items-center justify-center bg-black/20 transition-colors hover:bg-black/30"
                  >
                    {playing ? (
                      <Pause className="h-12 w-12 text-white" />
                    ) : (
                      <Play className="h-12 w-12 text-white" />
                    )}
                  </button>
                </>
              ) : (
                <div className="flex h-full flex-col items-center justify-center text-gray-400">
                  <Film className="h-12 w-12 mb-2" />
                  <p className="text-sm">No preview available</p>
                  <p className="text-xs">Render the project first</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Scene list */}
        <div className="lg:col-span-2">
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <List className="h-4 w-4" />
              Scenes ({project.scenes?.length || 0})
            </h2>
            {project.scenes && project.scenes.length > 0 ? (
              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                {project.scenes.map((scene) => (
                  <div
                    key={scene.id}
                    className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-700">
                        Scene {scene.scene_number}
                      </span>
                      <span className="text-xs text-gray-400">
                        {scene.duration_seconds}s
                      </span>
                    </div>
                    {scene.section_label && (
                      <p className="text-xs text-brand-600 font-medium mb-0.5">
                        {scene.section_label}
                      </p>
                    )}
                    <p className="text-gray-600 line-clamp-2">{scene.text}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No scenes yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
