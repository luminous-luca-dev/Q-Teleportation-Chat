'use client';

import React from 'react';
import { QuantumStateStep, TeleportSummary } from '@/lib/types';
import { Activity, Radio, Cpu, ShieldCheck, Gauge } from 'lucide-react';

interface TelemetryPanelProps {
  step: QuantumStateStep | null;
  summary: TeleportSummary | null;
  isStreaming: boolean;
  speedMs: number;
  onSpeedChange: (speed: number) => void;
}

export const TelemetryPanel: React.FC<TelemetryPanelProps> = ({
  step,
  summary,
  isStreaming,
  speedMs,
  onSpeedChange,
}) => {
  const progressPercent =
    step && step.total_bits > 0
      ? Math.round(((step.bit_index + 1) / step.total_bits) * 100)
      : summary
      ? 100
      : 0;

  return (
    <div className="bg-slate-950/80 border border-cyan-500/30 rounded-lg p-4 font-mono flex flex-col h-full justify-between">
      <div>
        <div className="flex items-center justify-between pb-2 mb-3 border-b border-cyan-500/20">
          <span className="text-cyan-300 font-bold text-sm tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            TELEMETRY &amp; HARDWARE CONTROLS
          </span>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
              isStreaming
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 animate-pulse'
                : 'bg-green-500/20 text-green-300 border border-green-500/50'
            }`}
          >
            {isStreaming ? 'TRANSMITTING' : 'IDLE / READY'}
          </span>
        </div>

        {/* テレポーテーション進捗バー */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-slate-300 mb-1">
            <span>ビット転送進捗 ({step ? `${step.bit_index + 1} / ${step.total_bits}` : '待機中'})</span>
            <span className="text-cyan-400 font-bold">{progressPercent}%</span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-cyan-500 via-purple-500 to-green-400 h-2.5 transition-all duration-200"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* 速度調整スライダー */}
        <div className="bg-slate-900/60 p-3 rounded border border-slate-800 mb-4">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-300 flex items-center gap-1">
              <Gauge className="w-3.5 h-3.5 text-amber-400" />
              ステップ実行ディレイ (速度調整)
            </span>
            <span className="text-amber-300 font-bold">{speedMs} ms / ゲート</span>
          </div>
          <input
            type="range"
            min="20"
            max="1000"
            step="20"
            value={speedMs}
            onChange={(e) => onSpeedChange(Number(e.target.value))}
            className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>高速 (20ms)</span>
            <span>標準 (100ms)</span>
            <span>観察モード (1s)</span>
          </div>
        </div>

        {/* 計器パラメータグリッド */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-slate-900/40 p-2 rounded border border-slate-800/80 flex flex-col">
            <span className="text-[10px] text-slate-400 flex items-center gap-1">
              <Radio className="w-3 h-3 text-cyan-400" />
              転送中文字
            </span>
            <span className="text-sm font-bold text-cyan-300 mt-0.5">
              {step ? `'${step.char}' (bit: ${step.bit_value})` : '---'}
            </span>
          </div>

          <div className="bg-slate-900/40 p-2 rounded border border-slate-800/80 flex flex-col">
            <span className="text-[10px] text-slate-400 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-green-400" />
              忠実度 (Fidelity)
            </span>
            <span className="text-sm font-bold text-green-400 mt-0.5">
              {summary ? `${(summary.success_rate * 100).toFixed(1)}%` : '100.0%'}
            </span>
          </div>
        </div>
      </div>

      {/* 実行ログ */}
      <div className="mt-3 bg-black/60 p-2.5 rounded border border-cyan-500/20 text-[11px] font-mono">
        <div className="text-[10px] text-slate-400 border-b border-slate-800 pb-1 mb-1">
          &gt; SYSTEM_LOG:
        </div>
        <p className="text-cyan-200 truncate">
          {step ? step.log : 'シミュレータ待機中。メッセージ送信でプロセス開始'}
        </p>
      </div>
    </div>
  );
};
