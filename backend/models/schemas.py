"""
schemas.py — Pydantic スキーマ定義
REST API のリクエスト/レスポンス型
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ─── ユーザー ─────────────────────────────────────────────────────────────────

class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=32, description="表示名")


class UserResponse(BaseModel):
    user_id: str
    name: str
    created_at: str


# ─── ルーム ───────────────────────────────────────────────────────────────────

class RoomCreateRequest(BaseModel):
    user_id_a: str = Field(..., description="作成者のユーザーID")
    user_id_b: str = Field(..., description="招待するユーザーID")


class RoomResponse(BaseModel):
    room_id: str
    user_ids: list[str]
    message_count: int
    created_at: str
    is_teleporting: bool


# ─── メッセージ送信（瞬時モード用REST API）──────────────────────────────────

class SendMessageRequest(BaseModel):
    sender_id: str = Field(..., description="送信者ユーザーID")
    text: str = Field(..., min_length=1, max_length=500, description="送信テキスト")
    target_duration_ms: float = Field(
        default=10000.0,
        ge=0.0,
        description="スロー再生モードの目標所要時間(ms)。瞬時モードでは無視。",
    )


class MessageResponse(BaseModel):
    message_id: str
    sender_id: str
    original_text: str
    recovered_text: str
    total_bits: int
    success_rate: float
    mode: str
    created_at: str


# ─── WebSocket メッセージ（型定義のドキュメント用）──────────────────────────

class WSClientMessage(BaseModel):
    """クライアント → サーバー WebSocket メッセージの型"""
    type: str  # "send_message" | "set_speed" | "ping"


class WSSendMessage(BaseModel):
    """type="send_message" の場合の追加フィールド"""
    type: str = "send_message"
    text: str
    mode: str = "instant"  # "instant" | "slow"
    target_duration_ms: float = 10000.0  # スロー再生の目標所要時間(ms)


class WSSetSpeed(BaseModel):
    """type="set_speed" の場合の追加フィールド"""
    type: str = "set_speed"
    target_duration_ms: float  # 残り時間で再計算する


# ─── テレポーテーション設定 ──────────────────────────────────────────────────

class TeleportConfig(BaseModel):
    target_duration_ms: float = Field(
        default=10000.0,
        ge=100.0,
        description="スロー再生モードの目標所要時間 (ミリ秒)",
    )
    min_step_delay_ms: float = Field(
        default=10.0,
        ge=1.0,
        description="ステップ間の最小遅延 (ミリ秒)",
    )

    def compute_step_delay(self, total_steps: int) -> float:
        """総ステップ数から1ステップあたりの遅延を計算"""
        if total_steps <= 0:
            return self.min_step_delay_ms
        delay = self.target_duration_ms / total_steps
        return max(self.min_step_delay_ms, delay)
