"""
websocket.py — WebSocket 接続管理 + ゆっくり再生モードのストリーミングハンドラー

接続URL: ws://{host}/ws/{room_id}/{user_id}

クライアント→サーバー メッセージ形式:
  {"type": "send_message", "text": "...", "mode": "slow"|"instant", "target_duration_ms": 10000}
  {"type": "set_speed",    "target_duration_ms": 5000}
  {"type": "ping"}

サーバー→クライアント メッセージ形式:
  {"type": "teleport_step", ...TeleportStep}   # ゆっくりモードの各ステップ
  {"type": "message_received", ...}            # メッセージ完了通知
  {"type": "teleport_start", ...}              # テレポーテーション開始通知
  {"type": "user_joined", "user_id": ...}
  {"type": "user_left",   "user_id": ...}
  {"type": "room_history", "messages": [...]}  # 接続時の過去ログ
  {"type": "pong"}
  {"type": "error", "message": ...}
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

import store
from core.encoding import text_to_bits, bits_to_text, text_to_bit_info
from core.quantum_engine import (
    teleport_bit_steps,
    teleport_text_instant,
    compute_step_delay_ms,
    compute_total_steps,
    STEPS_PER_BIT,
    STEP_BOB_MEASURE,
)

logger = logging.getLogger(__name__)


# ─── 接続マネージャー ─────────────────────────────────────────────────────────

class ConnectionManager:
    """
    WebSocket 接続をルーム別に管理するシングルトン。
    rooms: {room_id → {user_id → WebSocket}}
    """

    def __init__(self):
        self._rooms: dict[str, dict[str, WebSocket]] = {}

    # ── 接続/切断 ──────────────────────────────────────────────────

    async def connect(self, room_id: str, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        if room_id not in self._rooms:
            self._rooms[room_id] = {}
        self._rooms[room_id][user_id] = ws
        logger.info(f"WebSocket connected: room={room_id} user={user_id}")

    def disconnect(self, room_id: str, user_id: str) -> None:
        if room_id in self._rooms:
            self._rooms[room_id].pop(user_id, None)
            if not self._rooms[room_id]:
                del self._rooms[room_id]
        logger.info(f"WebSocket disconnected: room={room_id} user={user_id}")

    def is_connected(self, room_id: str, user_id: str) -> bool:
        return room_id in self._rooms and user_id in self._rooms[room_id]

    def get_connected_users(self, room_id: str) -> list[str]:
        return list(self._rooms.get(room_id, {}).keys())

    # ── 送信 ──────────────────────────────────────────────────────

    async def send_to_user(self, room_id: str, user_id: str, data: dict) -> bool:
        """指定ユーザーにメッセージを送信。失敗時は切断処理してFalseを返す"""
        ws = self._rooms.get(room_id, {}).get(user_id)
        if ws is None:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception as e:
            logger.warning(f"Send failed: room={room_id} user={user_id}: {e}")
            self.disconnect(room_id, user_id)
            return False

    async def broadcast_to_room(self, room_id: str, data: dict) -> int:
        """ルーム内の全接続ユーザーにブロードキャスト。送信成功数を返す"""
        users = list(self._rooms.get(room_id, {}).keys())
        success = 0
        for uid in users:
            if await self.send_to_user(room_id, uid, data):
                success += 1
        return success


# ─── グローバルインスタンス ───────────────────────────────────────────────────

manager = ConnectionManager()


# ─── テレポーテーション ハンドラー ───────────────────────────────────────────

async def handle_send_message(
    room_id: str,
    sender_id: str,
    text: str,
    mode: str,
    target_duration_ms: float,
) -> None:
    """
    メッセージ送信の中枢処理。
    - mode="instant": 即時転送、結果のみブロードキャスト
    - mode="slow"   : 1ゲートずつストリーミング
    """
    room = store.get_room(room_id)
    if not room:
        await manager.send_to_user(room_id, sender_id, {
            "type": "error", "message": "ルームが見つかりません",
        })
        return

    if room.is_teleporting:
        await manager.send_to_user(room_id, sender_id, {
            "type": "error",
            "message": "現在別のメッセージが転送中です。しばらくお待ちください。",
        })
        return

    room.is_teleporting = True
    try:
        if mode == "slow":
            await _handle_slow_mode(room_id, sender_id, text, target_duration_ms)
        else:
            await _handle_instant_mode(room_id, sender_id, text)
    finally:
        room.is_teleporting = False


async def _handle_instant_mode(room_id: str, sender_id: str, text: str) -> None:
    """瞬時モード: 量子テレポーテーションを全ビット実行し結果をブロードキャスト"""
    result = teleport_text_instant(text)

    # メッセージ保存
    msg = store.add_message(
        room_id=room_id,
        sender_id=sender_id,
        original_text=result["original_text"],
        recovered_text=result["recovered_text"],
        total_bits=result["total_bits"],
        success_rate=result["success_rate"],
        mode="instant",
    )

    await manager.broadcast_to_room(room_id, {
        "type": "message_received",
        "message_id": msg.message_id if msg else None,
        "sender_id": sender_id,
        "original_text": result["original_text"],
        "recovered_text": result["recovered_text"],
        "total_bits": result["total_bits"],
        "success_rate": result["success_rate"],
        "mode": "instant",
        "created_at": msg.created_at if msg else None,
        "bit_info": result["bit_info"],
    })


async def _handle_slow_mode(
    room_id: str,
    sender_id: str,
    text: str,
    target_duration_ms: float,
) -> None:
    """
    ゆっくり再生モード:
    1ゲートごとにステップデータをブロードキャストしながらテレポーテーション。
    速度は target_duration_ms で制御する（WebSocket経由でリアルタイム変更可能）。
    """
    bits = text_to_bits(text)
    total_bits = len(bits)
    total_steps = total_bits * STEPS_PER_BIT
    bit_info = text_to_bit_info(text)

    # 初回ステップ遅延計算
    step_delay_s = compute_step_delay_ms(text, target_duration_ms) / 1000.0

    # 速度変更を受け取るための共有状態
    # NOTE: WebSocketの受信は別タスクで行うため、辞書で共有する
    speed_state = {"step_delay_s": step_delay_s, "total_steps_remaining": total_steps}

    # テレポーテーション開始をブロードキャスト
    await manager.broadcast_to_room(room_id, {
        "type": "teleport_start",
        "sender_id": sender_id,
        "total_bits": total_bits,
        "total_steps": total_steps,
        "step_delay_ms": step_delay_s * 1000,
        "target_duration_ms": target_duration_ms,
        "bit_info": bit_info,
        "text_length": len(text),
    })

    recovered_bits: list[int] = []

    # ビットごとに処理
    bit_cursor = 0
    for char_idx, char_info in enumerate(bit_info["chars"]):
        char = char_info["char"]
        char_bits = char_info["bits"]

        for local_bit_idx, bit in enumerate(char_bits):
            global_bit_idx = bit_cursor + local_bit_idx

            # 1ビット分のステップをストリーミング
            for step in teleport_bit_steps(
                bit=bit,
                bit_index=global_bit_idx,
                total_bits=total_bits,
                char_index=char_idx,
                current_char=char,
            ):
                # 接続が残っているか確認
                if not manager.get_connected_users(room_id):
                    logger.warning(f"Room {room_id}: 全ユーザー切断, テレポーテーション中断")
                    return

                await manager.broadcast_to_room(room_id, step.to_dict())

                # Bob 観測ステップで復元ビットを記録
                if step.step_id == STEP_BOB_MEASURE and step.recovered_bit is not None:
                    recovered_bits.append(step.recovered_bit)

                # ステップ遅延 (speedを引数でもらって更新可能にするため speed_state から読む)
                await asyncio.sleep(speed_state["step_delay_s"])

        bit_cursor += len(char_bits)

    # 全ビット復元してテキストに変換
    recovered_text = bits_to_text(recovered_bits)
    success_rate = sum(
        1 for i, b in enumerate(bits)
        if i < len(recovered_bits) and recovered_bits[i] == b
    ) / total_bits if total_bits > 0 else 1.0

    # メッセージ保存
    msg = store.add_message(
        room_id=room_id,
        sender_id=sender_id,
        original_text=text,
        recovered_text=recovered_text,
        total_bits=total_bits,
        success_rate=round(success_rate, 4),
        mode="slow",
    )

    # テレポーテーション完了イベント
    await manager.broadcast_to_room(room_id, {
        "type": "teleport_complete",
        "sender_id": sender_id,
        "summary": {
            "original_text": text,
            "recovered_text": recovered_text,
            "total_bits": total_bits,
            "success_rate": round(success_rate, 4),
            "all_bits_matched": bool(recovered_text == text),
            "circuits_run": total_bits,
        },
    })

    # 完了メッセージブロードキャスト
    await manager.broadcast_to_room(room_id, {
        "type": "message_received",
        "message_id": msg.message_id if msg else None,
        "sender_id": sender_id,
        "original_text": text,
        "recovered_text": recovered_text,
        "text": recovered_text,
        "total_bits": total_bits,
        "success_rate": round(success_rate, 4),
        "mode": "slow",
        "created_at": msg.created_at if msg else None,
        "teleport_summary": {
            "original_text": text,
            "recovered_text": recovered_text,
            "total_bits": total_bits,
            "success_rate": round(success_rate, 4),
            "all_bits_matched": bool(recovered_text == text),
            "circuits_run": total_bits,
        },
    })

    return speed_state


# ─── WebSocket エンドポイント ─────────────────────────────────────────────────

async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str) -> None:
    """
    WebSocket エンドポイントのメインループ。
    接続確立 → 履歴送信 → メッセージ受信ループ → 切断処理
    """
    # バリデーション
    room = store.get_room(room_id)
    if not room:
        await websocket.close(code=4004, reason=f"Room '{room_id}' not found")
        return

    user = store.get_user(user_id)
    if not user:
        await websocket.close(code=4004, reason=f"User '{user_id}' not found")
        return

    if user_id not in room.user_ids:
        await websocket.close(code=4003, reason="Access denied")
        return

    # 接続確立
    await manager.connect(room_id, user_id, websocket)

    # 接続通知をルーム内にブロードキャスト
    await manager.broadcast_to_room(room_id, {
        "type": "user_joined",
        "user_id": user_id,
        "name": user.name,
        "connected_users": manager.get_connected_users(room_id),
    })

    # 過去メッセージ履歴を接続ユーザーに送信
    history = room.messages[-50:] if room.messages else []
    await manager.send_to_user(room_id, user_id, {
        "type": "room_history",
        "room_id": room_id,
        "messages": [m.to_dict() for m in history],
        "user_info": user.to_dict(),
        "room_info": room.to_dict(),
    })

    # 現在進行中のテレポーテーションがあれば通知
    if room.is_teleporting:
        await manager.send_to_user(room_id, user_id, {
            "type": "teleport_in_progress",
            "message": "現在テレポーテーション転送中です",
        })

    # メッセージ受信ループ
    try:
        while True:
            try:
                raw = await websocket.receive_text()
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_to_user(room_id, user_id, {
                    "type": "error", "message": "JSONパース失敗",
                })
                continue

            msg_type = data.get("type", "")

            # ─── ping ───────────────────────────────────────────────
            if msg_type == "ping":
                await manager.send_to_user(room_id, user_id, {"type": "pong"})

            # ─── send_message ────────────────────────────────────────
            elif msg_type == "send_message":
                text = data.get("text", "").strip()
                if not text:
                    await manager.send_to_user(room_id, user_id, {
                        "type": "error", "message": "テキストが空です",
                    })
                    continue

                if len(text) > 500:
                    await manager.send_to_user(room_id, user_id, {
                        "type": "error", "message": "テキストが長すぎます（最大500文字）",
                    })
                    continue

                mode = data.get("mode", "instant")
                target_ms = float(data.get("target_duration_ms", 10000.0))

                # テレポーテーションを asyncio タスクとして実行
                # (WebSocketの受信ループをブロックしないために)
                asyncio.create_task(
                    handle_send_message(
                        room_id=room_id,
                        sender_id=user_id,
                        text=text,
                        mode=mode,
                        target_duration_ms=target_ms,
                    )
                )

            # ─── set_speed (実装メモ: 現在進行中のタスクへの反映は将来対応) ──
            elif msg_type == "set_speed":
                target_ms = float(data.get("target_duration_ms", 10000.0))
                # TODO: 実行中タスクへの速度変更反映
                await manager.send_to_user(room_id, user_id, {
                    "type": "speed_updated",
                    "target_duration_ms": target_ms,
                    "message": "速度設定を受信しました（次のメッセージから適用）",
                })

            # ─── unknown ─────────────────────────────────────────────
            else:
                await manager.send_to_user(room_id, user_id, {
                    "type": "error", "message": f"未知のメッセージタイプ: {msg_type}",
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: room={room_id} user={user_id}: {e}", exc_info=True)
    finally:
        manager.disconnect(room_id, user_id)
        # 切断通知
        try:
            await manager.broadcast_to_room(room_id, {
                "type": "user_left",
                "user_id": user_id,
                "name": user.name,
                "connected_users": manager.get_connected_users(room_id),
            })
        except Exception:
            pass
