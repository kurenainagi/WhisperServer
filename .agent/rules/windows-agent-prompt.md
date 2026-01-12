# プロジェクト: AMD Radeon 780M用 ローカルAzure OpenAI Whisper互換サーバー

## プロジェクト概要

このプロジェクトは、FastAPIを使用してAzure OpenAIのWhisper API (`whisper-1`) を模倣するローカル音声文字起こしサーバーを構築するものです。

**目標**: AMD Radeon 780M (RDNA 3 iGPU) を使用してGPU加速された音声認識を実現する。

## 現在の状況（WSL2/Dockerで試行済み）

### ❌ 失敗したアプローチ（WSL2 + Docker環境）

| 方法 | 結果 | 理由 |
|------|------|------|
| **ROCm + CTranslate2** | 失敗 | WSL2には`/dev/kfd`が存在しない |
| **torch-directml + Transformers** | 失敗 | デバイス認識されるが推論時にD3D12エラー (-2005270521) |
| **onnxruntime-directml** | 利用不可 | Linux/WSL2では未対応（Windows専用パッケージ） |

### 技術的制約の詳細

1. **ROCm**: AMD GPU用のCUDA代替だが、Linuxカーネルの`/dev/kfd`デバイスが必要。WSL2カーネルにはこれが存在しない。
2. **DirectML on WSL2**: torch-directmlはDirectMLデバイス(`privateuseone:0`)を認識するが、Dockerコンテナ経由での`/dev/dxg`パススルーではモデル転送・推論時にD3D12エラーが発生。
3. **結論**: WSL2 + Dockerの組み合わせではAMD GPUによる推論は現時点で技術的に不可能。

## ✅ Windows Native環境での構築（これから実施）

**このタスクの目的**: Windows上で直接Python + DirectMLを使用し、GPUで動作するWhisper APIサーバーを構築する。

### 推奨アプローチ

1. **torch-directml + Transformers**
   - Whisperモデルを`torch-directml`バックエンドで実行
   - `transformers`ライブラリのpipelineを使用

2. **代替案: onnxruntime-directml + optimum**
   - ONNXに変換したWhisperモデルをDirectMLで実行
   - Windows環境では`onnxruntime-directml`パッケージが利用可能

### 必要な依存パッケージ

```
torch-directml
transformers
accelerate
librosa
soundfile
fastapi
uvicorn[standard]
python-multipart
```

または ONNX Runtime版:
```
onnxruntime-directml
optimum[onnxruntime]
transformers
librosa
soundfile
fastapi
uvicorn[standard]
python-multipart
```

## API仕様（Azure OpenAI完全互換）

### エンドポイント
```
POST /openai/deployments/{deployment_id}/audio/transcriptions
```

### 入力 (multipart/form-data)
- `file` (必須): 音声ファイル
- `language`: 言語コード (例: "ja")
- `prompt`: 初期プロンプト
- `response_format`: "json" または "verbose_json"

### 認証
- `api-key` ヘッダー（ダミー認証、空でなければOK）

### レスポンス例
```json
{
  "text": "文字起こし結果"
}
```

verbose_json形式:
```json
{
  "task": "transcribe",
  "language": "ja",
  "duration": 5.2,
  "text": "文字起こし結果",
  "segments": [...]
}
```

## 環境構築指針

### 環境汚染を最小限にするため
1. Python仮想環境（venv）を使用する
2. すべてのパッケージは仮想環境内にインストール
3. 削除時は仮想環境フォルダを削除するだけでクリーンアップ完了

### セットアップ手順（目標）
```powershell
# 1. 仮想環境作成
python -m venv .venv

# 2. 仮想環境有効化
.\.venv\Scripts\Activate.ps1

# 3. 依存パッケージインストール
pip install torch-directml transformers accelerate librosa soundfile fastapi uvicorn[standard] python-multipart

# 4. サーバー起動
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 既存コード参考

WSL2側で作成した以下のファイルが参考になります（一部修正が必要）:

### transcriber_dml.py（DirectML版推論エンジン）
- `torch_directml`を使用してGPUデバイスを取得
- `transformers.pipeline`でWhisperモデルをロード
- device引数にDirectMLデバイスオブジェクトを渡す

### main.py（FastAPI本体）
- lifespanでモデルをロード
- Azure OpenAI互換のエンドポイント実装済み
- エラーハンドリングもAzure互換形式

## 注意点

1. **モデルサイズ**: Radeon 780Mは共有メモリ（システムRAMと共有）を使用するため、`large-v3`（約3GB）はメモリ不足になる可能性あり。`medium`や`small`モデルから試すこと。

2. **DirectMLデバイス確認コード**:
```python
import torch_directml
print(torch_directml.is_available())  # True なら成功
print(torch_directml.device())  # デバイスオブジェクト取得
```

3. **float16について**: AMD GPUでは`float16`が不安定な場合あり。`float32`でまず動作確認を行う。

4. **テスト音声**: https://pro-video.jp/voice/announce/ からダウンロード可能

## 成功基準

1. サーバーが起動し、ヘルスチェック `/health` が応答する
2. テスト音声ファイルを送信し、正しく文字起こし結果が返る
3. GPUが使用されていることを確認（タスクマネージャーでGPU使用率確認）

## ファイル構成（目標）

```
whisper-api-windows/
├── .venv/                    # Python仮想環境（gitignore）
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   └── transcriber.py       # Whisper推論エンジン（DirectML版）
├── setup.ps1                # セットアップスクリプト
├── run.ps1                  # 起動スクリプト
├── requirements.txt
└── README.md
```
