# Multi-Model ASR Server

高速・高精度な日本語音声認識APIサーバー。
**Kotoba-Whisper** と **ReazonSpeech** の2つのモデルをサポート。

## 特徴
| モデル | 速度 (24秒音声) | パラメータ | 特徴 |
|--------|----------------|-----------|------|
| **ReazonSpeech** | ~1.6秒 | 159M | 超高速・軽量 |
| **Kotoba-Whisper** | ~6.8秒 | 1.5B | 高精度 |

---

## 使い方

### 1. サーバー起動
```
start_server.bat をダブルクリック
```

### 2. APIリクエスト

**ReazonSpeech (高速):**
```bash
curl -X POST "http://127.0.0.1:8000/openai/deployments/reazonspeech/audio/transcriptions" \
  -H "api-key: test" -F "file=@audio.mp3"
```

**Kotoba-Whisper (高精度):**
```bash
curl -X POST "http://127.0.0.1:8000/openai/deployments/whisper-1/audio/transcriptions" \
  -H "api-key: test" -F "file=@audio.mp3"
```

### 3. API仕様書
サーバー起動後、ブラウザで http://127.0.0.1:8000/docs にアクセス

---

## エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/openai/deployments/{model}/audio/transcriptions` | 音声認識 |
| GET | `/health` | ヘルスチェック & モデル一覧 |
| GET | `/docs` | Swagger UI |

### モデル名エイリアス
- `whisper-1`, `kotoba-whisper`, `kotoba` → Kotoba-Whisper
- `reazonspeech`, `reazonspeech-k2`, `reazon` → ReazonSpeech

---

## インストール
```powershell
.\setup.ps1
```

## 詳細
- [ARCHITECTURE.md](ARCHITECTURE.md) - システム設計
