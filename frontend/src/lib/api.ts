import { QuantumStateStep, TeleportSummary } from './types';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const WS_BASE = (
  process.env.NEXT_PUBLIC_WS_URL ||
  API_BASE.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')
).replace(/\/$/, '');

export interface User {
  user_id: string;
  name: string;
  created_at: number;
}

export interface Room {
  room_id: string;
  member_ids: string[];
  created_at: number;
  message_count: number;
}

export interface ChatMessage {
  message_id: string;
  room_id: string;
  sender_id: string;
  text: string;
  mode: 'instant' | 'slow';
  created_at: number;
  teleport_result?: TeleportSummary;
}

export async function fetchUsers(): Promise<User[]> {
  const res = await fetch(`${API_BASE}/api/users`);
  if (!res.ok) throw new Error('Failed to fetch users');
  const data = await res.json();
  return data.users;
}

export async function createUser(name: string): Promise<User> {
  const res = await fetch(`${API_BASE}/api/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error('Failed to create user');
  return res.json();
}

export async function fetchRooms(userId?: string): Promise<Room[]> {
  const url = userId ? `${API_BASE}/api/rooms?user_id=${userId}` : `${API_BASE}/api/rooms`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch rooms');
  const data = await res.json();
  return data.rooms;
}

export async function createRoom(memberIds: string[]): Promise<Room> {
  const res = await fetch(`${API_BASE}/api/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ member_ids: memberIds }),
  });
  if (!res.ok) throw new Error('Failed to create room');
  return res.json();
}

export async function fetchMessages(roomId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE}/api/rooms/${roomId}/messages`);
  if (!res.ok) throw new Error('Failed to fetch messages');
  const data = await res.json();
  return data.messages;
}

export async function sendInstantMessage(roomId: string, senderId: string, text: string) {
  const res = await fetch(`${API_BASE}/api/rooms/${roomId}/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sender_id: senderId, text }),
  });
  if (!res.ok) throw new Error('Failed to send message');
  return res.json();
}

export function getWebSocketUrl(roomId: string, userId: string): string {
  return `${WS_BASE}/ws/${roomId}/${userId}`;
}

