# WhisperServer (Multi-Model ASR API)

Azure OpenAI互換のAPIを提供する、高速・高精度な日本語音声認識サーバー。
**Kotoba-Whisper** (高精度) と **ReazonSpeech** (超高速) の2つのモデルをサポートし、用途に応じて切り替え可能です。

## 前提条件 (Prerequisites)

- **OS**: Windows 10/11 (推奨), WSL2, Linux
- **Python**: 3.10 以上 (3.11 推奨)
- **FFmpeg**: 
  - 必須ではありませんが、多様な音声フォーマット対応のためにインストールを推奨します。
  - Windowsの場合: `PATH` に ffmpeg.exe が通っていること。

## 特徴
| モデル | 速度 (24秒音声) | 特徴 | 推奨用途 |
|--------|----------------|------|----------|
| **ReazonSpeech** (k2-v2) | **~1.5秒** | **超高速**・軽量 (159M) | リアルタイム対話、大量バッチ処理 |
| **Kotoba-Whisper** (v2.0) | ~6.9秒 | **高精度**・文脈理解 (1.5B) | 議事録作成、複雑な文脈の認識 |

---

## インストール

1. **リポジリのクローン**
   ```powershell
   git clone <repository-url>
   cd WhisperServer
   ```

2. **セットアップ**
   自動セットアップスクリプトを実行します（仮想環境作成と依存関係インストール）。
   ```powershell
   .\setup.ps1
   ```
   または手動で:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## 使い方

### 1. サーバー起動
```powershell
.\run.ps1
```
または
```powershell
start_server.bat
```
サーバーは `http://127.0.0.1:8000` で起動します。
初回起動時にモデルファイルが自動ダウンロードされます（数GB）。

### 2. APIリクエスト

APIは Azure OpenAI Whisperモデルの形式 (`POST /openai/deployments/{model}/audio/transcriptions`) に準拠しています。 URLの `{model}` 部分でエンジンを切り替えます。

#### A) ReazonSpeech (高速モード)
```bash
curl -X POST "http://127.0.0.1:8000/openai/deployments/reazonspeech/audio/transcriptions" \
  -H "api-key: test" \
  -F "file=@audio.mp3" \
  -F "language=ja"
```

#### B) Kotoba-Whisper (高精度モード)
```bash
curl -X POST "http://127.0.0.1:8000/openai/deployments/whisper-1/audio/transcriptions" \
  -H "api-key: test" \
  -F "file=@audio.mp3" \
  -F "language=ja"
```

### 3. APIドキュメント
詳細な仕様はSwagger UIで確認できます。
- URL: http://127.0.0.1:8000/docs

---

## 付録: ベンチマーク結果
Windows 11 (Ryzen 7 7840HS) での計測結果:

| テスト音声 | ReazonSpeech | Kotoba-Whisper | 速度差 |
|------------|--------------|----------------|--------|
| 短い音声 (MP3) | 1.52s | 6.88s | **4.5x** |
| 長い音声 (MP3) | 2.64s | 12.02s | **4.5x** |

※ ReazonSpeechは `soundfile` によるネイティブデコード最適化済み。

## システム設計
詳細は [ARCHITECTURE.md](ARCHITECTURE.md) を参照してください。
