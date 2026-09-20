// Shared types used across components

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}
