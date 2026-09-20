import { useState, useEffect, useRef, useCallback } from 'react';
import { getWebSocketUrl, ChatMessage } from '@/lib/api';
import { QuantumStateStep, TeleportSummary, BlochVector, StepName } from '@/lib/types';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'QUANTUM' | 'MEASURE' | 'CLASSICAL' | 'SUCCESS';
  text: string;
}

export function useQuantumWebSocket(roomId?: string, userId?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStep, setCurrentStep] = useState<QuantumStateStep | null>(null);
  const [lastSummary, setLastSummary] = useState<TeleportSummary | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  const addLog = useCallback((text: string, level: LogEntry['level'] = 'INFO') => {
    const timeStr = new Date().toLocaleTimeString();
    setLogs((prev) => [
      ...prev.slice(-100), // 最新100件保持
      { id: Math.random().toString(36).substring(7), timestamp: timeStr, level, text },
    ]);
  }, []);

  useEffect(() => {
    if (!roomId || !userId) return;

    const wsUrl = getWebSocketUrl(roomId, userId);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      addLog(`WebSocket connection established with room [${roomId}]`, 'INFO');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'teleport_start') {
          setIsStreaming(true);
          setLastSummary(null);
          addLog(`Starting Quantum Teleportation protocol for "${data.text || ''}" (${data.total_bits} bits)`, 'QUANTUM');
        } else if (data.type === 'teleport_step') {
          const bVecs: BlochVector[] = data.bloch_vectors || [];
          const q0Vec = bVecs[0] || { x: 0, y: 0, z: 1 };
          const q2Vec = bVecs[2] || { x: 0, y: 0, z: 1 };

          const amplitudes = data.amplitudes || [];
          const stateVec: [number, number][] = amplitudes.map((a: { real: number; imag: number }) => [a.real, a.imag]);

          const stepData: QuantumStateStep = {
            ...data,
            step: (data.step_id || data.step) as StepName,
            char: data.current_char ?? data.char ?? '',
            bit_value: data.input_bit ?? data.bit_value ?? 0,
            log: data.log_message ?? data.log ?? '',
            bob_recovered_bit: data.recovered_bit ?? data.bob_recovered_bit ?? null,
            bloch_vector_q0: q0Vec,
            bloch_vector_q2: q2Vec,
            state_vector: stateVec,
          };

          setCurrentStep(stepData);

          let lvl: LogEntry['level'] = 'QUANTUM';
          if (stepData.step === 'ALICE_MEASURE' || stepData.step === 'BOB_MEASURE') lvl = 'MEASURE';
          else if (stepData.step === 'CLASSICAL_SEND') lvl = 'CLASSICAL';

          addLog(`[Bit ${stepData.bit_index + 1}/${stepData.total_bits}] ${stepData.log}`, lvl);
        } else if (data.type === 'teleport_complete') {
          setIsStreaming(false);
          const summary = data.summary as TeleportSummary;
          setLastSummary(summary);
          addLog(`Teleport complete. Fidelity: ${(summary.success_rate * 100).toFixed(1)}% (${summary.circuits_run} circuits executed)`, 'SUCCESS');
        } else if (data.type === 'message_received') {
          setIsStreaming(false);
          // テキスト取得: data.recovered_text または data.original_text または data.text
          const msgText = data.recovered_text ?? data.original_text ?? data.text ?? '';
          const summaryObj: TeleportSummary = {
            original_text: data.original_text ?? msgText,
            recovered_text: data.recovered_text ?? msgText,
            total_bits: data.total_bits ?? 0,
            success_rate: data.success_rate ?? 1.0,
            all_bits_matched: data.success_rate === 1.0,
            circuits_run: data.total_bits ?? 0,
          };

          const parseTime = (val: unknown): number => {
            if (typeof val === 'number') return val > 1e11 ? val / 1000 : val;
            if (typeof val === 'string') {
              const parsed = new Date(val).getTime();
              if (!isNaN(parsed)) return parsed / 1000;
            }
            return Date.now() / 1000;
          };

          setMessages((prev) => [
            ...prev,
            {
              message_id: data.message_id || ('m_' + Date.now() + Math.random().toString(36).substring(7)),
              room_id: roomId,
              sender_id: data.sender_id,
              text: msgText,
              mode: data.mode || 'slow',
              created_at: parseTime(data.created_at),
              teleport_result: summaryObj,
            },
          ]);
        }
      } catch (err) {
        console.error('WS parse error:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      addLog('WebSocket link disconnected', 'INFO');
    };

    return () => {
      ws.close();
    };
  }, [roomId, userId, addLog]);

  const sendMessage = useCallback(
    (text: string, mode: 'instant' | 'slow', stepDelaySeconds: number = 0.1) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        if (mode === 'slow') {
          setIsStreaming(true);
        }
        wsRef.current.send(
          JSON.stringify({
            type: 'send_message',
            mode,
            text,
            step_delay: stepDelaySeconds,
          })
        );
      }
    },
    []
  );

  return {
    isConnected,
    isStreaming,
    currentStep,
    lastSummary,
    messages,
    setMessages,
    logs,
    addLog,
    sendMessage,
  };
}
