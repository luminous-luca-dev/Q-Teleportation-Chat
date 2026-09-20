'use client';

import React, { useRef, useEffect } from 'react';
import { LogEntry } from '@/hooks/useQuantumWebSocket';
import { Terminal, Trash2 } from 'lucide-react';

interface TerminalPanelProps {
  logs: LogEntry[];
  onClear?: () => void;
}

export const TerminalPanel: React.FC<TerminalPanelProps> = ({ logs, onClear }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLevelBadge = (level: LogEntry['level']) => {
    switch (level) {
      case 'QUANTUM':
        return <span className="text-cyan-400 font-bold">[QUANTUM]</span>;
      case 'MEASURE':
        return <span className="text-purple-400 font-bold">[MEASURE]</span>;
      case 'CLASSICAL':
        return <span className="text-amber-400 font-bold">[CLASSIC]</span>;
      case 'SUCCESS':
        return <span className="text-green-400 font-bold">[SUCCESS]</span>;
      default:
        return <span className="text-slate-400">[SYSTEM]</span>;
    }
  };

  return (
    <div className="bg-black/85 border border-cyan-500/30 rounded-lg p-3 font-mono flex flex-col h-full text-xs">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-cyan-500/20">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-cyan-300 font-bold tracking-wider text-[11px]">
            QUANTUM SYSTEM TERMINAL / HARDWARE LOG
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-400">{logs.length} entries</span>
          {onClear && (
            <button
              type="button"
              onClick={onClear}
              className="text-slate-400 hover:text-slate-200 p-0.5 cursor-pointer"
              title="Clear logs"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1 p-2 bg-slate-950/70 rounded border border-slate-900 font-mono text-[11px] leading-relaxed">
        {logs.length === 0 ? (
          <div className="text-slate-400 text-center py-6">
            -- NO QUANTUM TRAFFIC LOGGED --
          </div>
        ) : (
          logs.map((l) => (
            <div key={l.id} className="flex items-start gap-2 hover:bg-slate-900/40 px-1 rounded">
              <span className="text-slate-400 shrink-0 text-[10px]">{l.timestamp}</span>
              <span className="shrink-0">{getLevelBadge(l.level)}</span>
              <span className="text-slate-300 break-all">{l.text}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
