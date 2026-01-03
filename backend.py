# backend.py
# FastAPI wrapper around a high-end Ollama model with JSON and streaming endpoints.

import os
import json
import socket
import platform
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import getpass
import threading
import time
from typing import List, Literal, Optional, AsyncGenerator
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from queue import Queue, Empty
from starlette.responses import StreamingResponse, JSONResponse
import ollama  # pip install ollama
from ollama._types import ResponseError
import asyncio

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")  # change to qwen2.5:72b, mistral-nemo:12b, etc.

# ---- Local storage config ----
APP_DIR = Path.cwd() / ".jarvis"           # e.g., C:\Users\<you>\.jarvis
APP_DIR.mkdir(parents=True, exist_ok=True)
STORE_JSON = APP_DIR / "memory.json"
STORE_LOG  = APP_DIR / "notes.txt"
_store_lock = threading.Lock()

# --- JSON log config ---
LOG_JSONL = APP_DIR / "events.jsonl"
LOG_LOCK = threading.Lock()
MAX_LOG_BYTES = 500_000_000  # ~500 MB simple rotation threshold
MAX_LOG_CHARS = 80000

class KV(BaseModel):
    key: str
    value: str

class AppendNote(BaseModel):
    text: str

class LogWrite(BaseModel):
    event: str
    data: dict | None = None
    level: Literal["INFO", "WARN", "ERROR", "DEBUG"] = "INFO"

class LogQuery(BaseModel):
    key: str
    value: str
    limit: int = 200

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = True
    keep_alive: Optional[str] = "5m"  # for ollama local cache
    options: Optional[dict] = None    # extra model options if needed

app = FastAPI(title="Ollama Chat Backend", version="1.0")

# CORS for local UI or a future web front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten if you expose beyond localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _timezone_name() -> str | None:
    # Primary: from aware datetime
    try:
        return datetime.now().astimezone().tzname()
    except Exception:
        pass
    # Fallback: from time module (works on Windows too)
    try:
        return time.tzname[time.daylight] if time.daylight else time.tzname[0]
    except Exception:
        return None

def _rotate_log_if_needed():
    try:
        if LOG_JSONL.exists() and LOG_JSONL.stat().st_size > MAX_LOG_BYTES:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            LOG_JSONL.replace(LOG_JSONL.with_name(f"events-{ts}.jsonl"))
    except Exception:
        pass  # non-fatal

def _log_append(obj: dict) -> None:
    line = json.dumps(obj, ensure_ascii=False)
    with LOG_LOCK:
        _rotate_log_if_needed()
        with LOG_JSONL.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

def _tail_jsonl(path: Path, n: int) -> list[dict]:
    """Return last n JSON objects without loading the whole file."""
    if not path.exists() or n <= 0:
        return []
    size = path.stat().st_size
    chunk = 1024 * 64
    data = b""
    with path.open("rb") as f:
        pos = max(0, size - chunk)
        f.seek(pos)
        data = f.read()
        # If not enough lines, read more backwards
        while data.count(b"\n") <= n and pos > 0:
            pos = max(0, pos - chunk)
            f.seek(pos)
            data = f.read(size - pos)
            if pos == 0:
                break
    lines = data.splitlines()[-n:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln.decode("utf-8")))
        except Exception:
            continue
    return out

def _filter_jsonl(path: Path, key: str, value: str, limit: int = 200) -> list[dict]:
    """Linear scan filter (good enough for small logs)."""
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if str(obj.get(key)) == value:
                    out.append(obj)
                    if len(out) >= limit:
                        break
            except Exception:
                continue
    return out

def _load_store() -> dict:
    if STORE_JSON.exists():
        try:
            return json.loads(STORE_JSON.read_text(encoding="utf-8"))
        except Exception:
            # If file is corrupt, keep a backup and start fresh
            backup = STORE_JSON.with_suffix(".bak")
            STORE_JSON.rename(backup)
    return {}

def _save_store(data: dict) -> None:
    tmp = STORE_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STORE_JSON)

def _truncate(text: str, limit: int = MAX_LOG_CHARS) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 20] + f"... [truncated {len(text)-limit} chars]"

