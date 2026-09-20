'use client';

import React from 'react';
import { QuantumStateStep } from '@/lib/types';
import { Radio, RefreshCw, CheckCircle2, ShieldAlert } from 'lucide-react';

interface BobPanelProps {
  step: QuantumStateStep | null;
  isStreaming: boolean;
}

export const BobPanel: React.FC<BobPanelProps> = ({ step, isStreaming }) => {
  const c0 = step?.classical_bits[0];
  const c1 = step?.classical_bits[1];
  const recoveredBit = step?.bob_recovered_bit;

  const needX = c1 === 1;
  const needZ = c0 === 1;

  const isXDone = step && ['BOB_Z', 'BOB_MEASURE', 'COMPLETE'].includes(step.step);
  const isZDone = step && ['BOB_MEASURE', 'COMPLETE'].includes(step.step);
  const isRecovered = step && ['BOB_MEASURE', 'COMPLETE'].includes(step.step);

  return (
    <div className="bg-slate-950/85 border border-green-500/30 rounded-lg p-3 font-mono flex flex-col h-full text-xs overflow-hidden">
      {/* ヘッダー */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-green-500/20">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-green-400"></span>
          <span className="text-green-300 font-bold tracking-wider">
            RECEIVER INSTRUMENT: BOB
          </span>
        </div>
        <span className="text-[10px] bg-green-950 border border-green-800 text-green-300 px-2 py-0.5 rounded">
          NODE: 0xBOB
        </span>
      </div>

      <div className="flex-1 flex flex-col gap-2 justify-between">
        {/* ステージ 1: 古典ビットの受信 */}
        <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
            <span className="flex items-center gap-1">
              <Radio className="w-3.5 h-3.5 text-amber-400" />
              1. 古典通信パケットの受信検知
            </span>
            <span className="text-amber-300 font-bold">
              {c0 !== null && c0 !== undefined ? 'PACKET RECEIVED' : 'WAITING FOR PACKET'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 bg-slate-950/80 p-2 rounded border border-slate-800/80 text-center">
            <div className="bg-slate-900/50 p-1.5 rounded">
              <span className="text-[10px] text-slate-400 block">受信 c0 (Z制御)</span>
              <span className="text-sm font-bold text-amber-400">{c0 ?? '-'}</span>
            </div>
            <div className="bg-slate-900/50 p-1.5 rounded">
              <span className="text-[10px] text-slate-400 block">受信 c1 (X制御)</span>
              <span className="text-sm font-bold text-amber-400">{c1 ?? '-'}</span>
            </div>
          </div>
        </div>

        {/* ステージ 2: パウリ補正ゲート適用判定 (X^c1, Z^c0) */}
        <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800">
          <div className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1">
              <RefreshCw className="w-3.5 h-3.5 text-green-400" />
              2. 量子状態の復元 (条件付きパウリ補正)
            </span>
            <span className="text-green-300 text-[10px]">Bobの量子ビット q2</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className={`p-2 rounded border transition-all ${
              step?.step === 'BOB_X'
                ? 'bg-green-950/80 border-green-400 text-green-200 shadow-[0_0_8px_rgba(0,255,102,0.5)]'
                : 'bg-slate-950/60 border-slate-800 text-slate-400'
            }`}>
              <div className="flex justify-between items-center font-semibold text-[10px]">
                <span>X ゲート (ビット反転)</span>
                <span className={`text-[9px] px-1 rounded ${needX ? 'bg-green-900 text-green-300' : 'text-slate-400'}`}>
                  {needX ? 'REQUIRED' : 'BYPASS'}
                </span>
              </div>
              <div className="text-[9px] text-slate-400 mt-0.5">
                c1=1 の場合に q2 を反転 ({isXDone ? 'APPLIED' : 'PENDING'})
              </div>
            </div>

            <div className={`p-2 rounded border transition-all ${
              step?.step === 'BOB_Z'
                ? 'bg-green-950/80 border-green-400 text-green-200 shadow-[0_0_8px_rgba(0,255,102,0.5)]'
                : 'bg-slate-950/60 border-slate-800 text-slate-400'
            }`}>
              <div className="flex justify-between items-center font-semibold text-[10px]">
                <span>Z ゲート (位相反転)</span>
                <span className={`text-[9px] px-1 rounded ${needZ ? 'bg-green-900 text-green-300' : 'text-slate-400'}`}>
                  {needZ ? 'REQUIRED' : 'BYPASS'}
                </span>
              </div>
              <div className="text-[9px] text-slate-400 mt-0.5">
                c0=1 の場合に位相補正 ({isZDone ? 'APPLIED' : 'PENDING'})
              </div>
            </div>
          </div>
        </div>

        {/* ステージ 3: 観測およびビット確定・テキストデコード */}
        <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
              3. Bob最終測定 → テレポーテーション完了
            </span>
            <span className={`text-[10px] px-1.5 rounded ${
              isRecovered ? 'bg-green-950 text-green-300 border border-green-600' : 'text-slate-400'
            }`}>
              {isRecovered ? 'DECODED' : 'PENDING'}
            </span>
          </div>

          <div className="flex items-center justify-between bg-slate-950/80 p-2 rounded border border-slate-800 text-center">
            <div>
              <span className="text-[10px] text-slate-400 block">復元ビット値</span>
              <span className="text-base font-bold text-green-400">
                {recoveredBit !== null && recoveredBit !== undefined ? recoveredBit : '-'}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-400 block">検証整合性</span>
              <span className={`text-xs font-bold ${
                recoveredBit === step?.bit_value ? 'text-green-400' : 'text-slate-400'
              }`}>
                {recoveredBit !== null && recoveredBit !== undefined
                  ? recoveredBit === step?.bit_value
                    ? '100% MATCH (Fidelity: 1.0)'
                    : 'BIT MISMATCH'
                  : 'VERIFYING'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
