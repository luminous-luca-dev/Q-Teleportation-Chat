'use client';

import React from 'react';
import { QuantumStateStep } from '@/lib/types';
import { Bloch3DCanvas } from '@/components/Bloch3DCanvas';

interface BlochSphereViewerProps {
  step: QuantumStateStep | null;
}

export const BlochSphereViewer: React.FC<BlochSphereViewerProps> = ({ step }) => {
  const v0 = step?.bloch_vector_q0 || { x: 0, y: 0, z: 1 };
  const v2 = step?.bloch_vector_q2 || { x: 0, y: 0, z: 1 };

  // 3量子ビットの基底 |000> ~ |111> の確率振幅・測定確率
  const stateVector = step?.state_vector || [];
  const basisStates = ['|000⟩', '|001⟩', '|010⟩', '|011⟩', '|100⟩', '|101⟩', '|110⟩', '|111⟩'];
  const probabilities = stateVector.map(([re, im]) => Math.min(1.0, re * re + im * im));

  return (
    <div className="bg-slate-950/85 border border-cyan-500/30 rounded-lg p-3 font-mono flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-cyan-500/20">
        <span className="text-cyan-300 font-bold text-xs tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          REAL-TIME 3D BLOCH SPHERES &amp; STATE VECTOR
        </span>
        <span className="text-[10px] text-slate-400 bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded">
          Three.js WebGL
        </span>
      </div>

      {/* 2連 3Dブロッホ球 */}
      <div className="flex items-center justify-around bg-slate-900/40 p-2 rounded border border-slate-800/80 mb-2">
        <Bloch3DCanvas vector={v0} colorHex={0x00f0ff} label="q₀: Alice 送信ビット" />
        <div className="h-24 w-[1px] bg-slate-800" />
        <Bloch3DCanvas vector={v2} colorHex={0x00ff66} label="q₂: Bob 復元ビット" />
      </div>

      {/* 状態ベクトルの確率分布バー */}
      <div className="flex-1 flex flex-col justify-end bg-slate-900/30 p-2 rounded border border-slate-800">
        <div className="text-[10px] text-slate-400 mb-1 flex justify-between">
          <span>8基底状態 確率振幅 (|q₀, q₁, q₂⟩)</span>
          <span className="text-cyan-400">Σ|c_i|² = 1.00</span>
        </div>
        <div className="grid grid-cols-8 gap-1 items-end h-16 pt-1">
          {basisStates.map((basis, idx) => {
            const prob = probabilities[idx] ?? 0;
            const heightPercent = Math.max(6, Math.round(prob * 100));
            const isHigh = prob > 0.15;
            return (
              <div key={basis} className="flex flex-col items-center h-full justify-end">
                <span className="text-[8px] text-slate-400 mb-0.5">
                  {prob > 0.02 ? `${(prob * 100).toFixed(0)}%` : ''}
                </span>
                <div
                  className="w-full rounded-t transition-all duration-300 border-t"
                  style={{
                    height: `${heightPercent}%`,
                    backgroundColor: isHigh ? 'rgba(0, 240, 255, 0.45)' : 'rgba(51, 65, 85, 0.3)',
                    borderColor: isHigh ? '#00f0ff' : '#475569',
                  }}
                />
                <span className="text-[8px] text-slate-400 font-mono mt-0.5">{basis}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
