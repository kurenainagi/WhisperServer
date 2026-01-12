# Windows Native Whisper Server (Optimized)

AMD Ryzen AI (780M) 搭載PC向けの、高速・高精度な音声認識APIサーバーです。
`faster-whisper` エンジンと日本語特化モデル `kotoba-whisper-v2.2` を使用し、Windows上で直接動作するように最適化されています。

## 特徴
- **爆速**: 24秒の音声を **約6.75秒** で処理 (実時間の約3.5倍速)。
- **高精度**: `kotoba-whisper-v2.2` (Large-v3ベース) により、日本語の専門用語や言い回しも正確に認識。
- **Azure OpenAI互換**: `whisper-1` 互換のAPIエンドポイントを提供。既存のアプリやツールからそのまま利用可能。
- **軽量**: Docker不要。Windows上でネイティブ動作します。

---

## 使い方 (How to Use)

### 1. サーバーの起動
フォルダ内の **`start_server.bat`** をダブルクリックしてください。
サーバーが起動し、以下のような画面が表示されれば準備完了です。

```
INFO:whisper-api:  Device: cpu
INFO:whisper-api:  Compute: int8
INFO:     Uvicorn running on http://127.0.0.1:8000
```

> **Note**: 初回起動時はセットアップ（仮想環境作成やモジュールインストール）が自動的に行われるため、数分かかる場合があります。

### 2. 動作確認 (ベンチマーク)
起動した状態で、別のターミナルから以下を実行すると速度を計測できます。
```powershell
.\.venv\Scripts\python.exe benchmark.py
```

### 3. APIの利用方法 (クライアントから呼ぶ場合)
サーバーは `http://127.0.0.1:8000` で待機しています。

**Curlの例:**
```bash
curl -X POST "http://127.0.0.1:8000/openai/deployments/whisper-1/audio/transcriptions" ^
  -H "Content-Type: multipart/form-data" ^
  -F "file=@audio.mp3" ^
  -F "language=ja"
```

**Pythonの例:**
```python
import requests

with open("audio.mp3", "rb") as f:
    response = requests.post(
        "http://127.0.0.1:8000/openai/deployments/whisper-1/audio/transcriptions",
        files={"file": f},
        data={"language": "ja"}
    )
print(response.json())
```

---

## インストール手順 (手動セットアップする場合)
リポジトリを新規にCloneした場合などは、自動セットアップだけでなく手動コマンドも利用できます。

1. **セットアップ** (初回のみ):
   ```powershell
   .\setup.ps1
   ```
2. **起動**:
   ```powershell
   .\run.ps1
   ```
   ※ `.ps1` ファイルが実行できない場合は、`start_server.bat` を使用するか、PowerShellで `Set-ExecutionPolicy RemoteSigned` 等を実行して権限を変更してください。

---

## 動作環境
- **OS**: Windows 10 / 11
- **CPU**: AMD Ryzen (AVX-512/AMX対応推奨) または Intel CPU
- **Python**: 3.10 以上 (インストーラーでPATHを通しておくこと)
- **FFmpeg**: インストール済みであること (パスが通っている、またはWinGetで導入可能であること)

## ディレクトリ構成
- `app/`: サーバーのソースコード
- `start_server.bat`: 起動用ランチャー
- `run.ps1`: 起動スクリプト (PowerShell版)
- `setup.ps1`: 環境構築スクリプト
- `requirements-windows.txt`: 必要なPythonライブラリ

## アーキテクチャ詳細
詳細は [ARCHITECTURE.md](ARCHITECTURE.md) を参照してください。
