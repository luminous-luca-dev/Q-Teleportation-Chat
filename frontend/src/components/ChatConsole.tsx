'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, User } from '@/lib/api';
import { Send, Terminal, Sparkles } from 'lucide-react';

interface ChatConsoleProps {
  currentUser: User | null;
  messages: ChatMessage[];
  onSendMessage: (text: string, mode: 'instant' | 'slow') => void;
  isStreaming: boolean;
}

export const ChatConsole: React.FC<ChatConsoleProps> = ({
  currentUser,
  messages,
  onSendMessage,
  isStreaming,
}) => {
  const [inputText, setInputText] = useState('');
  const [mode, setMode] = useState<'instant' | 'slow'>('slow');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText.trim(), mode);
    setInputText('');
  };

  return (
    <div className="bg-slate-950/80 border border-cyan-500/30 rounded-lg p-4 font-mono flex flex-col h-full">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-cyan-500/20">
        <span className="text-cyan-300 font-bold text-sm tracking-wider flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          QUANTUM MESSAGING CONSOLE
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setMode('slow')}
            className={`px-2 py-0.5 rounded text-[11px] transition-all ${
              mode === 'slow'
                ? 'bg-cyan-500 text-black font-bold shadow-[0_0_8px_rgba(0,240,255,0.7)]'
                : 'bg-slate-900 text-slate-400 border border-slate-800'
            }`}
          >
            ゆっくり可視化
          </button>
          <button
            type="button"
            onClick={() => setMode('instant')}
            className={`px-2 py-0.5 rounded text-[11px] transition-all ${
              mode === 'instant'
                ? 'bg-purple-500 text-white font-bold shadow-[0_0_8px_rgba(168,85,247,0.7)]'
                : 'bg-slate-900 text-slate-400 border border-slate-800'
            }`}
          >
            瞬時送信
          </button>
        </div>
      </div>

      {/* メッセージログ一覧 */}
      <div className="flex-1 overflow-y-auto space-y-3 p-2 bg-slate-900/30 rounded border border-slate-800/80">
        {messages.length === 0 ? (
          <div className="text-center text-slate-400 text-xs py-8">
            メッセージはありません。メッセージを入力して量子テレポーテーションを実行してください。
          </div>
        ) : (
          messages.map((m) => {
            const isMe = m.sender_id === currentUser?.user_id;
            return (
              <div
                key={m.message_id}
                className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center gap-1 text-[10px] text-slate-400 mb-0.5">
                  <span className={isMe ? 'text-cyan-400' : 'text-green-400'}>
                    {isMe ? 'YOU (Alice)' : 'PEER (Bob)'}
                  </span>
                  <span>•</span>
                  <span>
                    {m.created_at
                      ? new Date(
                          typeof m.created_at === 'number'
                            ? m.created_at > 1e11
                              ? m.created_at
                              : m.created_at * 1000
                            : m.created_at
                        ).toLocaleTimeString()
                      : '--:--:--'}
                  </span>
                  <span className="text-purple-400 text-[9px] bg-purple-950/60 px-1 rounded border border-purple-800">
                    {m.mode}
                  </span>
                </div>
                <div
                  className={`p-2.5 rounded-lg max-w-[85%] text-xs border ${
                    isMe
                      ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-100'
                      : 'bg-slate-900/80 border-slate-700 text-slate-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap">
                    {m.text || (m as unknown as { recovered_text?: string })?.recovered_text || (m as unknown as { original_text?: string })?.original_text || '---'}
                  </p>
                  {m.teleport_result && (
                    <div className="mt-1 pt-1 border-t border-cyan-500/20 text-[10px] text-cyan-400 flex items-center gap-2">
                      <Sparkles className="w-3 h-3" />
                      <span>
                        Teleported: {m.teleport_result.total_bits} bits (Fidelity:{' '}
                        {(m.teleport_result.success_rate * 100).toFixed(0)}%)
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 送信フォーム */}
      <form onSubmit={handleSend} className="mt-3 flex gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={isStreaming ? '量子状態を転送中...' : '量子暗号化メッセージを入力...'}
          disabled={isStreaming}
          className="flex-1 bg-slate-900/80 border border-slate-700 focus:border-cyan-400 focus:outline-none rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-400"
        />
        <button
          type="submit"
          disabled={isStreaming || !inputText.trim()}
          className="bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-800 disabled:text-slate-400 text-black font-bold px-4 py-2 rounded text-xs flex items-center gap-1.5 transition-all shadow-[0_0_10px_rgba(0,240,255,0.4)] disabled:shadow-none cursor-pointer disabled:cursor-not-allowed"
        >
          <Send className="w-3.5 h-3.5" />
          <span>送信</span>
        </button>
      </form>
    </div>
  );
};
