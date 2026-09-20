'use client';

import React from 'react';
import { QuantumStateStep } from '@/lib/types';
import { Binary, ArrowRight, Eye, Sparkles } from 'lucide-react';

interface AlicePanelProps {
  step: QuantumStateStep | null;
  isStreaming: boolean;
}

export const AlicePanel: React.FC<AlicePanelProps> = ({ step, isStreaming }) => {
  const bitVal = step?.bit_value ?? 0;
  const c0 = step?.classical_bits[0];
  const c1 = step?.classical_bits[1];

  const isEncoded = step && step.step !== 'INIT';
  const isEntangled = step && ['ALICE_CNOT', 'ALICE_H', 'ALICE_MEASURE', 'CLASSICAL_SEND', 'BOB_X', 'BOB_Z', 'BOB_MEASURE', 'COMPLETE'].includes(step.step);
  const isMeasured = step && ['ALICE_MEASURE', 'CLASSICAL_SEND', 'BOB_X', 'BOB_Z', 'BOB_MEASURE', 'COMPLETE'].includes(step.step);

  return (
    <div className="bg-slate-950/85 border border-cyan-500/30 rounded-lg p-3 font-mono flex flex-col h-full text-xs overflow-hidden">
      {/* ヘッダー */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-cyan-500/20">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
          <span className="text-cyan-300 font-bold tracking-wider">
            TRANSMITTER INSTRUMENT: ALICE
          </span>
        </div>
        <span className="text-[10px] bg-cyan-950 border border-cyan-800 text-cyan-300 px-2 py-0.5 rounded">
          NODE: 0xALICE
        </span>
      </div>

      <div className="flex-1 flex flex-col gap-2 justify-between">
        {/* ステージ 1: 文字 → UTF-8 バイナリ → 量子ビット準備 */}
        <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
            <span className="flex items-center gap-1">
              <Binary className="w-3.5 h-3.5 text-cyan-400" />
              1. 転送対象文字のバイナリ量子化
            </span>
            <span className="text-cyan-300 font-bold">
              {step ? `文字: '${step.char}'` : '待機中'}
            </span>
          </div>

          <div className="flex items-center justify-around bg-slate-950/80 p-2 rounded border border-slate-800/80">
            <div className="text-center">
              <div className="text-[10px] text-slate-400">入力ビット値</div>
              <div className="text-base font-bold text-cyan-400">
                {step ? step.bit_value : '-'}
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400" />
            <div className="text-center">
              <div className="text-[10px] text-slate-400">初期化量子状態</div>
              <div className="text-sm font-bold text-purple-300">
                {step ? (step.bit_value === 0 ? '|0⟩' : '|1⟩') : '|?⟩'}
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400" />
            <div className="text-center">
              <div className="text-[10px] text-slate-400">エンコード状態</div>
              <div className={`text-[10px] px-1.5 py-0.5 rounded border ${
                isEncoded
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-500'
                  : 'bg-slate-900 text-slate-400 border-slate-800'
              }`}>
                {isEncoded ? 'ENCODED' : 'READY'}
              </div>
            </div>
          </div>
        </div>

        {/* ステージ 2: ベル対との複合ゲート操作 (Aliceのエンタングルメント測定準備) */}
        <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800">
          <div className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              2. ベル基底測定プロセス (q0 &amp; q1)
            </span>
            <span className="text-purple-300 text-[10px]">
              {step?.step === 'ALICE_CNOT' ? 'CNOTゲート適用中' : step?.step === 'ALICE_H' ? 'Hゲート適用中' : ''}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className={`p-2 rounded border transition-all ${
              step?.step === 'ALICE_CNOT'
                ? 'bg-purple-950/80 border-purple-400 text-purple-200 shadow-[0_0_8px_rgba(168,85,247,0.5)]'
                : 'bg-slate-950/60 border-slate-800 text-slate-400'
            }`}>
              <div className="font-semibold text-[10px]">CNOT (q0 → q1)</div>
              <div className="text-[9px] text-slate-400 mt-0.5">Alice保有の2量子ビットをもつれさせる</div>
            </div>

            <div className={`p-2 rounded border transition-all ${
              step?.step === 'ALICE_H'
                ? 'bg-cyan-950/80 border-cyan-400 text-cyan-200 shadow-[0_0_8px_rgba(0,240,255,0.5)]'
                : 'bg-slate-950/60 border-slate-800 text-slate-400'
            }`}>
              <div className="font-semibold text-[10px]">Hadamard (q0)</div>
              <div className="text-[9px] text-slate-400 mt-0.5">X基底へ変換しベル測定を完了させる</div>
            </div>
          </div>
        </div>

        {/* ステージ 3: 測定と古典通信出力 */}
        <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span className="flex items-center gap-1">
              <Eye className="w-3.5 h-3.5 text-amber-400" />
              3. 測定結果確定 (古典チャネルへ送出)
            </span>
            <span className={`text-[10px] px-1.5 rounded ${
              isMeasured ? 'bg-amber-950 text-amber-300 border border-amber-600' : 'text-slate-400'
            }`}>
              {isMeasured ? 'MEASURED' : 'PENDING'}
            </span>
          </div>

          <div className="flex items-center gap-3 bg-slate-950/80 p-2 rounded border border-slate-800">
            <div className="flex-1 text-center bg-slate-900/80 p-1.5 rounded border border-slate-800">
              <span className="text-[10px] text-slate-400 block">古典ビット c0 (q0観測)</span>
              <span className={`text-base font-bold ${c0 !== null && c0 !== undefined ? 'text-amber-400' : 'text-slate-400'}`}>
                {c0 !== null && c0 !== undefined ? c0 : '-'}
              </span>
            </div>
            <div className="flex-1 text-center bg-slate-900/80 p-1.5 rounded border border-slate-800">
              <span className="text-[10px] text-slate-400 block">古典ビット c1 (q1観測)</span>
              <span className={`text-base font-bold ${c1 !== null && c1 !== undefined ? 'text-amber-400' : 'text-slate-400'}`}>
                {c1 !== null && c1 !== undefined ? c1 : '-'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
