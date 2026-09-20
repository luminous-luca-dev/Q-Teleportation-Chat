"""
store.py — インメモリデータストア
ユーザー・ルーム・メッセージの管理（後でDB移行予定）
"""
from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import Optional


# ─── ID生成 ──────────────────────────────────────────────────────────────────

def generate_id(length: int = 8, prefix: str = "") -> str:
    """ランダムな英数字IDを生成"""
    chars = string.ascii_uppercase + string.digits
    return prefix + "".join(random.choices(chars, k=length))


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── データモデル ─────────────────────────────────────────────────────────────

class User:
    def __init__(self, user_id: str, name: str):
        self.user_id = user_id
        self.name = name
        self.created_at = utcnow_iso()
        self.room_ids: list[str] = []

    def to_dict(self, include_rooms: bool = False) -> dict:
        d = {
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at,
        }
        if include_rooms:
            d["room_ids"] = self.room_ids
        return d


class StoredMessage:
    def __init__(
        self,
        message_id: str,
        sender_id: str,
        original_text: str,
        recovered_text: str,
        total_bits: int,
        success_rate: float,
        mode: str,
    ):
        self.message_id = message_id
        self.sender_id = sender_id
        self.original_text = original_text
        self.recovered_text = recovered_text
        self.total_bits = total_bits
        self.success_rate = success_rate
        self.mode = mode  # "instant" | "slow"
        self.created_at = utcnow_iso()

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "text": self.recovered_text,
            "original_text": self.original_text,
            "recovered_text": self.recovered_text,
            "total_bits": self.total_bits,
            "success_rate": self.success_rate,
            "mode": self.mode,
            "created_at": self.created_at,
        }


class Room:
    def __init__(self, room_id: str, user_ids: list[str]):
        self.room_id = room_id
        self.user_ids: list[str] = list(user_ids)
        self.messages: list[StoredMessage] = []
        self.created_at = utcnow_iso()
        self.is_teleporting: bool = False  # 同時テレポーテーション防止フラグ

    def to_dict(self, include_messages: bool = False) -> dict:
        d = {
            "room_id": self.room_id,
            "user_ids": self.user_ids,
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "is_teleporting": self.is_teleporting,
        }
        if include_messages:
            d["messages"] = [m.to_dict() for m in self.messages]
        return d


# ─── グローバルストア ─────────────────────────────────────────────────────────

_users: dict[str, User] = {}
_rooms: dict[str, Room] = {}


# ─── ユーザー操作 ─────────────────────────────────────────────────────────────

def create_user(name: str) -> User:
    """新規ユーザーを作成してIDを発行"""
    while True:
        user_id = generate_id(8)
        if user_id not in _users:
            break
    user = User(user_id=user_id, name=name)
    _users[user_id] = user
    return user


def get_user(user_id: str) -> Optional[User]:
    return _users.get(user_id)


def search_users(query: str, exclude_id: Optional[str] = None, limit: int = 20) -> list[User]:
    """ユーザーID・名前でファジー検索"""
    q = query.lower().strip()
    if not q:
        # クエリなし → 全ユーザー（自分を除く）
        results = [u for uid, u in _users.items() if uid != exclude_id]
        return results[:limit]

    results = []
    for uid, user in _users.items():
        if uid == exclude_id:
            continue
        if q in uid.lower() or q in user.name.lower():
            results.append(user)
        if len(results) >= limit:
            break
    return results


def get_all_users() -> list[User]:
    return list(_users.values())


# ─── ルーム操作 ───────────────────────────────────────────────────────────────

def create_room(user_ids: list[str]) -> Room:
    """トークルームを作成"""
    while True:
        room_id = generate_id(10, prefix="R")
        if room_id not in _rooms:
            break
    room = Room(room_id=room_id, user_ids=user_ids)
    _rooms[room_id] = room
    # 各ユーザーのルームリストに追加
    for uid in user_ids:
        if uid in _users:
            _users[uid].room_ids.append(room_id)
    return room


def get_room(room_id: str) -> Optional[Room]:
    return _rooms.get(room_id)


def get_user_rooms(user_id: str) -> list[Room]:
    """ユーザーが参加しているルームを全て取得"""
    user = _users.get(user_id)
    if not user:
        return []
    return [_rooms[rid] for rid in user.room_ids if rid in _rooms]


def find_room_between(user_id_a: str, user_id_b: str) -> Optional[Room]:
    """2ユーザー間の既存ルームを検索"""
    for room in _rooms.values():
        if set(room.user_ids) == {user_id_a, user_id_b}:
            return room
    return None


def get_all_rooms() -> list[Room]:
    """全ルームを取得"""
    return list(_rooms.values())


# ─── メッセージ操作 ──────────────────────────────────────────────────────────

def add_message(
    room_id: str,
    sender_id: str,
    original_text: str,
    recovered_text: str,
    total_bits: int,
    success_rate: float,
    mode: str,
) -> Optional[StoredMessage]:
    """ルームにメッセージを追加"""
    room = _rooms.get(room_id)
    if not room:
        return None
    msg_id = generate_id(12, prefix="M")
    msg = StoredMessage(
        message_id=msg_id,
        sender_id=sender_id,
        original_text=original_text,
        recovered_text=recovered_text,
        total_bits=total_bits,
        success_rate=success_rate,
        mode=mode,
    )
    room.messages.append(msg)
    return msg
