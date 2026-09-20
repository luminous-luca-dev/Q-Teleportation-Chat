'use client';

import React, { useEffect, useState, useCallback, useTransition } from 'react';
import GridLayout, { Layout } from 'react-grid-layout';
import { Header } from '@/components/Header';
import { CircuitViewer } from '@/components/CircuitViewer';
import { BlochSphereViewer } from '@/components/BlochSphereViewer';
import { TelemetryPanel } from '@/components/TelemetryPanel';
import { ChatConsole } from '@/components/ChatConsole';
import { AlicePanel } from '@/components/AlicePanel';
import { BobPanel } from '@/components/BobPanel';
import { TerminalPanel } from '@/components/TerminalPanel';
import { useQuantumWebSocket } from '@/hooks/useQuantumWebSocket';
import { User, Room, fetchUsers, fetchRooms, fetchMessages, sendInstantMessage } from '@/lib/api';
import { LayoutGrid, RotateCcw } from 'lucide-react';

const DEFAULT_LAYOUT: Layout[] = [
  // 12カラムグリッド配置
  { i: 'circuit', x: 0, y: 0, w: 8, h: 5, minW: 4, minH: 3 },
  { i: 'chat', x: 8, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
  { i: 'bloch', x: 0, y: 5, w: 4, h: 5, minW: 3, minH: 3 },
  { i: 'telemetry', x: 8, y: 6, w: 4, h: 4, minW: 3, minH: 3 },
  { i: 'alice', x: 4, y: 5, w: 4, h: 5, minW: 3, minH: 3 },
  { i: 'bob', x: 0, y: 10, w: 6, h: 4, minW: 3, minH: 3 },
  { i: 'terminal', x: 6, y: 10, w: 6, h: 4, minW: 3, minH: 3 },
];

export default function Home() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [currentRoom, setCurrentRoom] = useState<Room | null>(null);
  const [speedMs, setSpeedMs] = useState(100);
  const [layout, setLayout] = useState<Layout[]>(DEFAULT_LAYOUT);
  const [containerWidth, setContainerWidth] = useState(1400);

  // WebSocket カスタムフック
  const {
    isConnected,
    isStreaming,
    currentStep,
    lastSummary,
    messages,
    setMessages,
    logs,
    addLog,
    sendMessage,
  } = useQuantumWebSocket(currentRoom?.room_id, currentUser?.user_id);

  // 初期データ取得
  useEffect(() => {
    async function init() {
      try {
        const uList = await fetchUsers();
        setUsers(uList);
        if (uList.length > 0) setCurrentUser(uList[0]);

        const rList = await fetchRooms();
        setRooms(rList);
        if (rList.length > 0) {
          setCurrentRoom(rList[0]);
          const mList = await fetchMessages(rList[0].room_id);
          setMessages(mList);
        }
      } catch (err) {
        console.error('Init error:', err);
      }
    }
    init();
  }, [setMessages]);

  // ウィンドウ幅追従
  useEffect(() => {
    const handleResize = () => {
      setContainerWidth(Math.max(1000, window.innerWidth - 32));
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // メッセージ送信
  const handleSendMessage = useCallback(
    async (text: string, mode: 'instant' | 'slow') => {
      if (!currentRoom || !currentUser) return;

      if (mode === 'instant') {
        try {
          addLog(`Sending instant quantum message: "${text}"`, 'INFO');
          const res = await sendInstantMessage(currentRoom.room_id, currentUser.user_id, text);
          setMessages((prev) => [...prev, res.message]);
          addLog(`Instant teleport complete: ${res.teleport_result.total_bits} bits transferred`, 'SUCCESS');
        } catch (err) {
          console.error('Instant send failed:', err);
          addLog('Failed to transmit message', 'INFO');
        }
      } else {
        sendMessage(text, 'slow', speedMs / 1000);
      }
    },
    [currentRoom, currentUser, speedMs, sendMessage, setMessages, addLog]
  );

  return (
    <div className="min-h-screen bg-[#050811] text-slate-200 cyber-grid scanline flex flex-col">
      {/* ヘッダー */}
      <Header
        users={users}
        currentUser={currentUser}
        currentRoom={currentRoom}
        onSwitchUser={setCurrentUser}
        isConnected={isConnected}
      />

      {/* サブバー: レイアウトリセット & グリッド状態 */}
      <div className="px-6 py-1.5 bg-slate-950/60 border-b border-cyan-500/10 flex items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-2 text-slate-400">
          <LayoutGrid className="w-3.5 h-3.5 text-cyan-400" />
          <span>CYBERDECK MODULAR WORKSPACE (Drag &amp; Resize enabled)</span>
        </div>
        <button
          type="button"
          onClick={() => setLayout(DEFAULT_LAYOUT)}
          className="flex items-center gap-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 px-2 py-0.5 rounded cursor-pointer transition-all"
          title="Reset panels to default layout"
        >
          <RotateCcw className="w-3 h-3" />
          <span>レイアウトリセット</span>
        </button>
      </div>

      {/* メイン: react-grid-layout マルチパネル */}
      <main className="flex-1 p-4 max-w-[1920px] mx-auto w-full">
        <GridLayout
          className="layout"
          layout={layout}
          cols={12}
          rowHeight={65}
          width={containerWidth}
          onLayoutChange={(newLayout) => setLayout(newLayout)}
          draggableHandle=".panel-drag-handle"
          isResizable={true}
          isDraggable={true}
        >
          {/* 1. 量子回路パネル */}
          <div key="circuit" className="overflow-hidden flex flex-col">
            <div className="panel-drag-handle cursor-move bg-slate-900/90 hover:bg-cyan-950/60 px-3 py-1 border-t border-x border-cyan-500/30 rounded-t text-[10px] font-mono text-cyan-300 flex items-center justify-between">
              <span>::: PANEL 01 — QUANTUM CIRCUIT (QISKIT) :::</span>
              <span className="text-[9px] text-slate-400">DRAG</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <CircuitViewer step={currentStep} />
            </div>
          </div>

          {/* 2. チャットコンソール */}
          <div key="chat" className="overflow-hidden flex flex-col">
            <div className="panel-drag-handle cursor-move bg-slate-900/90 hover:bg-cyan-950/60 px-3 py-1 border-t border-x border-cyan-500/30 rounded-t text-[10px] font-mono text-cyan-300 flex items-center justify-between">
              <span>::: PANEL 02 — CHAT TERMINAL :::</span>
              <span className="text-[9px] text-slate-400">DRAG</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <ChatConsole
                currentUser={currentUser}
                messages={messages}
                onSendMessage={handleSendMessage}
                isStreaming={isStreaming}
              />
            </div>
          </div>

          {/* 3. ブロッホ球 & 状態ベクトル */}
          <div key="bloch" className="overflow-hidden flex flex-col">
            <div className="panel-drag-handle cursor-move bg-slate-900/90 hover:bg-cyan-950/60 px-3 py-1 border-t border-x border-cyan-500/30 rounded-t text-[10px] font-mono text-cyan-300 flex items-center justify-between">
              <span>::: PANEL 03 — BLOCH SPHERE &amp; STATE VECTOR :::</span>
              <span className="text-[9px] text-slate-400">DRAG</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <BlochSphereViewer step={currentStep} />
            </div>
          </div>

          {/* 4. テレメトリ & 速度制御 */}
          <div key="telemetry" className="overflow-hidden flex flex-col">
            <div className="panel-drag-handle cursor-move bg-slate-900/90 hover:bg-cyan-950/60 px-3 py-1 border-t border-x border-cyan-500/30 rounded-t text-[10px] font-mono text-cyan-300 flex items-center justify-between">
              <span>::: PANEL 04 — TELEMETRY &amp; SPEED CONTROL :::</span>
              <span className="text-[9px] text-slate-400">DRAG</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <TelemetryPanel
                step={currentStep}
                summary={lastSummary}
                isStreaming={isStreaming}
                speedMs={speedMs}
                onSpeedChange={setSpeedMs}
              />
            </div>
          </div>

          {/* 5. Alice 送信詳細計器パネル */}
          <div key="alice" className="overflow-hidden flex flex-col">
            <div className="panel-drag-handle cursor-move bg-slate-900/90 hover:bg-cyan-950/60 px-3 py-1 border-t border-x border-cyan-500/30 rounded-t text-[10px] font-mono text-cyan-300 flex items-center justify-between">
              <span>::: PANEL 05 — ALICE ENCODE &amp; MEASUREMENT :::</span>
              <span className="text-[9px] text-slate-400">DRAG</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <AlicePanel step={currentStep} isStreaming={isStreaming} />
            </div>
          </div>

          {/* 6. Bob 受信詳細計器パネル */}
          <div key="bob" className="overflow-hidden flex flex-col">
            <div className="panel-drag-handle cursor-move bg-slate-900/90 hover:bg-green-950/60 px-3 py-1 border-t border-x border-green-500/30 rounded-t text-[10px] font-mono text-green-300 flex items-center justify-between">
              <span>::: PANEL 06 — BOB DECODE &amp; CORRECTION :::</span>
              <span className="text-[9px] text-slate-400">DRAG</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <BobPanel step={currentStep} isStreaming={isStreaming} />
            </div>
          </div>

          {/* 7. システム・ハードウェアログ ターミナル */}
          <div key="terminal" className="overflow-hidden flex flex-col">
            <div className="panel-drag-handle cursor-move bg-slate-900/90 hover:bg-cyan-950/60 px-3 py-1 border-t border-x border-cyan-500/30 rounded-t text-[10px] font-mono text-cyan-300 flex items-center justify-between">
              <span>::: PANEL 07 — SYSTEM &amp; QUANTUM HARDWARE LOG :::</span>
              <span className="text-[9px] text-slate-400">DRAG</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <TerminalPanel logs={logs} />
            </div>
          </div>
        </GridLayout>
      </main>
    </div>
  );
}
