#!/bin/sh
set -eu

db_ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if python - <<'PY'
import os
import socket
import sys
from urllib.parse import urlparse

url = urlparse(os.environ.get("DATABASE_URL", ""))
host = url.hostname
port = url.port or 5432

if not host:
    sys.exit(1)

try:
    with socket.create_connection((host, port), timeout=2):
        pass
except OSError:
    sys.exit(1)
PY
  then
    db_ready=1
    break
  fi
  sleep 1
done

if [ "$db_ready" -eq 1 ]; then
  alembic upgrade head
fi

exec "$@"
