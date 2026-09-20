"""
routes.py — REST API エンドポイント

ユーザー管理・ルーム管理・瞬時送信モードのAPIを提供する。
ゆっくり再生モードは WebSocket エンドポイントで処理。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

import store
from models.schemas import (
    UserCreateRequest,
    UserResponse,
    RoomCreateRequest,
    RoomResponse,
    SendMessageRequest,
    MessageResponse,
)
from core.quantum_engine import teleport_text_instant

router = APIRouter(prefix="/api", tags=["quantum-chat"])


# ─── ユーザー API ─────────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse, summary="ユーザー登録・ID発行")
async def create_user(req: UserCreateRequest):
    """
    新しいユーザーを作成してランダムIDを発行する。
    発行されたIDを使って他のユーザーを検索・チャットができる。
    """
    user = store.create_user(name=req.name.strip())
    return user.to_dict()


@router.get("/users/{user_id}", response_model=UserResponse, summary="ユーザー情報取得")
async def get_user(user_id: str):
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"ユーザー '{user_id}' が見つかりません")
    return user.to_dict(include_rooms=True)


@router.get("/users", summary="ユーザー検索")
async def search_users(
    q: str = Query(default="", description="検索クエリ（ID または 名前）"),
    exclude: Optional[str] = Query(default=None, description="除外するユーザーID（自分自身）"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    ユーザーIDまたは表示名でユーザーを検索する。
    クエリなしの場合は全ユーザーを返す。
    """
    users = store.search_users(query=q, exclude_id=exclude, limit=limit)
    return {
        "users": [u.to_dict() for u in users],
        "count": len(users),
    }


# ─── ルーム API ───────────────────────────────────────────────────────────────

@router.post("/rooms", response_model=RoomResponse, summary="トークルーム作成")
async def create_room(req: RoomCreateRequest):
    """
    2ユーザー間のトークルームを作成する。
    既存のルームがあれば既存のものを返す。
    """
    # 両ユーザーの存在確認
    for uid in [req.user_id_a, req.user_id_b]:
        if not store.get_user(uid):
            raise HTTPException(status_code=404, detail=f"ユーザー '{uid}' が見つかりません")

    if req.user_id_a == req.user_id_b:
        raise HTTPException(status_code=400, detail="自分自身とはルームを作成できません")

    # 既存ルームチェック
    existing = store.find_room_between(req.user_id_a, req.user_id_b)
    if existing:
        return existing.to_dict()

    room = store.create_room(user_ids=[req.user_id_a, req.user_id_b])
    return room.to_dict()


@router.get("/rooms/{room_id}", response_model=RoomResponse, summary="ルーム情報取得")
async def get_room(room_id: str):
    room = store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"ルーム '{room_id}' が見つかりません")
    return room.to_dict()


@router.get("/rooms/{room_id}/messages", summary="メッセージ履歴取得")
async def get_messages(
    room_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    room = store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"ルーム '{room_id}' が見つかりません")

    messages = room.messages[offset: offset + limit]
    return {
        "room_id": room_id,
        "messages": [m.to_dict() for m in messages],
        "total": len(room.messages),
        "offset": offset,
        "limit": limit,
    }


@router.get("/rooms", summary="ルーム一覧取得")
async def get_user_rooms(user_id: str | None = Query(default=None, description="ユーザーID（省略時は全ルーム）")):
    if user_id:
        user = store.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"ユーザー '{user_id}' が見つかりません")
        rooms = store.get_user_rooms(user_id)
    else:
        rooms = store.get_all_rooms()

    return {
        "user_id": user_id,
        "rooms": [r.to_dict() for r in rooms],
        "count": len(rooms),
    }


# ─── 瞬時送信モード ──────────────────────────────────────────────────────────

@router.post("/rooms/{room_id}/send", summary="瞬時送信モード（REST API）")
async def send_message_instant(room_id: str, req: SendMessageRequest):
    """
    量子テレポーテーション瞬時送信モード。
    中間アニメーションなしで即座にメッセージを転送し、結果を返す。
    
    実際の量子テレポーテーション回路を全ビット実行するが、
    WebSocket ストリーミングは行わない。
    """
    room = store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"ルーム '{room_id}' が見つかりません")

    sender = store.get_user(req.sender_id)
    if not sender:
        raise HTTPException(status_code=404, detail=f"ユーザー '{req.sender_id}' が見つかりません")

    if req.sender_id not in room.user_ids:
        raise HTTPException(status_code=403, detail="このルームへのアクセス権がありません")

    if room.is_teleporting:
        raise HTTPException(status_code=409, detail="現在他のメッセージが転送中です。しばらくお待ちください。")

    # 量子テレポーテーション実行（全ビット一括）
    room.is_teleporting = True
    try:
        result = teleport_text_instant(req.text)
    finally:
        room.is_teleporting = False

    # メッセージ保存
    msg = store.add_message(
        room_id=room_id,
        sender_id=req.sender_id,
        original_text=result["original_text"],
        recovered_text=result["recovered_text"],
        total_bits=result["total_bits"],
        success_rate=result["success_rate"],
        mode="instant",
    )

    return {
        "message": msg.to_dict() if msg else None,
        "teleport_result": {
            "original_text": result["original_text"],
            "recovered_text": result["recovered_text"],
            "total_bits": result["total_bits"],
            "success_rate": result["success_rate"],
            "bit_info": result["bit_info"],
        },
    }


# ─── システム情報 ─────────────────────────────────────────────────────────────

@router.get("/system/stats", summary="システム統計")
async def get_stats():
    """現在のインメモリDBの統計情報"""
    all_users = store.get_all_users()
    return {
        "total_users": len(all_users),
        "users": [u.to_dict() for u in all_users],
    }
