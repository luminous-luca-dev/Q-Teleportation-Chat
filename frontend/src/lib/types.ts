export type StepName =
  | 'INIT'
  | 'ENCODE'
  | 'BELL_H'
  | 'BELL_CNOT'
  | 'ALICE_CNOT'
  | 'ALICE_H'
  | 'ALICE_MEASURE'
  | 'CLASSICAL_SEND'
  | 'BOB_X'
  | 'BOB_Z'
  | 'BOB_MEASURE'
  | 'COMPLETE';

export interface BlochVector {
  x: number;
  y: number;
  z: number;
  r?: number;
  qubit?: number;
  label?: string;
  is_pure?: boolean;
}

export interface CircuitOp {
  op_id?: number;
  gate?: string;
  name?: string;
  label?: string;
  qubits?: number[];
  target_qubits?: number[];
  status?: 'pending' | 'active' | 'done';
}

export interface AmplitudeItem {
  index: number;
  label: string;
  real: number;
  imag: number;
  prob: number;
  phase_deg: number;
}

export interface QuantumStateStep {
  type: string;
  step_id: string;
  step_index: number;
  bit_index: number;
  total_bits: number;
  char_index: number;
  current_char: string;
  input_bit: number;
  phase: string;
  description: string;
  log_message: string;
  amplitudes: AmplitudeItem[];
  bloch_vectors: BlochVector[];
  circuit_ops: CircuitOp[];
  classical_bits: [number | null, number | null];
  recovered_bit: number | null;
  // フロントエンド互換エイリアス
  step: StepName;
  char: string;
  bit_value: number;
  log: string;
  bob_recovered_bit: number | null;
  bloch_vector_q0: BlochVector;
  bloch_vector_q2: BlochVector;
  state_vector: [number, number][];
}

export interface TeleportSummary {
  original_text: string;
  recovered_text: string;
  total_bits: number;
  success_rate: number;
  all_bits_matched: boolean;
  circuits_run: number;
}
