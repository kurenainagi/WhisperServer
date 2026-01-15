# WhisperServer API 仕様書

本ドキュメントは、**WhisperServer** を外部アプリケーションから利用するための統合ガイドです。
このサーバーは **Azure OpenAI Service (Whisper API)** と互換性のあるインターフェースを提供しており、既存のOpenAI対応クライアントからも容易に利用可能です。

## 1. サーバー概要

- **ベースURL**: `http://127.0.0.1:8000`
- **プロトコル**: HTTP/1.1 REST API
- **認証**: ヘッダーに `api-key` が必要（値は任意。例: `test`）

## 2. 利用可能なモデル

用途に合わせて URL の `{deployment_id}` 部分を変更してモデルを選択します。

| モデルID (deployment_id) | エンジン | 特徴 | 推奨用途 |
|---|---|---|---|
| **`reazonspeech`** | ReazonSpeech (k2-v2) | **超高速** (24秒音声を約1.5秒で処理) | リアルタイム性が求められるシステム、対話AI |
| **`whisper-1`** | Kotoba-Whisper (v2.0) | **高精度** (文脈理解に優れる) | 議事録作成、長文の書き起こし |

※ `whisper-1` は `kotoba-whisper` と指定しても動作します。

---

## 3. APIリファレンス

### 音声認識 (Transcriptions)

音声ファイルをアップロードしてテキスト化します。

**エンドポイント:**
`POST /openai/deployments/{deployment_id}/audio/transcriptions`

**ヘッダー:**
- `api-key`: `test` (任意の文字列)
- `Content-Type`: `multipart/form-data`

**パラメータ (Form-Data):**

| パラメータ名 | 必須 | 説明 |
|---|---|---|
| `file` | **Yes** | 音声ファイルバイナリ (mp3, wav, m4a 等)。Windows最適化によりMP3/WAVが特に高速です。 |
| `language` | No | 言語コード。日本語の場合は `ja` を推奨 (自動判定も可)。 |
| `response_format` | No | レスポンス形式。`json` (デフォルト) または `verbose_json`。 |
| `prompt` | No | 前の文脈や専門用語のヒントを与えるプロンプトテキスト。 |

**レスポンス (JSON):**

```json
{
  "text": "ここに認識されたテキストが入ります。"
}
```

※ `verbose_json` を指定した場合、詳細なセグメント情報（タイムスタンプ等）が含まれます。

---

## 4. クライアント実装例

### A. Python (requests)

```python
import requests

url = "http://127.0.0.1:8000/openai/deployments/reazonspeech/audio/transcriptions"

headers = {
    "api-key": "test"
}

files = {
    "file": ("audio.mp3", open("audio.mp3", "rb"))
}

# 高速モデル (ReazonSpeech) を使用
response = requests.post(url, headers=headers, files=files)

print(response.json()["text"])
```

### B. C# (.NET / Unity)

WindowsデスクトップアプリやUnityからの利用例です。

```csharp
using System.Net.Http;
using System.Net.Http.Headers;
using System.IO;

public async Task<string> TranscribeAudioAsync(string filePath)
{
    // ReazonSpeech (高速版) を指定
    string url = "http://127.0.0.1:8000/openai/deployments/reazonspeech/audio/transcriptions";
    
    using (var client = new HttpClient())
    using (var form = new MultipartFormDataContent())
    using (var fileStream = File.OpenRead(filePath))
    {
        client.DefaultRequestHeaders.Add("api-key", "test");
        
        var fileContent = new StreamContent(fileStream);
        fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("audio/mpeg");
        
        form.Add(fileContent, "file", Path.GetFileName(filePath));
        
        var response = await client.PostAsync(url, form);
        string jsonResponse = await response.Content.ReadAsStringAsync();
        
        return jsonResponse; // {"text": "..."} が返る
    }
}
```

### C. cURL (コマンドライン)

```bash
curl -X POST "http://127.0.0.1:8000/openai/deployments/reazonspeech/audio/transcriptions" \
  -H "api-key: test" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_audio.mp3" \
  -F "language=ja"
```

### D. OpenAI Python SDK

このサーバーはOpenAI互換なので、公式SDKも利用可能です。

```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="test",
    api_version="2023-05-15",
    azure_endpoint="http://127.0.0.1:8000"
)

with open("audio.mp3", "rb") as audio_file:
    result = client.audio.transcriptions.create(
        model="reazonspeech", # モデル名をここで指定
        file=audio_file,
        language="ja"
    )

print(result.text)
```
