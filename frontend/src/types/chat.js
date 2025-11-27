// Type definitions for chat application

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Message type
export const MessageRole = {
  USER: 'user',
  ASSISTANT: 'assistant'
};

// Helper to safely parse dates
const parseDate = (dateValue) => {
  if (dateValue instanceof Date) return dateValue;
  if (typeof dateValue === 'string') return new Date(dateValue);
  return new Date();
};

// Session summary (for list view)
export const createSessionSummary = (data) => ({
  id: data.id,
  createdAt: parseDate(data.createdAt)
});

// Full session with messages
export const createSession = (data) => ({
  id: data.id,
  createdAt: parseDate(data.createdAt),
  messages: data.messages.map(msg => ({
    id: msg.id,
    role: msg.role,
    content: msg.content,
    createdAt: parseDate(msg.createdAt)
  }))
});

// Message
export const createMessage = (data) => ({
  id: data.id,
  role: data.role,
  content: data.content,
  createdAt: parseDate(data.createdAt)
});

