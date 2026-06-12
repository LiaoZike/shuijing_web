"""
Modal Breeze-ASR-26 部署腳本
------------------------------
部署指令：
    modal deploy scratch/modal_breeze_asr.py

部署完後會給你一個 HTTPS URL，例如：
    https://liaozike--breeze-asr-api-breezeasr-transcribe.modal.run
"""

import modal
import os
from fastapi import Request

# ── 建立環境 Image（只在第一次 build，之後快取）─────────────────────────────
def _download_model():
    """在 image build 時預先下載模型，之後啟動不用重新下載"""
    from transformers import pipeline
    print("Pre-downloading Breeze-ASR-26 (6GB, one-time)...")
    pipeline(
        "automatic-speech-recognition",
        model="MediaTek-Research/Breeze-ASR-26",
    )
    print("Done!")


image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "transformers>=4.35.0",
        "torch",
        "torchaudio",
        "librosa",
        "soundfile",
        "accelerate",
    )
    .run_function(_download_model)
)

app = modal.App("breeze-asr-api", image=image)


# ── ASR Class（GPU 常駐，idle 5 分鐘後自動休眠）───────────────────────────
@app.cls(
    gpu="t4",
    container_idle_timeout=300,   # 閒置 5 分鐘後休眠
)
class BreezeASR:

    @modal.enter()
    def load_model(self):
        """Container 啟動時載入模型（只跑一次，之後快）"""
        import torch
        from transformers import pipeline

        device = 0 if torch.cuda.is_available() else -1
        gpu_name = torch.cuda.get_device_name(0) if device == 0 else "CPU"
        print(f"Loading Breeze-ASR-26 on {gpu_name}...")

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model="MediaTek-Research/Breeze-ASR-26",
            device=device,
            chunk_length_s=30,
        )
        print("Model ready!")

    @modal.web_endpoint(method="POST")
    async def transcribe(self, request: Request):
        """
        接收音檔 bytes，回傳辨識文字

        curl 測試：
            curl -X POST <URL> \
                 -H "Content-Type: audio/m4a" \
                 --data-binary @audio.m4a
        """
        import tempfile

        body = await request.body()
        if not body:
            return {"error": "No audio data", "status": "error"}

        # 從 Content-Type 判斷副檔名
        ct = request.headers.get("content-type", "audio/wav").lower()
        if "m4a" in ct or "mp4" in ct:
            ext = ".m4a"
        elif "mp3" in ct or "mpeg" in ct:
            ext = ".mp3"
        elif "flac" in ct:
            ext = ".flac"
        else:
            ext = ".wav"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(body)
            tmp_path = f.name

        try:
            result = self.pipe(tmp_path)
            return {"text": result["text"], "status": "ok"}
        except Exception as e:
            return {"error": str(e), "status": "error"}
        finally:
            os.unlink(tmp_path)


# ── 本地快速測試（modal run）────────────────────────────────────────────────
@app.local_entrypoint()
def main():
    print("Deployment script loaded OK.")
    print("Run: modal deploy scratch/modal_breeze_asr.py")
