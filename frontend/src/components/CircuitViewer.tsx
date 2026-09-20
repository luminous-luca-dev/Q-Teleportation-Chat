'use client';

import React from 'react';
import { QuantumStateStep } from '@/lib/types';

interface CircuitViewerProps {
  step: QuantumStateStep | null;
}

export const CircuitViewer: React.FC<CircuitViewerProps> = ({ step }) => {
  // 3本の量子ワイヤ: q0(Alice Msg), q1(Alice Bell), q2(Bob Bell)
  const currentStep = step?.step || 'INIT';

  const isGateActive = (gateName: string) => {
    switch (gateName) {
      case 'ENCODE_X':
        return currentStep === 'ENCODE' && step?.bit_value === 1;
      case 'BELL_H':
        return currentStep === 'BELL_H';
      case 'BELL_CNOT':
        return currentStep === 'BELL_CNOT';
      case 'ALICE_CNOT':
        return currentStep === 'ALICE_CNOT';
      case 'ALICE_H':
        return currentStep === 'ALICE_H';
      case 'ALICE_MEASURE':
        return currentStep === 'ALICE_MEASURE' || currentStep === 'CLASSICAL_SEND';
      case 'BOB_X':
        return currentStep === 'BOB_X';
      case 'BOB_Z':
        return currentStep === 'BOB_Z';
      case 'BOB_MEASURE':
        return currentStep === 'BOB_MEASURE' || currentStep === 'COMPLETE';
      default:
        return false;
    }
  };

  const getGateBadgeClass = (active: boolean) =>
    `px-2 py-1 rounded text-xs font-mono border transition-all duration-300 ${
      active
        ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200 shadow-[0_0_12px_rgba(0,240,255,0.6)] scale-110'
        : 'bg-slate-900/60 border-slate-700 text-slate-400'
    }`;

  return (
    <div className="bg-slate-950/80 border border-cyan-500/30 rounded-lg p-4 font-mono relative overflow-hidden flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-cyan-500/20">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
          <span className="text-cyan-300 font-bold text-sm tracking-wider">
            QUANTUM TELEPORTATION CIRCUIT (QISKIT AER)
          </span>
        </div>
        <span className="text-xs text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
          {currentStep}
        </span>
      </div>

      {/* 回路ダイアグラム */}
      <div className="flex-1 flex flex-col justify-around py-2 relative text-xs">
        {/* q0: Alice Qubit |psi> */}
        <div className="relative flex items-center h-12">
          <div className="w-28 text-slate-300 font-semibold flex items-center gap-1 shrink-0">
            <span className="text-cyan-400">q₀</span>
            <span className="text-[10px] text-slate-400">|ψ⟩ Alice</span>
          </div>
          <div className="flex-1 h-[2px] bg-cyan-500/30 relative flex items-center justify-around">
            <div className={getGateBadgeClass(isGateActive('ENCODE_X'))}>
              {step?.bit_value === 1 ? 'X (bit=1)' : 'I (bit=0)'}
            </div>
            <div className="w-8"></div>
            <div className="w-8"></div>
            <div className={getGateBadgeClass(isGateActive('ALICE_CNOT'))}>● (Ctrl)</div>
            <div className={getGateBadgeClass(isGateActive('ALICE_H'))}>H</div>
            <div className={getGateBadgeClass(isGateActive('ALICE_MEASURE'))}>
              M → c₀ [{step?.classical_bits[0] ?? '-'}]
            </div>
            <div className="w-16"></div>
          </div>
        </div>

        {/* q1: Bell Pair (Alice half) */}
        <div className="relative flex items-center h-12">
          <div className="w-28 text-slate-300 font-semibold flex items-center gap-1 shrink-0">
            <span className="text-purple-400">q₁</span>
            <span className="text-[10px] text-slate-400">|0⟩ Bell(A)</span>
          </div>
          <div className="flex-1 h-[2px] bg-purple-500/30 relative flex items-center justify-around">
            <div className="w-12"></div>
            <div className={getGateBadgeClass(isGateActive('BELL_H'))}>H</div>
            <div className={getGateBadgeClass(isGateActive('BELL_CNOT'))}>● (Ctrl)</div>
            <div className={getGateBadgeClass(isGateActive('ALICE_CNOT'))}>⊕ (Target)</div>
            <div className="w-8"></div>
            <div className={getGateBadgeClass(isGateActive('ALICE_MEASURE'))}>
              M → c₁ [{step?.classical_bits[1] ?? '-'}]
            </div>
            <div className="w-16"></div>
          </div>
        </div>

        {/* q2: Bell Pair (Bob half) */}
        <div className="relative flex items-center h-12">
          <div className="w-28 text-slate-300 font-semibold flex items-center gap-1 shrink-0">
            <span className="text-green-400">q₂</span>
            <span className="text-[10px] text-slate-400">|0⟩ Bob</span>
          </div>
          <div className="flex-1 h-[2px] bg-green-500/30 relative flex items-center justify-around">
            <div className="w-12"></div>
            <div className="w-8"></div>
            <div className={getGateBadgeClass(isGateActive('BELL_CNOT'))}>⊕ (Target)</div>
            <div className="w-12"></div>
            <div className="w-8"></div>
            <div className="flex gap-1">
              <div className={getGateBadgeClass(isGateActive('BOB_X'))}>
                X<sup>c1</sup>
              </div>
              <div className={getGateBadgeClass(isGateActive('BOB_Z'))}>
                Z<sup>c0</sup>
              </div>
            </div>
            <div className={getGateBadgeClass(isGateActive('BOB_MEASURE'))}>
              M → {step?.bob_recovered_bit ?? '?'}
            </div>
          </div>
        </div>

        {/* 古典通信チャネル線 */}
        <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-2">
            <span className="text-amber-400">📡 古典通信チャンネル:</span>
            <span>
              c₀ = {step?.classical_bits[0] ?? '未測定'}, c₁ = {step?.classical_bits[1] ?? '未測定'}
            </span>
          </div>
          <div className="text-right text-cyan-300">
            Bob復元ビット:{' '}
            <span className="text-green-400 font-bold text-sm">
              {step?.bob_recovered_bit ?? '---'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
