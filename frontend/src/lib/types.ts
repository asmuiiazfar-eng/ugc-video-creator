export interface Avatar {
  id: string;
  name: string;
  thumbnail_url: string;
  generated_url?: string;
  preset: boolean;
  created_at?: string;
}

export interface Voice {
  id: string;
  name: string;
  provider: string;
  voice_id: string;
  preview_url?: string;
  category?: string;
  accent?: string;
  gender?: string;
}

export interface Background {
  id: string;
  name: string;
  thumbnail_url: string;
  full_url?: string;
  category: string;
  preset: boolean;
}

export interface ScriptScene {
  scene_number: number;
  section_label: string;
  text: string;
  duration_seconds: number;
}

export interface Scene {
  id: string;
  project_id: string;
  scene_number: number;
  section_label: string;
  text: string;
  duration_seconds: number;
  background_id?: string;
  background_url?: string;
  transition?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Project {
  id: string;
  title: string;
  status: 'draft' | 'generating' | 'ready' | 'rendering' | 'completed' | 'failed';
  avatar_id?: string;
  avatar_url?: string;
  voice_id?: string;
  voice_name?: string;
  script_raw?: string;
  thumbnail_url?: string;
  video_url?: string;
  total_scenes?: number;
  credit_cost?: number;
  created_at: string;
  updated_at?: string;
  scenes?: Scene[];
}

export interface CreditTransaction {
  id: string;
  user_id: string;
  amount: number;
  type: 'purchase' | 'usage' | 'refund' | 'bonus';
  description?: string;
  created_at: string;
}

export interface WizardState {
  step: number;
  avatar: Avatar | null;
  voice: Voice | null;
  voiceSpeed: number;
  voicePitch: string;
  productName: string;
  productDescription: string;
  targetAudience: string;
  tone: string;
  videoDuration: string;
  scriptScenes: ScriptScene[];
  scenes: Scene[];
  backgrounds: Record<string, { background: Background | null; transition: string }>;
  generating: boolean;
  totalCreditCost: number;
}
