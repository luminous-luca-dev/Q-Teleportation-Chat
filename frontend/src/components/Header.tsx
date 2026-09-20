'use client';

import React from 'react';
import { User, Room } from '@/lib/api';
import { Atom, UserCheck, Shield, Shuffle } from 'lucide-react';

interface HeaderProps {
  users: User[];
  currentUser: User | null;
  currentRoom: Room | null;
  onSwitchUser: (user: User) => void;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  users,
  currentUser,
  currentRoom,
  onSwitchUser,
  isConnected,
}) => {
  return (
    <header className="bg-slate-950/90 border-b border-cyan-500/30 px-6 py-3 font-mono flex items-center justify-between">
      {/* ロゴ & タイトル */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <Atom className="w-8 h-8 text-cyan-400 animate-spin" style={{ animationDuration: '10s' }} />
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
          </span>
        </div>
        <div>
          <h1 className="text-base font-bold text-white tracking-widest flex items-center gap-2">
            <span className="text-cyan-400 glow-text-cyan">QUANTUM TELEPORTATION</span>
            <span className="text-slate-400 text-xs font-normal">| DECK v1.0</span>
          </h1>
          <p className="text-[10px] text-slate-400">
            Qiskit Aer Quantum Circuit Simulator • Entanglement Communication Protocol
          </p>
        </div>
      </div>

      {/* ステータス & ユーザー切替 */}
      <div className="flex items-center gap-4 text-xs">
        {/* WebSocket 接続インジケーター */}
        <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className="text-slate-300">
            WS: {isConnected ? 'LINKED (8000)' : 'OFFLINE'}
          </span>
        </div>

        {/* ルーム情報 */}
        <div className="bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-slate-400">ROOM:</span>
          <span className="text-purple-300 font-bold">{currentRoom?.room_id ?? 'INIT'}</span>
        </div>

        {/* ユーザー切替 */}
        <div className="flex items-center gap-2 bg-slate-900/80 border border-cyan-500/40 px-3 py-1.5 rounded">
          <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">OPERATOR:</span>
          <span className="text-cyan-300 font-bold">{currentUser?.name ?? '---'}</span>

          {users.length > 1 && (
            <button
              type="button"
              onClick={() => {
                const nextUser = users.find((u) => u.user_id !== currentUser?.user_id) || users[0];
                onSwitchUser(nextUser);
              }}
              title="ユーザー切替 (Alice ↔ Bob)"
              className="ml-2 bg-cyan-950 hover:bg-cyan-900 text-cyan-400 p-1 rounded border border-cyan-500/30 transition-all cursor-pointer"
            >
              <Shuffle className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
