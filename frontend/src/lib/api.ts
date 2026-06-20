import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { supabase } from './supabase';
import type {
  Avatar,
  Voice,
  Background,
  ScriptScene,
  Scene,
  Project,
  CreditTransaction,
} from './types';

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const { data: session } = await supabase.auth.getSession();
  const token = session?.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ─── Avatar ─────────────────────────────────────────────────── */

export async function getAvatars(): Promise<Avatar[]> {
  const { data } = await api.get<Avatar[]>('/avatars');
  return data;
}

export async function uploadAvatar(file: File): Promise<{ file_id: string }> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<{ file_id: string }>('/avatars/upload', form);
  return data;
}

export async function generateAvatar(fileId: string): Promise<Avatar> {
  const { data } = await api.post<Avatar>(`/avatars/generate`, { file_id: fileId });
  return data;
}

/* ─── Voices ─────────────────────────────────────────────────── */

export async function getVoices(): Promise<Voice[]> {
  const { data } = await api.get<Voice[]>('/voices');
  return data;
}

export async function getVoicePreview(id: string): Promise<string> {
  const { data } = await api.get<{ preview_url: string }>(`/voices/${id}/preview`);
  return data.preview_url;
}

/* ─── Script ─────────────────────────────────────────────────── */

export async function generateScript(payload: {
  product_name: string;
  product_description: string;
  target_audience: string;
  tone: string;
  duration: string;
}): Promise<ScriptScene[]> {
  const { data } = await api.post<ScriptScene[]>('/scripts/generate', payload);
  return data;
}

export async function splitScript(text: string): Promise<ScriptScene[]> {
  const { data } = await api.post<ScriptScene[]>('/scripts/split', { text });
  return data;
}

/* ─── Backgrounds ────────────────────────────────────────────── */

export async function getBackgrounds(category?: string): Promise<Background[]> {
  const params = category ? { category } : {};
  const { data } = await api.get<Background[]>('/backgrounds', { params });
  return data;
}

export async function generateBackground(prompt: {
  location: string;
  mood: string;
}): Promise<Background> {
  const { data } = await api.post<Background>('/backgrounds/generate', prompt);
  return data;
}

/* ─── Projects ───────────────────────────────────────────────── */

export async function createProject(payload: {
  title: string;
  avatar_id?: string;
  voice_id?: string;
  voice_speed?: number;
  voice_pitch?: string;
  script_raw?: string;
  scenes?: Partial<Scene>[];
}): Promise<Project> {
  const { data } = await api.post<Project>('/projects', payload);
  return data;
}

export async function getProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/projects');
  return data;
}

export async function getProject(id: string): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${id}`);
  return data;
}

/* ─── Scenes ─────────────────────────────────────────────────── */

export async function createScene(
  projectId: string,
  payload: Partial<Scene>
): Promise<Scene> {
  const { data } = await api.post<Scene>(`/projects/${projectId}/scenes`, payload);
  return data;
}

export async function updateScene(id: string, payload: Partial<Scene>): Promise<Scene> {
  const { data } = await api.put<Scene>(`/scenes/${id}`, payload);
  return data;
}

export async function deleteScene(id: string): Promise<void> {
  await api.delete(`/scenes/${id}`);
}

/* ─── Render ─────────────────────────────────────────────────── */

export async function submitRender(projectId: string): Promise<{ render_id: string }> {
  const { data } = await api.post<{ render_id: string }>(`/projects/${projectId}/render`);
  return data;
}

/* ─── Credits ────────────────────────────────────────────────── */

export async function getCredits(): Promise<{ balance: number }> {
  const { data } = await api.get<{ balance: number }>('/credits');
  return data;
}

export async function getCreditHistory(): Promise<CreditTransaction[]> {
  const { data } = await api.get<CreditTransaction[]>('/credits/history');
  return data;
}

export async function createCheckout(plan: string): Promise<{ url: string }> {
  const { data } = await api.post<{ url: string }>('/credits/checkout', { plan });
  return data;
}

export default api;
