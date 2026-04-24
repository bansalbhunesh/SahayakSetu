#!/usr/bin/env bash
# startup.sh — boot backend (uvicorn) + frontend (static serve) for local dev / e2e.
# Usage:
#   ./startup.sh              # start both, wait until ready, keep running (Ctrl-C stops)
#   ./startup.sh --detach     # start both in background, print PIDs, exit
#   ./startup.sh --stop       # kill processes listening on backend/frontend ports
#   ./startup.sh --status     # report health of both services

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-4173}"
LOG_DIR="${LOG_DIR:-$REPO_ROOT/.runtime}"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
BACKEND_PID_FILE="$LOG_DIR/backend.pid"
FRONTEND_PID_FILE="$LOG_DIR/frontend.pid"

mkdir -p "$LOG_DIR"

PY="$REPO_ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3 || true)"
fi
if [[ -z "${PY:-}" ]]; then
  echo "[startup] no python interpreter found (venv missing, python3 not on PATH)" >&2
  exit 1
fi

port_pids() { lsof -ti tcp:"$1" 2>/dev/null || true; }

wait_for_http() {
  local url="$1" label="$2" attempts="${3:-60}"
  for ((i=1; i<=attempts; i++)); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      echo "[startup] $label ready ($url)"
      return 0
    fi
    sleep 1
  done
  echo "[startup] $label FAILED to become ready at $url after ${attempts}s" >&2
  return 1
}

stop_port() {
  local port="$1" label="$2"
  local pids; pids="$(port_pids "$port")"
  if [[ -n "$pids" ]]; then
    echo "[startup] stopping $label on port $port (pids: $pids)"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
    pids="$(port_pids "$port")"
    if [[ -n "$pids" ]]; then
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

cmd="${1:---run}"

case "$cmd" in
  --stop)
    stop_port "$BACKEND_PORT" backend
    stop_port "$FRONTEND_PORT" frontend
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
    echo "[startup] stopped."
    exit 0
    ;;
  --status)
    echo "--- backend ($BACKEND_PORT) ---"
    curl -sS --max-time 3 "http://127.0.0.1:$BACKEND_PORT/health" || echo "(no response)"
    echo
    echo "--- frontend ($FRONTEND_PORT) ---"
    curl -sS --max-time 3 -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:$FRONTEND_PORT/" || echo "(no response)"
    exit 0
    ;;
esac

# If anything is already listening on these ports, reuse or bail.
if [[ -n "$(port_pids "$BACKEND_PORT")" ]]; then
  echo "[startup] port $BACKEND_PORT already in use — reusing existing backend"
  BACKEND_ALREADY_UP=1
else
  BACKEND_ALREADY_UP=0
fi
if [[ -n "$(port_pids "$FRONTEND_PORT")" ]]; then
  echo "[startup] port $FRONTEND_PORT already in use — reusing existing frontend"
  FRONTEND_ALREADY_UP=1
else
  FRONTEND_ALREADY_UP=0
fi

# Local dev overrides — the committed .env is production-shaped (ENV=production,
# CORS locked to vercel). Export dev-friendly values so the local frontend can
# reach the API and moderation fails open on parse errors.
export ENV="${ENV_OVERRIDE:-development}"
export MODERATION_STRICT="${MODERATION_STRICT_OVERRIDE:-false}"
export FRONTEND_ORIGIN="${FRONTEND_ORIGIN_OVERRIDE:-http://127.0.0.1:$FRONTEND_PORT}"
export ALLOWED_ORIGINS="${ALLOWED_ORIGINS_OVERRIDE:-http://127.0.0.1:$FRONTEND_PORT,http://localhost:$FRONTEND_PORT}"
# Redis is optional for local dev — unset so rate-limit + cache run in-memory.
unset REDIS_URL
export RATE_LIMIT_USE_REDIS="false"
export RATE_LIMIT_STORAGE_URI="memory://"
export PYTHONUNBUFFERED=1

if [[ "$BACKEND_ALREADY_UP" == "0" ]]; then
  echo "[startup] launching backend: uvicorn backend.main:app --port $BACKEND_PORT"
  nohup "$PY" -m uvicorn backend.main:app \
    --host 0.0.0.0 --port "$BACKEND_PORT" \
    > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
fi

if [[ "$FRONTEND_ALREADY_UP" == "0" ]]; then
  echo "[startup] launching frontend: npx serve frontend -l $FRONTEND_PORT"
  nohup npx --yes serve "$REPO_ROOT/frontend" -l "$FRONTEND_PORT" \
    > "$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
fi

wait_for_http "http://127.0.0.1:$BACKEND_PORT/health" "backend" 90 || { tail -40 "$BACKEND_LOG" >&2; exit 1; }
wait_for_http "http://127.0.0.1:$FRONTEND_PORT/" "frontend" 30 || { tail -40 "$FRONTEND_LOG" >&2; exit 1; }

echo "[startup] ----------------------------------------"
echo "[startup] backend:  http://127.0.0.1:$BACKEND_PORT  (log: $BACKEND_LOG)"
echo "[startup] frontend: http://127.0.0.1:$FRONTEND_PORT (log: $FRONTEND_LOG)"
echo "[startup] ----------------------------------------"

if [[ "$cmd" == "--detach" ]]; then
  exit 0
fi

cleanup() {
  echo
  echo "[startup] shutting down..."
  [[ -f "$BACKEND_PID_FILE"  ]] && kill "$(cat "$BACKEND_PID_FILE")"  2>/dev/null || true
  [[ -f "$FRONTEND_PID_FILE" ]] && kill "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null || true
  sleep 1
  stop_port "$BACKEND_PORT" backend
  stop_port "$FRONTEND_PORT" frontend
  rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
}
trap cleanup INT TERM EXIT

# Stream logs so Ctrl-C is easy.
tail -n +1 -F "$BACKEND_LOG" "$FRONTEND_LOG"
