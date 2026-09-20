# -*- coding: utf-8 -*-
"""
test_teleport.py — 量子テレポーテーションロジックの単体テスト

実行:
  cd quantum_chat/backend
  python -m pytest tests/test_teleport.py -v
  または:
  python tests/test_teleport.py
"""
import sys
import os

# パス設定 (backend/ をルートに追加)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.encoding import (
    text_to_bits, bits_to_text, text_to_bit_info,
    format_bits_grouped, bits_to_hex,
)
from core.quantum_engine import (
    teleport_bit_instant, teleport_text_instant,
    teleport_bit_steps, compute_step_delay_ms, compute_total_steps,
    STEPS_PER_BIT,
)


# ─── encoding テスト ─────────────────────────────────────────────────────────

class TestEncoding:

    def test_ascii_roundtrip(self):
        """ASCIIテキストのビット変換往復テスト"""
        for text in ["A", "Hello", "Hello World!", "0123456789"]:
            bits = text_to_bits(text)
            recovered = bits_to_text(bits)
            assert recovered == text, f"往復失敗: '{text}' → '{recovered}'"

    def test_japanese_roundtrip(self):
        """日本語テキストのビット変換往復テスト"""
        for text in ["あ", "こんにちは", "量子コンピュータ", "日本語テスト123"]:
            bits = text_to_bits(text)
            recovered = bits_to_text(bits)
            assert recovered == text, f"日本語往復失敗: '{text}' → '{recovered}'"

    def test_emoji_roundtrip(self):
        """絵文字のビット変換往復テスト (4バイトUTF-8)"""
        text = "Hello 🌟"
        bits = text_to_bits(text)
        recovered = bits_to_text(bits)
        assert recovered == text

    def test_bit_count_ascii(self):
        """ASCII文字のビット数確認 (1文字 = 8ビット)"""
        bits = text_to_bits("A")
        assert len(bits) == 8
        # 'A' = 0x41 = 01000001
        assert bits == [0, 1, 0, 0, 0, 0, 0, 1]

    def test_bit_count_japanese(self):
        """日本語文字のビット数確認 ('あ' = 3バイト = 24ビット)"""
        bits = text_to_bits("あ")
        assert len(bits) == 24

    def test_bit_info_structure(self):
        """text_to_bit_info の構造確認"""
        info = text_to_bit_info("Hi")
        assert info["text"] == "Hi"
        assert info["total_bits"] == 16  # 2文字 × 8ビット
        assert len(info["chars"]) == 2
        assert info["chars"][0]["char"] == "H"
        assert info["chars"][0]["bit_start"] == 0
        assert info["chars"][0]["bit_end"] == 7
        assert info["chars"][1]["char"] == "i"
        assert info["chars"][1]["bit_start"] == 8
        assert info["chars"][1]["bit_end"] == 15

    def test_empty_text(self):
        """空文字列の処理"""
        bits = text_to_bits("")
        assert bits == []
        text = bits_to_text([])
        assert text == ""

    def test_format_bits(self):
        """ビット列フォーマット"""
        bits = text_to_bits("A")
        formatted = format_bits_grouped(bits)
        assert formatted == "01000001"

    def test_bits_to_hex(self):
        """ビット列16進数変換"""
        bits = text_to_bits("A")
        assert bits_to_hex(bits) == "41"


# ─── quantum_engine テスト ───────────────────────────────────────────────────

class TestTeleportBitInstant:

    def test_teleport_0(self):
        """ビット0のテレポーテーション"""
        result = teleport_bit_instant(0)
        assert result["input_bit"] == 0
        assert result["recovered_bit"] == 0, "ビット0が正しく転送されなかった"
        assert result["success"] is True

    def test_teleport_1(self):
        """ビット1のテレポーテーション"""
        result = teleport_bit_instant(1)
        assert result["input_bit"] == 1
        assert result["recovered_bit"] == 1, "ビット1が正しく転送されなかった"
        assert result["success"] is True

    def test_classical_bits_range(self):
        """古典ビット (c0, c1) が 0 or 1 であること"""
        for _ in range(20):
            result = teleport_bit_instant(0)
            c0, c1 = result["classical_bits"]
            assert c0 in [0, 1]
            assert c1 in [0, 1]

    def test_multiple_runs_always_succeed(self):
        """複数回実行して全て成功することを確認 (量子テレポーテーションは決定論的に成功)"""
        n_trials = 50
        for bit in [0, 1]:
            success_count = sum(
                1 for _ in range(n_trials)
                if teleport_bit_instant(bit)["success"]
            )
            assert success_count == n_trials, (
                f"ビット{bit}: {n_trials}回中{success_count}回成功 (100%期待)"
            )


