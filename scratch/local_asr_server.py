r"""
Local ASR server.

Default behavior:
    1. Try to load model files from D:/models/Breeze-ASR-26.
    2. If D:/models/Breeze-ASR-26 is missing or empty, load MediaTek-Research/Breeze-ASR-26 directly from Hugging Face.
    3. Run ASR with GPU when available.

Run:
    python scratch/local_asr_server.py

Optional:
    python scratch/local_asr_server.py --model-dir D:/models/Breeze-ASR-26 --device cuda
    python scratch/local_asr_server.py --model-id MediaTek-Research/Breeze-ASR-26
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

# Suppress Hugging Face transformers sequential GPU pipelines warning
import logging
import warnings
logging.getLogger("transformers.pipelines.pt_utils").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*pipelines sequentially on GPU.*")

# Workaround for compatibility issue with some versions of transformers on Python 3.13
if not hasattr(torch, "float8_e8m0fnu"):
    setattr(torch, "float8_e8m0fnu", torch.float32)

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware


DEFAULT_MODEL_ID = "MediaTek-Research/Breeze-ASR-26"
DEFAULT_MODEL_DIR = Path("D:/models/Breeze-ASR-26")
DEFAULT_PORT = 8002
BASE_DIR = Path(__file__).resolve().parents[1]
MIN_AUDIO_SECONDS = 1.0
MIN_AUDIO_RMS = 0.003


def load_env_file(env_path: Path = BASE_DIR / ".env") -> None:
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
        print(f"[SYSTEM] Loaded env file: {env_path}")
        return
    except ImportError:
        pass

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
    print(f"[SYSTEM] Loaded env file without python-dotenv: {env_path}")


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        print(f"[WARN] Ignoring invalid integer env var {name}={value!r}.")
        return default


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        print(f"[WARN] Ignoring invalid float env var {name}={value!r}.")
        return default

app = FastAPI(title="Shuijing ASR Local Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipe = None
runtime = {
    "model_id": DEFAULT_MODEL_ID,
    "model_dir": str(DEFAULT_MODEL_DIR),
    "model_source": DEFAULT_MODEL_ID,
    "device": "not loaded",
}


def model_dir_has_files(model_dir: Path) -> bool:
    """Return True when the folder looks like a downloaded HF model snapshot."""
    if not model_dir.exists() or not model_dir.is_dir():
        return False

    existing = {path.name for path in model_dir.iterdir() if path.is_file()}
    has_config = "config.json" in existing
    has_weights = (
        "model.safetensors" in existing
        or "pytorch_model.bin" in existing
        or "model.safetensors.index.json" in existing
        or any(name.endswith(".safetensors") for name in existing)
    )
    return has_config and has_weights


def resolve_model_source(model_id: str, model_dir: Path) -> str:
    if model_dir_has_files(model_dir):
        print(f"[MODEL] Found local model at: {model_dir}")
        return str(model_dir)

    print(f"[MODEL] Local model not found at: {model_dir}")
    print(f"[MODEL] Loading directly from Hugging Face: {model_id}")
    return model_id


def print_environment() -> None:
    print("[SYSTEM] Python:", sys.executable)
    print("[SYSTEM] Torch:", torch.__version__)
    print("[SYSTEM] Torch CUDA build:", torch.version.cuda or "CPU-only")
    print("[SYSTEM] CUDA available:", torch.cuda.is_available())
    print("[SYSTEM] CUDA device count:", torch.cuda.device_count())
    if torch.cuda.is_available():
        print("[SYSTEM] GPU:", torch.cuda.get_device_name(0))


def choose_device(device_arg: str) -> tuple[int, str]:
    if device_arg == "cpu":
        return -1, "CPU"

    if device_arg == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "You requested --device cuda, but this Python environment cannot see CUDA. "
            "Check that you are running the same Python that has CUDA-enabled PyTorch."
        )

    if torch.cuda.is_available():
        return 0, torch.cuda.get_device_name(0)

    print("[WARN] GPU not detected by PyTorch. Falling back to CPU.")
    return -1, "CPU"


def inspect_audio(audio_path: str) -> dict:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        audio_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "s16le",
        "pipe:1",
    ]
    completed = subprocess.run(command, capture_output=True, check=True)
    pcm = np.frombuffer(completed.stdout, dtype=np.int16)
    duration = len(pcm) / 16000
    if len(pcm) == 0:
        rms = 0.0
        peak = 0.0
    else:
        samples = pcm.astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(samples * samples)))
        peak = float(np.max(np.abs(samples)))
    return {"duration": duration, "rms": rms, "peak": peak}


def should_skip_audio(audio_info: dict) -> tuple[bool, str]:
    duration = audio_info["duration"]
    rms = audio_info["rms"]
    min_seconds = env_float("ASR_MIN_SECONDS", MIN_AUDIO_SECONDS)
    min_rms = env_float("ASR_MIN_RMS", MIN_AUDIO_RMS)
    if duration < min_seconds:
        return True, f"音訊太短（{duration:.2f} 秒），請至少錄 {min_seconds:g} 秒。"
    if rms < min_rms:
        return True, "沒有偵測到明顯聲音，請靠近麥克風再試一次。"
    return False, ""


def load_model(model_id: str, model_dir: Path, device_arg: str) -> None:
    global pipe

    from transformers import pipeline

    print_environment()
    model_source = resolve_model_source(model_id, model_dir)

    device_index, device_name = choose_device(device_arg)
    runtime.update(
        {
            "model_id": model_id,
            "model_dir": str(model_dir),
            "model_source": model_source,
            "device": device_name,
        }
    )

    print(f"[MODEL] Loading model source: {model_source}")
    print(f"[SYSTEM] Device: {device_name}")
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model_source,
        device=device_index,
        chunk_length_s=30,
    )
    print("[MODEL] ASR model is ready.")

    # 預先進行一次空語音暖機，初始化 GPU/CUDA 上下文，避免第一筆語音請求因為初始化時間過長而逾時
    try:
        import numpy as np
        print("[MODEL] Warming up GPU/CUDA context with a dummy forward pass...")
        dummy_pcm = np.zeros(16000, dtype=np.float32)
        pipe(dummy_pcm)
        print("[MODEL] Warm-up completed successfully.")
    except Exception as e:
        print(f"[WARN] Model warm-up failed (non-fatal): {e}")


@app.get("/")
def health():
    return {
        "status": "ok",
        "model_id": runtime["model_id"],
        "model_dir": runtime["model_dir"],
        "model_source": runtime["model_source"],
        "device": runtime["device"],
        "cuda_available": torch.cuda.is_available(),
    }


@app.post("/transcribe")
async def transcribe(request: Request):
    if pipe is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    body = await request.body()
    if not body:
        return {"error": "No audio data", "status": "error"}

    content_type = request.headers.get("content-type", "").lower()
    if "m4a" in content_type or "mp4" in content_type:
        ext = ".m4a"
    elif "mp3" in content_type or "mpeg" in content_type:
        ext = ".mp3"
    elif "flac" in content_type:
        ext = ".flac"
    else:
        ext = ".wav"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as audio_file:
        audio_file.write(body)
        tmp_path = audio_file.name

    try:
        audio_info = inspect_audio(tmp_path)
        print(
            "[ASR] Received "
            f"{ext}; duration={audio_info['duration']:.2f}s "
            f"rms={audio_info['rms']:.5f} peak={audio_info['peak']:.5f}"
        )
        should_skip, reason = should_skip_audio(audio_info)
        if should_skip:
            print(f"[ASR] Skipped: {reason}")
            return {
                "text": "",
                "status": "no_speech",
                "error": reason,
                "duration": round(audio_info["duration"], 2),
                "rms": round(audio_info["rms"], 5),
            }

        print("[ASR] Transcribing...")
        result = pipe(tmp_path)
        text = result.get("text", "").strip()
        if not text:
            return {"text": "", "status": "no_speech", "error": "辨識不到語音內容。"}
        print(f"[ASR] Result: {text}")
        return {"text": text, "status": "ok"}
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
        print(f"[ERROR] Audio decode failed: {detail}")
        return {"error": "音檔格式無法解析，請重新錄音。", "status": "error"}
    except Exception as exc:
        print(f"[ERROR] Transcription failed: {exc}")
        return {"error": str(exc), "status": "error"}
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def start_ngrok(port: int, domain: str = None) -> None:
    token = (
        os.environ.get("NGROK_TOKEN", "")
        or os.environ.get("NGROK_AUTHTOKEN", "")
        or os.environ.get("NGROK_AUTH_TOKEN", "")
    ).strip()
    if not token:
        print("[NGROK] NGROK_TOKEN is not set in the environment or .env; skip public tunnel.")
        print(f"[NGROK] Local API URL: http://127.0.0.1:{port}/transcribe")
        return

    from pyngrok import conf, ngrok

    # 預設使用日本 (jp) 節點，連線較穩定且延遲低
    region = os.environ.get("NGROK_REGION", "jp")
    conf.get_default().region = region

    print("[NGROK] Starting tunnel...")
    ngrok.set_auth_token(token)
    
    connect_kwargs = {}
    if domain:
        connect_kwargs["domain"] = domain
        
    public_url = ngrok.connect(port, **connect_kwargs)
    print("\n" + "=" * 70)
    print("[NGROK] Public API URL:")
    print(f"  {public_url}/transcribe")
    print("=" * 70 + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local ASR server.")
    parser.add_argument(
        "--model-id",
        default=os.environ.get("ASR_MODEL_ID", DEFAULT_MODEL_ID),
        help="Hugging Face model id to download when local files are missing.",
    )
    parser.add_argument(
        "--model-dir",
        default=os.environ.get("ASR_MODEL_DIR", str(DEFAULT_MODEL_DIR)),
        help="Local model folder. Default: D:/models/Breeze-ASR-26",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cuda", "cpu"],
        default=os.environ.get("ASR_DEVICE", "auto"),
    )
    parser.add_argument("--port", type=int, default=env_int("ASR_PORT", DEFAULT_PORT))
    parser.add_argument("--no-ngrok", action="store_true")
    parser.add_argument(
        "--domain",
        default=os.environ.get("NGROK_DOMAIN", ""),
        help="Custom permanent ngrok domain (e.g. xxx.ngrok-free.app)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    load_env_file()
    args = parse_args()
    model_dir = Path(args.model_dir).expanduser().resolve()

    load_model(args.model_id, model_dir, args.device)
    if not args.no_ngrok:
        start_ngrok(args.port, domain=args.domain)

    print(f"[SYSTEM] Starting FastAPI server on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
