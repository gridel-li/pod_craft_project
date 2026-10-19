/**
 * Shared TypeScript interfaces for the PodCraft app.
 */

export interface User {
  id: string;
  username: string;
  email: string;
  credits: number;
  plan: string;
  is_admin?: boolean;
}

export interface TaskSegment {
  type: string;
  content: string;
  duration_sec: number;
}

export interface Task {
  // interface 只在 TypeScript 编译阶段存在；运行时仍要依靠后端 Pydantic 校验 API 数据。
  id: string;
  topic: string;
  mood: string;
  style: string;
  status: string;
  progress: number;
  current_step: string;
  title: string;
  audio_path: string;
  duration_sec: number;
  segments: TaskSegment[];
  error_message: string;
  created_at: string;
}