class TestTeleportTextInstant:

    def test_ascii_text(self):
        """ASCII テキストのテレポーテーション往復"""
        for text in ["Hi", "Hello", "Test 123"]:
            result = teleport_text_instant(text)
            assert result["recovered_text"] == text, (
                f"'{text}' → '{result['recovered_text']}'"
            )
            assert result["success_rate"] == 1.0

    def test_japanese_text(self):
        """日本語テキストのテレポーテーション往復"""
        for text in ["あ", "こんにちは"]:
            result = teleport_text_instant(text)
            assert result["recovered_text"] == text, (
                f"'{text}' → '{result['recovered_text']}'"
            )

    def test_total_bits_calculation(self):
        """総ビット数の計算確認"""
        result = teleport_text_instant("A")
        assert result["total_bits"] == 8

        result = teleport_text_instant("AB")
        assert result["total_bits"] == 16

    def test_bit_info_included(self):
        """bit_info が含まれていること"""
        result = teleport_text_instant("Hi")
        assert "bit_info" in result
        assert result["bit_info"]["total_bits"] == 16


class TestTeleportBitSteps:

    def test_step_count(self):
        """1ビットのステップ数確認"""
        steps = list(teleport_bit_steps(0, 0, 8, 0, "A"))
        assert len(steps) == STEPS_PER_BIT

    def test_step_ids_sequence(self):
        """ステップIDの順序確認"""
        from core.quantum_engine import (
            STEP_INIT, STEP_ENCODE, STEP_BELL_H, STEP_BELL_CNOT,
            STEP_ALICE_CNOT, STEP_ALICE_H, STEP_ALICE_MEASURE,
            STEP_CLASSICAL_SEND, STEP_BOB_X, STEP_BOB_Z,
            STEP_BOB_MEASURE, STEP_COMPLETE,
        )
        expected_ids = [
            STEP_INIT, STEP_ENCODE, STEP_BELL_H, STEP_BELL_CNOT,
            STEP_ALICE_CNOT, STEP_ALICE_H, STEP_ALICE_MEASURE,
            STEP_CLASSICAL_SEND, STEP_BOB_X, STEP_BOB_Z,
            STEP_BOB_MEASURE, STEP_COMPLETE,
        ]
        steps = list(teleport_bit_steps(1, 0, 8, 0, "A"))
        actual_ids = [s.step_id for s in steps]
        assert actual_ids == expected_ids

    def test_statevector_structure(self):
        """各ステップの状態ベクトルが8成分 (2³) であること"""
        for step in teleport_bit_steps(0, 0, 8, 0, "A"):
            assert len(step.amplitudes) == 8, f"step {step.step_id}: 振幅数={len(step.amplitudes)}"
            for amp in step.amplitudes:
                assert "label" in amp
                assert "real" in amp
                assert "imag" in amp
                assert "prob" in amp

    def test_bloch_vectors_structure(self):
        """各ステップのブロッホベクトルが3量子ビット分あること"""
        for step in teleport_bit_steps(1, 0, 8, 0, "A"):
            assert len(step.bloch_vectors) == 3
            for bv in step.bloch_vectors:
                assert "x" in bv and "y" in bv and "z" in bv and "r" in bv
                # ブロッホベクトルの大きさは1以下
                assert bv["r"] <= 1.01, f"r={bv['r']} > 1 (ありえない値)"

    def test_init_state_is_000(self):
        """初期化ステップで状態が |000⟩ であること"""
        steps = list(teleport_bit_steps(0, 0, 8, 0, "A"))
        init_step = steps[0]
        # |000⟩ → インデックス0の確率=1.0、他は0
        probs = [a["prob"] for a in init_step.amplitudes]
        assert abs(probs[0] - 1.0) < 1e-6, f"初期状態の|000⟩確率={probs[0]} (1.0期待)"
        for p in probs[1:]:
            assert p < 1e-6, f"初期状態の非|000⟩確率={p} (0期待)"

    def test_encode_bit1_flips_q0(self):
        """bit=1のエンコードステップで q0 が |1⟩ になること"""
        steps = list(teleport_bit_steps(1, 0, 8, 0, "A"))
        encode_step = steps[1]
        # q0=|1⟩ → インデックス1の確率=1.0 (Qiskit little-endian: bit0=LSB)
        probs = [a["prob"] for a in encode_step.amplitudes]
        assert abs(probs[1] - 1.0) < 1e-6, f"bit=1エンコード後: |001⟩確率={probs[1]} (1.0期待)"

    def test_bell_state_entanglement(self):
        """ベル対生成後、q1とq2がエンタングル (r<1) になること"""
        steps = list(teleport_bit_steps(0, 0, 8, 0, "A"))
        bell_cnot_step = steps[3]  # STEP_BELL_CNOT
        # q1とq2のブロッホベクトルは混合状態 (r < 1)
        bv_q1 = bell_cnot_step.bloch_vectors[1]
        bv_q2 = bell_cnot_step.bloch_vectors[2]
        assert bv_q1["r"] < 0.5, f"q1のBloch半径r={bv_q1['r']} (エンタングル後は<<1期待)"
        assert bv_q2["r"] < 0.5, f"q2のBloch半径r={bv_q2['r']} (エンタングル後は<<1期待)"

    def test_teleport_succeeds_in_steps(self):
        """ステップジェネレーターの最終ステップで転送成功していること"""
        for bit in [0, 1]:
            steps = list(teleport_bit_steps(bit, 0, 8, 0, "A"))
            last = steps[-1]
            assert last.recovered_bit == bit, (
                f"bit={bit}: 最終ステップで recovered_bit={last.recovered_bit}"
            )

    def test_classical_bits_set_after_measure(self):
        """Alice観測後に古典ビットが設定されること"""
        from core.quantum_engine import STEP_ALICE_MEASURE
        for step in teleport_bit_steps(0, 0, 8, 0, "A"):
            if step.step_id == STEP_ALICE_MEASURE:
                assert step.classical_bits[0] in [0, 1]
                assert step.classical_bits[1] in [0, 1]
                break
        else:
            pytest.fail("ALICE_MEASUREステップが見つからない")

    def test_to_dict_serializable(self):
        """to_dict() が JSON シリアライズ可能であること"""
        import json
        for step in teleport_bit_steps(1, 3, 8, 0, "A"):
            d = step.to_dict()
            json_str = json.dumps(d)  # シリアライズ失敗なら例外
            assert len(json_str) > 0