def _last_user_prompt(msgs: list[ChatMessage]) -> str:
    """
    Return the most recent user message content; if none, fall back to
    concatenating all non-system messages.
    """
    for m in reversed(msgs):
        if m.role == "user":
            return m.content
    # fallback: join all user/assistant (rarely needed)
    return "\n".join(f"{m.role}: {m.content}" for m in msgs if m.role != "system")

# --- time helpers ---
def now_local_iso() -> str:
    # your machine's local time (timezone-aware)
    return datetime.now().astimezone().isoformat(timespec="seconds")

def now_ist_iso() -> str:
    # IST explicitly, regardless of your system tz
    return datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="minutes")

def timezone_name_fallback() -> str | None:
    try:
        return datetime.now().astimezone().tzname()
    except Exception:
        try:
            return time.tzname[time.daylight] if time.daylight else time.tzname[0]
        except Exception:
            return None


def _drive_letter_of(path: Path) -> str:
    # Windows: returns like 'C:'; on *nix returns ''.
    return path.drive

def _local_time_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

def build_context_system_msg() -> dict :
    return {
        "role": "system",
        "content": (
            f"Context:\n"
            f"- Current local datetime: {_local_time_iso()} ({_timezone_name()})\n"
            f"- Current local date: {_local_time_iso()[:10]}\n"
            f"- Host: {socket.gethostname()} User: {getpass.getuser()}\n"
            f"- CWD: {Path.cwd()} Drive: {_drive_letter_of(Path.cwd())}\n"
            f"- Store: {STORE_JSON}\n"
        )
    }

def _final_messages(req: ChatRequest) -> list[dict]:
    return [build_context_system_msg()] + [m.model_dump() for m in req.messages]


@app.get("/health")
async def health():
    return {"ok": True, "model": DEFAULT_MODEL}

@app.post("/chat")
async def chat_once(req: ChatRequest):
    model = req.model or DEFAULT_MODEL
    opts = req.options or {}
    prompt_text = _truncate (_last_user_prompt(req.messages))

    #log incoming prompt
    _log_append({
        "ts": _local_time_iso(),
        "event": "chat_request",
        "level": "INFO",
        "model": model,
        "temp": req.temperature,
        "count_msgs": len(req.messages),
        "prompt" : prompt_text,
    })
    try:
        resp = ollama.chat(
            model=model,
            messages=_final_messages(req),
            keep_alive=req.keep_alive,
            options={"temperature": req.temperature, **opts} if req.temperature is not None else opts,
            stream=False,
        )

        response_text  = _truncate((resp.get("message", {}) or {}).get("content", "") or "" )
        # —— log the response summary
        msg = resp.get("message", {}) or {}
        _log_append({
            "ts": _local_time_iso(),
            "event": "chat_response",
            "level": "INFO",
            "model": model,
            "chars": len(msg.get("content", "") or ""),
            "response" : response_text,

        })

        return JSONResponse(resp)
    
    except ResponseError as e:
        _log_append({
            "ts": _local_time_iso(),
            "event": "chat_error",
            "level": "ERROR",
            "model": model,
            "prompt": prompt_text,
            "detail": str(e),
        })
        return JSONResponse(
            {"error": f"Model '{model}' not found or not pulled. Run: ollama pull {model}",
             "detail": str(e)},
            status_code=400,
        )
    
@app.get("/system/info")
async def system_info():
    cwd = Path.cwd()
    return {
        "now": _local_time_iso(),
        "now_ist": now_ist_iso(),
        "timezone": _timezone_name(),
        "username": getpass.getuser(),
        "hostname": socket.gethostname(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "python": platform.python_version(),
        },
        "cwd": str(cwd),
        "drive": _drive_letter_of(cwd),
        "app_dir": str(APP_DIR),
        "store_json": str(STORE_JSON),
        "store_log": str(STORE_LOG),
    }

@app.get("/log/last")
async def log_last(n: int = 50):
    items = _tail_jsonl(LOG_JSONL, n)
    return {"count": len(items), "items": items, "path": str(LOG_JSONL)}

