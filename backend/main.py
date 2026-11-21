"""
main.py — FastAPI アプリケーション エントリポイント

起動コマンド:
  cd quantum_chat/backend
  uvicorn main:app --reload --host 0.0.0.0 --port 8000

API ドキュメント:
  http://localhost:8000/docs   (Swagger UI)
  http://localhost:8000/redoc  (ReDoc)

WebSocket:
  ws://localhost:8000/ws/{room_id}/{user_id}
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

import store
from api.routes import router as api_router
from api.websocket import websocket_endpoint

# ─── ログ設定 ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── ライフサイクル ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  量子テレポーテーション チャットシミュレータ — バックエンド起動")
    logger.info("  Quantum Teleportation Chat Simulator Backend v1.0")
    logger.info("=" * 60)

    # 開発用デモユーザー作成
    alice = store.create_user("Alice")
    bob = store.create_user("Bob")
    demo_room = store.create_room([alice.user_id, bob.user_id])
    logger.info(f"  デモユーザー作成: Alice={alice.user_id}, Bob={bob.user_id}")
    logger.info(f"  デモルーム作成:   room_id={demo_room.room_id}")
    logger.info("  API Docs: http://localhost:8000/docs")
    logger.info("=" * 60)

    yield

    logger.info("バックエンド シャットダウン")


# ─── FastAPI アプリ ───────────────────────────────────────────────────────────

app = FastAPI(
    title="量子テレポーテーション チャットシミュレータ",
    description="""
## Quantum Teleportation Chat Simulator API

テキストメッセージを量子テレポーテーション回路（Qiskit AerSimulator）を介して
シミュレーション転送するチャットアプリのバックエンド。

### 通信モード
- **瞬時送信モード**: REST API で即座に転送、アニメーションなし
- **ゆっくり再生モード**: WebSocket で1ゲートずつストリーミング

### 量子テレポーテーション手順
1. テキスト → UTF-8 → ビット列
2. 各ビット → 量子状態 |0⟩ or |1⟩
3. ベル対生成 (H + CNOT)
4. Alice 回路 (CNOT + H + 観測)
5. 古典通信 (c0, c1 送信)
6. Bob 補正 (X^c1 Z^c0)
7. Bob 観測 → ビット復元
8. ビット列 → テキスト
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS 設定 ────────────────────────────────────────────────────────────────

allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()] if allowed_origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ルーター登録 ─────────────────────────────────────────────────────────────

app.include_router(api_router)

# ─── WebSocket エンドポイント ─────────────────────────────────────────────────

@app.websocket("/ws/{room_id}/{user_id}")
async def ws_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    """
    リアルタイム通信エンドポイント。
    
    - room_id: トークルームID (例: RABCD123456)
    - user_id: ユーザーID (例: ABCD1234)
    
    接続後、クライアントは JSON メッセージを送受信できる。
    詳細は websocket.py のドキュメントを参照。
    """
    await websocket_endpoint(websocket, room_id, user_id)


# ─── ヘルスチェック ───────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health_check():
    """サーバーの稼働状態確認"""
    return {
        "status": "ok",
        "service": "quantum-chat-backend",
        "version": "1.0.0",
        "total_users": len(store.get_all_users()),
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "量子テレポーテーション チャットシミュレータ API",
        "docs": "/docs",
        "health": "/health",
        "websocket": "ws://{host}/ws/{room_id}/{user_id}",
    }
