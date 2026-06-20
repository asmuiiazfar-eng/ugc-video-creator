import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Video, Clock, FileText, AlertCircle } from 'lucide-react';
import { getProjects } from '../lib/api';
import type { Project } from '../lib/types';
import LoadingSkeleton from '../components/LoadingSkeleton';

const statusConfig: Record<string, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'badge-gray' },
  generating: { label: 'Generating', className: 'badge-yellow' },
  ready: { label: 'Ready', className: 'badge-blue' },
  rendering: { label: 'Rendering', className: 'badge-yellow' },
  completed: { label: 'Completed', className: 'badge-green' },
  failed: { label: 'Failed', className: 'badge-red' },
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Projects</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your UGC video projects
          </p>
        </div>
        <Link to="/create" className="btn-primary">
          <Plus className="h-4 w-4" />
          Create New
        </Link>
      </div>

      {/* Loading */}
      {loading && <LoadingSkeleton type="card" count={6} />}

      {/* Empty state */}
      {!loading && projects.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-300 py-20 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gray-100">
            <Video className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">No projects yet</h3>
          <p className="mt-1 max-w-sm text-sm text-gray-500">
            Create your first UGC video and bring your ideas to life with AI.
          </p>
          <Link to="/create" className="btn-primary mt-6">
            <Plus className="h-4 w-4" />
            Create Your First Video
          </Link>
        </div>
      )}

      {/* Project grid */}
      {!loading && projects.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => {
            const status = statusConfig[project.status] || statusConfig.draft;
            return (
              <button
                key={project.id}
                onClick={() => navigate(`/projects/${project.id}`)}
                className="card group cursor-pointer text-left transition-all hover:shadow-md hover:border-brand-200"
              >
                {/* Thumbnail */}
                <div className="relative mb-4 h-40 overflow-hidden rounded-lg bg-gray-100">
                  {project.thumbnail_url ? (
                    <img
                      src={project.thumbnail_url}
                      alt={project.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <Video className="h-10 w-10 text-gray-300" />
                    </div>
                  )}
                  <div className="absolute right-2 top-2">
                    <span className={status.className}>{status.label}</span>
                  </div>
                </div>

                {/* Info */}
                <h3 className="font-semibold text-gray-900 group-hover:text-brand-600 transition-colors truncate">
                  {project.title}
                </h3>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                  {project.total_scenes !== undefined && (
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      {project.total_scenes} scenes
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