class TestSpeedControl:

    def test_step_delay_calculation(self):
        """ステップ遅延の計算確認"""
        # "A" = 8ビット × 12ステップ = 96ステップ
        # target=10000ms → delay = 10000/96 ≈ 104ms
        delay = compute_step_delay_ms("A", target_duration_ms=10000.0)
        total_steps = compute_total_steps("A")
        expected = 10000.0 / total_steps
        assert abs(delay - expected) < 1.0

    def test_min_delay_enforced(self):
        """最小遅延が enforced されること"""
        # 非常に長いテキストでも最小遅延以下にはならない
        delay = compute_step_delay_ms("A" * 1000, target_duration_ms=1.0, min_delay_ms=10.0)
        assert delay >= 10.0

    def test_total_steps_japanese(self):
        """日本語テキストの総ステップ数確認"""
        # "あ" = 3バイト = 24ビット → 24 × 12 = 288ステップ
        total = compute_total_steps("あ")
        assert total == 24 * STEPS_PER_BIT


# ─── メイン実行 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("量子テレポーテーション バックエンド 単体テスト")
    print("=" * 60)

    # pytest を使わず直接実行する場合
    import traceback

    test_classes = [
        TestEncoding,
        TestTeleportBitInstant,
        TestTeleportTextInstant,
        TestTeleportBitSteps,
        TestSpeedControl,
    ]

    total = 0
    passed = 0
    failed = 0

    for cls in test_classes:
        print(f"\n[{cls.__name__}]")
        instance = cls()
        methods = [m for m in dir(cls) if m.startswith("test_")]
        for method_name in methods:
            total += 1
            try:
                getattr(instance, method_name)()
                print(f"  PASS: {method_name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL: {method_name}: {e}")
                traceback.print_exc()
                failed += 1

    print("\n" + "=" * 60)
    print(f"結果: {passed}/{total} 成功 | {failed} 失敗")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