@app.get("/log/export")
async def log_export():
    """Return the whole file path (client can read or you can stream it)."""
    return {"path": str(LOG_JSONL), "exists": LOG_JSONL.exists()}

@app.post("/log/write")
async def log_write(entry: LogWrite):
    obj = {
        "ts": _local_time_iso(),
        "event": entry.event,
        "level": entry.level,
        "data": entry.data or {},
        "host": socket.gethostname(),
        "user": getpass.getuser(),
    }
    _log_append(obj)
    return {"ok": True, "path": str(LOG_JSONL)}

@app.post("/log/query")
async def log_query(q: LogQuery):
    items = _filter_jsonl(LOG_JSONL, q.key, q.value, q.limit)
    return {"count": len(items), "items":  items}

@app.post("/store/set")
async def store_set(item: KV):
    with _store_lock:
        data = _load_store()
        data[item.key] = item.value
        _save_store(data)
    return {"ok": True, "written": {item.key: item.value}}

@app.get("/store/get")
async def store_get(key: str):
    with _store_lock:
        data = _load_store()
        return {"key": key, "value": data.get(key)}

@app.get("/store/all")
async def store_all():
    with _store_lock:
        data = _load_store()
        return {"data": data, "path": str(STORE_JSON)}

@app.post("/store/append")
async def store_append(note: AppendNote):
    line = f"[{_local_time_iso()}] {note.text}\n"
    with _store_lock:
        with STORE_LOG.open("a", encoding="utf-8") as f:
            f.write(line)
    return {"ok": True, "appended_to": str(STORE_LOG)}


async def _stream_generator(req: ChatRequest) -> AsyncGenerator[bytes, None]:
    """
    Safe streaming generator.
    - Ollama stream runs fully in a worker thread
    - Chunks are passed via a Queue
    - No full-response buffering
    - Hard output cap to avoid runaway generations
    """

    loop = asyncio.get_event_loop()
    model = req.model or DEFAULT_MODEL
    prompt_text = _truncate(_last_user_prompt(req.messages))

    _log_append({
        "ts": _local_time_iso(),
        "event": "chat_stream_start",
        "level": "INFO",
        "model": model,
        "count_msgs": len(req.messages),
        "prompt": prompt_text,
    })

    q: Queue = Queue()
    MAX_STREAM_CHARS = 50_000   # hard safety cap
    LOG_CHARS = 8_000           # how much we keep for logs

    def run_chat():
        sent = 0
        try:
            for chunk in ollama.chat(
                model=model,
                messages=_final_messages(req),
                keep_alive=req.keep_alive,
                options={"temperature": req.temperature, **(req.options or {})}
                if req.temperature is not None
                else (req.options or {}),
                stream=True,
            ):
                delta = chunk.get("message", {}).get("content", "")
                if not delta:
                    continue

                sent += len(delta)
                q.put(delta)

                if sent >= MAX_STREAM_CHARS:
                    q.put("\n[Response truncated]\n")
                    break
        except Exception as e:
            q.put(f"\n[Stream error] {e}\n")
        finally:
            q.put(None)  # sentinel → tells async side to stop

    # Start Ollama streaming in background thread
    loop.run_in_executor(None, run_chat)

    logged = ""
    total = 0

    while True:
        try:
            item = q.get(timeout=0.1)
        except Empty:
            await asyncio.sleep(0)
            continue

        if item is None:
            break

        total += len(item)

        # keep a small prefix for logs only
        if len(logged) < LOG_CHARS:
            logged += item

        yield item.encode("utf-8")
        await asyncio.sleep(0)

    _log_append({
        "ts": _local_time_iso(),
        "event": "chat_stream_end",
        "level": "INFO",
        "model": model,
        "bytes": total,
        "prompt": prompt_text,
        "response": _truncate(logged),
    })

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming endpoint. Returns text chunks immediately as they are produced.
    Client should read incrementally.
    """
    return StreamingResponse(_stream_generator(req), media_type="text/plain; charset=utf-8")

if __name__ == "__main__":
    # Run: uvicorn backend:app --reload --port 8000
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
