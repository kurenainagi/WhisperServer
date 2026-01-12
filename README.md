# AMD Radeon 780M用 ローカルAzure OpenAI Whisper Server

このプロジェクトは、AMD Radeon 780M (RDNA 3 iGPU) を搭載したPC上で、Azure OpenAI Whisper API (`whisper-1`) と互換性のあるローカル推論サーバーを構築するものです。
Dockerコンテナ上で動作し、ROCmを利用してiGPUの性能を引き出します。

## 特徴
- **Azure OpenAI完全互換**: APIエンドポイント、パラメータ、レスポンス形式を模倣。既存のクライアントコードをそのまま接続可能。
- **高速推論**: `Faster-Whisper` (CTranslate2) + `INT8` 量子化により、iGPUでも高速かつ低メモリで動作。
- **AMD RDNA 3対応**: Radeon 780M (gfx1103) をROCm環境で動作させるための設定済み。

## 前提条件 (ホストマシンの設定)

## 前提条件 (WSL2環境の場合)

### 1. Windows側でのドライバ確認
WSL2では、**Linux内でのドライバインストールは不要で、推奨されません**。
WindowsのホストOSに、AMD公式の最新ドライバがインストールされていることを確認してください。
* **AMD Software: Adrenalin Edition** (最新版推奨)
* **Azure OpenAI完全互換API**: `POST /openai/deployments/{id}/audio/transcriptions`
* **推論エンジン**: Hugging Face Transformers (`openai/whisper-large-v3`)
* **実行環境**: Docker (WSL2 / Linux)

## 必要要件
* Docker Desktop (WSL2 backend) または Docker Engine (Linux)
* 8GB以上のRAM (Largeモデル用)

## セットアップ & 実行

1. **リポジリの準備**:
   ```bash
   git clone <repository_url>
   cd env_whisper
   ```

2. **コンテナのビルドと起動**:
   ```bash
   docker compose up -d --build
   ```
   ※初回起動時にWhisperモデル（約3GB）のダウンロードが行われるため、APIが応答するまで数分かかる場合があります。

3. **動作確認**:
   ```bash
   curl -X POST "http://localhost:8000/openai/deployments/whisper-1/audio/transcriptions" \
     -H "api-key: dummy" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio.mp3"
   ```

## 技術的詳細と制限 (GPUについて)

### Faster-Whisper (CTranslate2) と AMD GPU on WSL2 Docker
本プロジェクトでは `faster-whisper` (CTranslate2バックエンド) の利用を前提としており、Radeon 780M (RDNA 3) でのGPU加速を試みました。
しかし、以下の技術的制約により、**WSL2上のDockerコンテナ内** ではGPUを利用できませんでした。

* **ROCmの制約**: CTranslate2が依存するROCmのユーザーモードドライバは、Linuxカーネルの `/dev/kfd` (Kernel Fusion Driver) デバイスへの直接アクセスを要求します。
* **WSL2の制約**: WSL2は `/dev/kfd` をサポートしておらず、代わりに `/dev/dxg` (DirectX Graphics) を介してGPUを認識させます。
* **互換性**: 現在のROCm (CTranslate2ビルド) は `/dev/dxg` 経由での動作をネイティブサポートしていません。

このため、本サーバーは **CPUモード (`float32`)** で動作するように構成されています。
Ryzen 780MのCPU性能により、実用的な速度で動作しますが、GPU本来の速度は出ません。

### GPUを利用するための代替案
もしGPUによる高速化が必須の場合は、Docker/WSL2ではなく、以下の環境での実行を推奨します：

1. **Windows Native環境**: PythonをWindowsに直接インストールし、ZLUDA等を使用してCUDA互換モードで動かす (最も推奨)。
2. **Linux Native環境**: Ubuntu等をネイティブインストール（デュアルブート）すれば、`/dev/kfd` が利用できるため、本Docker構成 (`docker-compose.yml` のデバイス設定を `/dev/kfd` に変更) でGPUが動作します。

## セットアップ & 実行 (CPUモード)

1. **コンテナのビルドと起動**:
   ```bash
   docker compose up -d --build
   ```
   ※初回起動時にWhisperモデル（約3GB）のダウンロードが行われるため、APIが応答するまで数分かかる場合があります。

2. **動作確認**:
   ```bash
   # テストリクエスト
   curl -X POST "http://localhost:8000/openai/deployments/whisper-1/audio/transcriptions" \
     -H "api-key: dummy" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio.mp3" \
     -F "response_format=verbose_json"
   ```

## よくある質問 (FAQ)

### Q. なぜ AMD GPU (Radeon 780M) が使えないのですか？
**A. WSL2 (Linux on Windows) の仕組みと、Faster-Whisper (ROCm) の要求仕様が一致しないためです。**

1.  **ROCm (Whisperのエンジン) の要求**:
    *   AMD GPUを動かすためのドライバ (ROCm) は、Linuxカーネルの **`/dev/kfd`** (Kernel Fusion Driver) というデバイスと直接通信する必要があります。
2.  **WSL2 の仕様**:
    *   WSL2は完全なLinuxではなく、Windowsと統合された特殊なカーネルを使用しています。このカーネルには `/dev/kfd` が**存在しません**。
    *   代わりに `/dev/dxg` というデバイスを使って Windows側のGPUドライバと通信しますが、ROCmはこの `/dev/dxg` に対応していません。
3.  **結果**:
    *   アプリはGPUを探しに行きますが、「通信相手のデバイス (`/dev/kfd`) が見つからない」ため、GPUを認識できずにエラーとなります。

### Q. どうすれば GPU を使えるようになりますか？
Docker (WSL2) という環境を変える必要があります。以下のいずれかの方法で実現可能です。

**方法1: Windowsネイティブ環境で動かす (推奨)**
Dockerを使わず、Windows上に直接 Python とライブラリをインストールします。
*   **利点**: WindowsのGPUドライバを直接利用できるため、動作する可能性が高いです。
*   **ツール**: `ZLUDA` (CUDA互換ツール) などを使用することで、Faster-WhisperをGPUで動かせる可能性があります。

**方法2: Linuxネイティブ環境で動かす**
Windowsではなく、PCに直接 Ubuntu などのLinuxをインストール（デュアルブートなど）します。
*   **利点**: 本物の `/dev/kfd` デバイスが使えるため、今回作成した Docker イメージが**そのまま GPUモードで動作します**（`docker-compose.yml` でデバイス設定を有効化するだけです）。

### Q. Large-v3 モデルが遅いですが、解決策は？
CPUモードでは演算が重いため、以下の対策があります。
1.  **`medium` モデルを使う**: 認識精度は少し落ちますが、速度は1.6倍になります（約13秒）。
2.  **`base` モデルを使う**: 精度は荒いですが、爆速です（約3秒）。
3.  **GPU環境へ移行する**: 上記の「方法1」または「方法2」を検討してください。

## 環境変数 (カスタマイズ)
`docker-compose.yml` または `.env` で以下を変更可能です。

| 変数名 | デフォルト | 説明 |
|---|---|---|
| `WHISPER_MODEL` | `large-v3` | 使用するモデル (base, small, medium, large-v3 等) |

## トラブルシューティング
- **メモリエラー**: `WHISPER_MODEL` を `medium` や `small` に変更してください。780Mはメインメモリ(VRAM共有)を使用するため、BIOSでVRAM割り当てを増やしておくと安定します。
