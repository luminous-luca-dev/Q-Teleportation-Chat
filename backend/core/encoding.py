"""
encoding.py — テキスト ↔ ビット列 変換モジュール
UTF-8フル対応（ASCII/日本語/絵文字など全て処理可能）
"""
from __future__ import annotations


# ─── テキスト → ビット列 ─────────────────────────────────────────────────────

def text_to_bits(text: str) -> list[int]:
    """
    テキストをUTF-8バイト列に変換し、ビット列として返す（MSBファースト）。
    
    例) "A"  → b'\x41' → [0,1,0,0,0,0,0,1]
        "あ" → b'\xe3\x81\x82' → [1,1,1,0,0,0,1,1, 1,0,0,0,0,0,0,1, 1,0,0,0,0,0,1,0]
    """
    bits: list[int] = []
    for byte in text.encode("utf-8"):
        for i in range(7, -1, -1):  # bit7(MSB) → bit0(LSB)
            bits.append((byte >> i) & 1)
    return bits


def bits_to_text(bits: list[int]) -> str:
    """
    ビット列をUTF-8テキストに復元する。
    長さが8の倍数でない場合は末尾をゼロパディング。
    UTF-8として無効なバイト列は '?' に置換。
    """
    # 8の倍数になるようにパディング
    remainder = len(bits) % 8
    if remainder != 0:
        bits = list(bits) + [0] * (8 - remainder)

    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | int(bits[i + j])
        byte_array.append(byte)

    return byte_array.decode("utf-8", errors="replace")


# ─── 可視化用の詳細情報 ──────────────────────────────────────────────────────

def text_to_bit_info(text: str) -> dict:
    """
    テキストのビット変換詳細情報を返す（フロントエンド可視化用）。
    
    Returns:
        {
            "text": str,
            "total_bits": int,
            "bits": list[int],
            "chars": [
                {
                    "char": str,
                    "utf8_hex": str,       # 例: "E3 81 82"
                    "utf8_bytes": list[int],
                    "bits": list[int],
                    "bit_start": int,      # グローバルビット列上の開始インデックス
                    "bit_end": int,
                    "byte_count": int,
                },
                ...
            ]
        }
    """
    chars_info = []
    all_bits: list[int] = []

    for char in text:
        byte_seq = char.encode("utf-8")
        char_bits: list[int] = []
        for byte in byte_seq:
            for i in range(7, -1, -1):
                char_bits.append((byte >> i) & 1)

        start_idx = len(all_bits)
        all_bits.extend(char_bits)

        chars_info.append({
            "char": char,
            "utf8_hex": " ".join(f"{b:02X}" for b in byte_seq),
            "utf8_bytes": list(byte_seq),
            "bits": char_bits,
            "bit_start": start_idx,
            "bit_end": start_idx + len(char_bits) - 1,
            "byte_count": len(byte_seq),
        })

    return {
        "text": text,
        "total_bits": len(all_bits),
        "bits": all_bits,
        "chars": chars_info,
    }


def bit_index_to_char_info(bit_index: int, chars_info: list[dict]) -> dict:
    """
    グローバルビットインデックスから、対応する文字情報を返す。
    """
    for i, char_info in enumerate(chars_info):
        if char_info["bit_start"] <= bit_index <= char_info["bit_end"]:
            local_idx = bit_index - char_info["bit_start"]
            return {
                "char_index": i,
                "char": char_info["char"],
                "local_bit_index": local_idx,
                "bit_in_byte": local_idx % 8,
                "byte_in_char": local_idx // 8,
            }
    return {"char_index": -1, "char": "", "local_bit_index": -1}


# ─── ビット列の表示用フォーマット ────────────────────────────────────────────

def format_bits_grouped(bits: list[int], group_size: int = 8) -> str:
    """ビット列をグループ分けして文字列化 例) '01000001 01000010'"""
    s = "".join(str(b) for b in bits)
    groups = [s[i:i + group_size] for i in range(0, len(s), group_size)]
    return " ".join(groups)


def bits_to_hex(bits: list[int]) -> str:
    """ビット列を16進数文字列に変換 例) '41 42'"""
    remainder = len(bits) % 8
    if remainder != 0:
        bits = list(bits) + [0] * (8 - remainder)
    hexes = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | int(bits[i + j])
        hexes.append(f"{byte:02X}")
    return " ".join(hexes)
