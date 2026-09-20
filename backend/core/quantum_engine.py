"""
quantum_engine.py — 量子テレポーテーション回路のコアロジック

【量子ビット構成 (3量子ビットシステム)】
  q0 : Alice のメッセージ量子ビット（転送したいビット）
  q1 : Alice のベル対量子ビット（エンタングル片割れ Alice側）
  q2 : Bob のベル対量子ビット（エンタングル片割れ Bob側）

【テレポーテーション手順】
  1. |000⟩ に初期化
  2. (bit=1なら) X gate on q0 → メッセージを |1⟩ にエンコード
  3. H gate on q1 → ベル対生成 Step1: |+⟩ 重ね合わせ
  4. CNOT(q1→q2) → ベル対生成 Step2: エンタングルメント |Φ+⟩
  5. CNOT(q0→q1) → Alice回路
  6. H gate on q0 → Alice回路
  7. Measure q0 → c0, Measure q1 → c1 (Alice観測)
  8. 古典チャンネルで (c0, c1) を Bob に送信
  9. c1==1 なら X gate on q2 (Bob補正)
 10. c0==1 なら Z gate on q2 (Bob補正)
 11. Measure q2 → 復元ビット (Bob観測)

【Blochベクトル計算】
  ρ = (I + r·σ)/2 より: x=2Re(ρ₀₁), y=-2Im(ρ₀₁), z=ρ₀₀-ρ₁₁
  エンタングル状態では r<1 (Bloch球内部 = 混合状態)

Qiskit 2.x 対応: Statevector.evolve() / DensityMatrix / partial_trace
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Generator, Optional

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace


# ─── ステップID定数 ──────────────────────────────────────────────────────────

STEP_INIT           = "INIT"
STEP_ENCODE         = "ENCODE"
STEP_BELL_H         = "BELL_H"
STEP_BELL_CNOT      = "BELL_CNOT"
STEP_ALICE_CNOT     = "ALICE_CNOT"
STEP_ALICE_H        = "ALICE_H"
STEP_ALICE_MEASURE  = "ALICE_MEASURE"
STEP_CLASSICAL_SEND = "CLASSICAL_SEND"
STEP_BOB_X          = "BOB_X"
STEP_BOB_Z          = "BOB_Z"
STEP_BOB_MEASURE    = "BOB_MEASURE"
STEP_COMPLETE       = "COMPLETE"

# 1ビットあたりのステップ数（可視化ステップ）
STEPS_PER_BIT: int = 12

# 量子ビットラベル
QUBIT_LABELS = ["Alice(msg) q0", "Alice(Bell) q1", "Bob(Bell) q2"]

# 量子フェーズ（スタイリング用）
PHASE_INIT      = "init"
PHASE_ALICE     = "alice"
PHASE_BELL      = "bell"
PHASE_CLASSICAL = "classical"
PHASE_BOB       = "bob"
PHASE_COMPLETE  = "complete"


# ─── 回路操作テンプレート ────────────────────────────────────────────────────
# フロントエンドが完全な回路図を描画するためのメタデータ

CIRCUIT_OPS_TEMPLATE: list[dict] = [
    {"op_id": 0,  "gate": "INIT",    "qubits": [0, 1, 2], "label": "初期化 |000⟩",           "phase": PHASE_INIT,      "status": "pending"},
    {"op_id": 1,  "gate": "X",       "qubits": [0],       "label": "ビットエンコード (X|I)",  "phase": PHASE_ALICE,     "status": "pending"},
    {"op_id": 2,  "gate": "H",       "qubits": [1],       "label": "ベル対生成: H gate q1",   "phase": PHASE_BELL,      "status": "pending"},
    {"op_id": 3,  "gate": "CNOT",    "qubits": [1, 2],    "label": "ベル対生成: CNOT q1→q2", "phase": PHASE_BELL,      "status": "pending"},
    {"op_id": 4,  "gate": "CNOT",    "qubits": [0, 1],    "label": "Alice: CNOT q0→q1",      "phase": PHASE_ALICE,     "status": "pending"},
    {"op_id": 5,  "gate": "H",       "qubits": [0],       "label": "Alice: H gate q0",        "phase": PHASE_ALICE,     "status": "pending"},
    {"op_id": 6,  "gate": "MEASURE", "qubits": [0, 1],    "label": "Alice: 観測 q0,q1",       "phase": PHASE_ALICE,     "status": "pending"},
    {"op_id": 7,  "gate": "CLASSIC", "qubits": [],        "label": "古典通信: (c0,c1) 送信",  "phase": PHASE_CLASSICAL, "status": "pending"},
    {"op_id": 8,  "gate": "X",       "qubits": [2],       "label": "Bob: X補正 (if c1=1)",   "phase": PHASE_BOB,       "status": "pending"},
    {"op_id": 9,  "gate": "Z",       "qubits": [2],       "label": "Bob: Z補正 (if c0=1)",   "phase": PHASE_BOB,       "status": "pending"},
    {"op_id": 10, "gate": "MEASURE", "qubits": [2],       "label": "Bob: 観測 q2",            "phase": PHASE_BOB,       "status": "pending"},
]


# ─── ブロッホ球・状態ベクトル ヘルパー ──────────────────────────────────────

def compute_bloch_vectors(sv: Statevector) -> list[dict]:
    """
    全量子ビットのブロッホベクトルを計算して返す。
    エンタングル中は r < 1.0（混合状態）になる点が視覚的に面白い。

    Returns: [{"qubit": i, "label": ..., "x": ..., "y": ..., "z": ..., "r": ..., "is_pure": ...}]
    """
    n = sv.num_qubits
    dm = DensityMatrix(sv)
    result = []

    for i in range(n):
        # i 以外の全ビットをトレースアウト → 1量子ビット密度行列
        qargs_out = [j for j in range(n) if j != i]
        rho = partial_trace(dm, qargs_out).data

        # ブロッホベクトル: ρ = (I + r·σ)/2
        # x = Tr(ρ σx) = 2 Re(ρ₀₁)
        # y = Tr(ρ σy) = -2 Im(ρ₀₁)   (σy = [[0,-i],[i,0]])
        # z = Tr(ρ σz) = ρ₀₀ - ρ₁₁
        x = float(2.0 * rho[0, 1].real)
        y = float(-2.0 * rho[0, 1].imag)
        z = float((rho[0, 0] - rho[1, 1]).real)
        r = float(np.sqrt(x**2 + y**2 + z**2))

        result.append({
            "qubit": i,
            "label": QUBIT_LABELS[i] if i < len(QUBIT_LABELS) else f"q{i}",
            "x": round(x, 6),
            "y": round(y, 6),
            "z": round(z, 6),
            "r": round(r, 6),
            "is_pure": r > 0.999,  # 純粋状態かどうか
        })

    return result


def sv_to_amplitudes(sv: Statevector) -> list[dict]:
    """
    状態ベクトルを JSON シリアライズ可能な振幅リストに変換。

    ケット表記は big-endian: |q2 q1 q0⟩

    Returns: [{"index": int, "label": str, "real": float, "imag": float, "prob": float, "phase_deg": float}]
    """
    n = sv.num_qubits
    amplitudes = []
    for idx, amp in enumerate(sv.data):
        # big-endian ケット表記: 上位ビット = q_{n-1}, 下位ビット = q0
        bits_str = "".join(str((idx >> k) & 1) for k in range(n - 1, -1, -1))
        label = f"|{bits_str}⟩"
        prob = float(abs(amp) ** 2)
        phase_deg = float(np.degrees(np.angle(amp))) if abs(amp) > 1e-10 else 0.0

        amplitudes.append({
            "index": idx,
            "label": label,
            "real": round(float(amp.real), 6),
            "imag": round(float(amp.imag), 6),
            "prob": round(prob, 6),
            "phase_deg": round(phase_deg, 2),
        })
    return amplitudes


# ─── 量子ゲート適用 ──────────────────────────────────────────────────────────

def _qc1(n_qubits: int, method: str, *args) -> QuantumCircuit:
    """指定ゲートを1つだけ含む QuantumCircuit を生成"""
    qc = QuantumCircuit(n_qubits)
    getattr(qc, method)(*args)
    return qc


def _apply(sv: Statevector, qc: QuantumCircuit) -> Statevector:
    """Statevector にゲートを適用"""
    return sv.evolve(qc)


# ─── 測定シミュレーション ────────────────────────────────────────────────────

def measure_qubit(sv: Statevector, qubit: int) -> tuple[int, Statevector]:
    """
    指定量子ビットを測定し、(測定値, 崩壊後Statevector) を返す。
    ボルン則に従いランダムサンプリング。

    Qiskit のリトルエンディアン規則:
      index の bit k = qubit k の状態
      → (idx >> qubit) & 1 でqubitの値を取得
    """
    n = sv.num_qubits
    probs = sv.probabilities([qubit])  # [P(0), P(1)]
    p0, p1 = float(probs[0]), float(probs[1])

    # 数値誤差対策: 確率を正規化
    total = p0 + p1
    if total < 1e-12:
        outcome = 0
    else:
        p0, p1 = p0 / total, p1 / total
        outcome = int(np.random.choice([0, 1], p=[p0, p1]))

    # 状態崩壊: 測定結果と一致しないインデックスの振幅を0に
    data = np.array(sv.data, dtype=complex)
    for idx in range(2 ** n):
        if ((idx >> qubit) & 1) != outcome:
            data[idx] = 0.0

    # 正規化
    norm = np.linalg.norm(data)
    if norm > 1e-12:
        data /= norm

    return outcome, Statevector(data)


# ─── メインジェネレーター ────────────────────────────────────────────────────

@dataclass
class TeleportStep:
    """テレポーテーション1ステップのデータスナップショット"""
    # メタ情報
    type: str = "teleport_step"
    step_id: str = ""
    step_index: int = 0
    bit_index: int = 0
    total_bits: int = 0
    char_index: int = 0
    current_char: str = ""
    input_bit: int = 0
    phase: str = ""
    description: str = ""
    log_message: str = ""
    # 量子状態
    amplitudes: list = field(default_factory=list)
    bloch_vectors: list = field(default_factory=list)
    circuit_ops: list = field(default_factory=list)
    # 古典情報
    classical_bits: list = field(default_factory=lambda: [None, None])
    recovered_bit: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "step_id": self.step_id,
            "step_index": self.step_index,
            "bit_index": self.bit_index,
            "total_bits": self.total_bits,
            "char_index": self.char_index,
            "current_char": self.current_char,
            "input_bit": self.input_bit,
            "phase": self.phase,
            "description": self.description,
            "log_message": self.log_message,
            "amplitudes": self.amplitudes,
            "bloch_vectors": self.bloch_vectors,
            "circuit_ops": self.circuit_ops,
            "classical_bits": self.classical_bits,
            "recovered_bit": self.recovered_bit,
        }


def teleport_bit_steps(
    bit: int,
    bit_index: int,
    total_bits: int,
    char_index: int,
    current_char: str,
) -> Generator[TeleportStep, None, None]:
    """
    1ビットの量子テレポーテーション全ステップを生成するジェネレーター。

    各ステップで TeleportStep をyieldする。
    フロントエンドはこれを受け取って各パネルを更新する。
    """
    N = 3  # 量子ビット数
    sv = Statevector.from_label("000")  # |q2 q1 q0⟩ = |000⟩
    classical_bits: list[Optional[int]] = [None, None]
    recovered_bit: Optional[int] = None
    step_idx = 0

    # 回路操作の状態管理（全ステップにコピーを埋め込む）
    ops = copy.deepcopy(CIRCUIT_OPS_TEMPLATE)
    active_op_id = -1

    def _mark_op(op_id: int, status: str = "active"):
        """指定opをアクティブに、それ以前を done に変更"""
        for op in ops:
            if op["op_id"] < op_id:
                op["status"] = "done"
            elif op["op_id"] == op_id:
                op["status"] = status
            else:
                op["status"] = "pending"

    def _snap(step_id: str, desc: str, log: str, phase: str) -> TeleportStep:
        nonlocal step_idx
        s = TeleportStep(
            step_id=step_id,
            step_index=step_idx,
            bit_index=bit_index,
            total_bits=total_bits,
            char_index=char_index,
            current_char=current_char,
            input_bit=bit,
            phase=phase,
            description=desc,
            log_message=log,
            amplitudes=sv_to_amplitudes(sv),
            bloch_vectors=compute_bloch_vectors(sv),
            circuit_ops=copy.deepcopy(ops),
            classical_bits=list(classical_bits),
            recovered_bit=recovered_bit,
        )
        step_idx += 1
        return s

    # ─── ステップ 0: INIT ───────────────────────────────────────────
    _mark_op(0, "done")
    yield _snap(
        STEP_INIT,
        "3量子ビットを初期化: |q2 q1 q0⟩ = |000⟩",
        f"[{bit_index:04d}/{total_bits}] INIT | char='{current_char}' | 全量子ビット |0⟩ にリセット",
        PHASE_INIT,
    )

    # ─── ステップ 1: ENCODE ─────────────────────────────────────────
    _mark_op(1, "active")
    if bit == 1:
        sv = _apply(sv, _qc1(N, "x", 0))
        ops[1]["label"] = "ビットエンコード: X gate (bit=1)"
    else:
        ops[1]["label"] = "ビットエンコード: 恒等 (bit=0)"
    _mark_op(1, "done")
    yield _snap(
        STEP_ENCODE,
        f"ビット {bit} を量子状態 |{bit}⟩ にエンコード → q0={'|1⟩' if bit else '|0⟩'}",
        f"[{bit_index:04d}/{total_bits}] ENCODE | bit={bit} | {'X gate applied → q0=|1⟩' if bit else 'Identity (no gate) → q0=|0⟩'}",
        PHASE_ALICE,
    )

    # ─── ステップ 2: BELL_H ─────────────────────────────────────────
    _mark_op(2, "active")
    sv = _apply(sv, _qc1(N, "h", 1))
    _mark_op(2, "done")
    yield _snap(
        STEP_BELL_H,
        "ベル対生成 ①: q1 に Hadamard gate → (|0⟩+|1⟩)/√2 重ね合わせ状態",
        f"[{bit_index:04d}/{total_bits}] BELL_H | q1: |0⟩ → |+⟩ = (|0⟩+|1⟩)/√2 | エンタングル準備開始",
        PHASE_BELL,
    )

    # ─── ステップ 3: BELL_CNOT ──────────────────────────────────────
    _mark_op(3, "active")
    sv = _apply(sv, _qc1(N, "cx", 1, 2))
    _mark_op(3, "done")
    yield _snap(
        STEP_BELL_CNOT,
        "ベル対生成 ②: CNOT(q1→q2) → エンタングルメント |Φ+⟩ = (|00⟩+|11⟩)/√2 生成",
        f"[{bit_index:04d}/{total_bits}] BELL_CNOT | q1,q2: |Φ+⟩ベル状態生成 | ブロッホ球r<1(混合状態)に注目!",
        PHASE_BELL,
    )

    # ─── ステップ 4: ALICE_CNOT ─────────────────────────────────────
    _mark_op(4, "active")
    sv = _apply(sv, _qc1(N, "cx", 0, 1))
    _mark_op(4, "done")
    yield _snap(
        STEP_ALICE_CNOT,
        "Alice操作 ①: CNOT(q0→q1) — メッセージとベル対を絡み合わせる",
        f"[{bit_index:04d}/{total_bits}] ALICE_CNOT | q0(ctrl)→q1(tgt) | Aliceの量子回路ステップ1",
        PHASE_ALICE,
    )

    # ─── ステップ 5: ALICE_H ────────────────────────────────────────
    _mark_op(5, "active")
    sv = _apply(sv, _qc1(N, "h", 0))
    _mark_op(5, "done")
    yield _snap(
        STEP_ALICE_H,
        "Alice操作 ②: q0 に Hadamard gate — ベル基底測定の準備",
        f"[{bit_index:04d}/{total_bits}] ALICE_H | q0: Hadamard gate適用 | Aliceの量子回路ステップ2",
        PHASE_ALICE,
    )

    # ─── ステップ 6: ALICE_MEASURE ──────────────────────────────────
    _mark_op(6, "active")
    c0, sv = measure_qubit(sv, 0)  # q0 測定 → c0
    c1, sv = measure_qubit(sv, 1)  # q1 測定 → c1
    classical_bits[0] = c0
    classical_bits[1] = c1
    ops[6]["label"] = f"Alice: 観測 → c0={c0}, c1={c1}"
    _mark_op(6, "done")
    yield _snap(
        STEP_ALICE_MEASURE,
        f"Alice 観測: q0→c0={c0}, q1→c1={c1} — 古典ビット ({c0},{c1}) が確定",
        f"[{bit_index:04d}/{total_bits}] ALICE_MEASURE | q0→c0={c0} | q1→c1={c1} | ベル基底測定完了 状態崩壊",
        PHASE_ALICE,
    )

    # ─── ステップ 7: CLASSICAL_SEND ─────────────────────────────────
    _mark_op(7, "active")
    ops[7]["label"] = f"古典通信: c0={c0}, c1={c1} 送信"
    _mark_op(7, "done")
    yield _snap(
        STEP_CLASSICAL_SEND,
        f"古典チャンネル: Alice → Bob  (c0={c0}, c1={c1}) を送信中...",
        f"[{bit_index:04d}/{total_bits}] CLASSICAL_TX | c0={c0} c1={c1} → Bobへ古典通信路で転送",
        PHASE_CLASSICAL,
    )

    # ─── ステップ 8: BOB_X ──────────────────────────────────────────
    _mark_op(8, "active")
    if c1 == 1:
        sv = _apply(sv, _qc1(N, "x", 2))
        ops[8]["label"] = f"Bob: X gate 適用 (c1=1)"
        log_x = "c1=1 → X gate を q2 に適用"
    else:
        ops[8]["label"] = f"Bob: X gate スキップ (c1=0)"
        log_x = "c1=0 → X gate スキップ"
    _mark_op(8, "done")
    yield _snap(
        STEP_BOB_X,
        f"Bob補正 ①: c1={c1} → {'X gate を q2 に適用' if c1 else 'X gate はスキップ'}",
        f"[{bit_index:04d}/{total_bits}] BOB_X | c1={c1} | {log_x}",
        PHASE_BOB,
    )

    # ─── ステップ 9: BOB_Z ──────────────────────────────────────────
    _mark_op(9, "active")
    if c0 == 1:
        sv = _apply(sv, _qc1(N, "z", 2))
        ops[9]["label"] = f"Bob: Z gate 適用 (c0=1)"
        log_z = "c0=1 → Z gate を q2 に適用"
    else:
        ops[9]["label"] = f"Bob: Z gate スキップ (c0=0)"
        log_z = "c0=0 → Z gate スキップ"
    _mark_op(9, "done")
    yield _snap(
        STEP_BOB_Z,
        f"Bob補正 ②: c0={c0} → {'Z gate を q2 に適用' if c0 else 'Z gate はスキップ'}",
        f"[{bit_index:04d}/{total_bits}] BOB_Z | c0={c0} | {log_z}",
        PHASE_BOB,
    )

    # ─── ステップ 10: BOB_MEASURE ───────────────────────────────────
    _mark_op(10, "active")
    rec, sv = measure_qubit(sv, 2)
    recovered_bit = rec
    success = recovered_bit == bit
    ops[10]["label"] = f"Bob: 観測 → {recovered_bit} ({'✓' if success else '✗'})"
    _mark_op(10, "done")
    yield _snap(
        STEP_BOB_MEASURE,
        f"Bob 観測: q2={recovered_bit} — 転送{'成功 ✓' if success else '失敗 ✗'} (入力={bit})",
        f"[{bit_index:04d}/{total_bits}] BOB_MEASURE | q2→{recovered_bit} | {'SUCCESS ✓' if success else 'ERROR ✗'} (input={bit})",
        PHASE_BOB,
    )

    # ─── ステップ 11: COMPLETE ──────────────────────────────────────
    for op in ops:
        op["status"] = "done"
    yield _snap(
        STEP_COMPLETE,
        f"ビット {bit_index} 完了: {bit} → {recovered_bit} | 文字 '{current_char}'",
        f"[{bit_index:04d}/{total_bits}] COMPLETE | {bit}→{recovered_bit} | {'OK' if success else 'ERR'}",
        PHASE_COMPLETE,
    )


# ─── 瞬時モード ──────────────────────────────────────────────────────────────

def teleport_bit_instant(bit: int) -> dict:
    """
    1ビットをアニメーションなしで高速テレポーテーション。
    結果のみ返す。
    """
    N = 3
    sv = Statevector.from_label("000")

    if bit == 1:
        sv = _apply(sv, _qc1(N, "x", 0))
    sv = _apply(sv, _qc1(N, "h", 1))
    sv = _apply(sv, _qc1(N, "cx", 1, 2))
    sv = _apply(sv, _qc1(N, "cx", 0, 1))
    sv = _apply(sv, _qc1(N, "h", 0))

    c0, sv = measure_qubit(sv, 0)
    c1, sv = measure_qubit(sv, 1)

    if c1 == 1:
        sv = _apply(sv, _qc1(N, "x", 2))
    if c0 == 1:
        sv = _apply(sv, _qc1(N, "z", 2))

    recovered, _ = measure_qubit(sv, 2)

    return {
        "input_bit": bit,
        "classical_bits": [c0, c1],
        "recovered_bit": recovered,
        "success": recovered == bit,
    }


def teleport_text_instant(text: str) -> dict:
    """
    テキスト全体を瞬時テレポーテーション。
    中間可視化なし、結果のみ返す。
    """
    from .encoding import text_to_bits, bits_to_text, text_to_bit_info

    bits = text_to_bits(text)
    recovered_bits: list[int] = []
    all_results: list[dict] = []
    success_count = 0

    for i, b in enumerate(bits):
        result = teleport_bit_instant(b)
        recovered_bits.append(result["recovered_bit"])
        all_results.append(result)
        if result["success"]:
            success_count += 1

    recovered_text = bits_to_text(recovered_bits)
    success_rate = success_count / len(bits) if bits else 1.0
    bit_info = text_to_bit_info(text)

    return {
        "original_text": text,
        "recovered_text": recovered_text,
        "total_bits": len(bits),
        "success_count": success_count,
        "success_rate": round(success_rate, 4),
        "bit_info": bit_info,
        "bit_results": all_results,
    }


# ─── ステップ総数の計算 ──────────────────────────────────────────────────────

def compute_total_steps(text: str) -> int:
    """テキスト全体のテレポーテーション総ステップ数を計算"""
    from .encoding import text_to_bits
    total_bits = len(text_to_bits(text))
    return total_bits * STEPS_PER_BIT


def compute_step_delay_ms(
    text: str,
    target_duration_ms: float = 10000.0,
    min_delay_ms: float = 10.0,
) -> float:
    """目標所要時間と総ステップ数からステップ間隔(ms)を計算"""
    total_steps = compute_total_steps(text)
    if total_steps <= 0:
        return min_delay_ms
    delay = target_duration_ms / total_steps
    return max(min_delay_ms, delay)
