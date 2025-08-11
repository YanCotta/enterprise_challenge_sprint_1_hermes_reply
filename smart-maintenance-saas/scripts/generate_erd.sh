#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

: ${DATABASE_URL:="postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db"}
DB_URL_SYNC=${DATABASE_URL/"postgresql+asyncpg"/"postgresql"}

python - <<'PY'
import os
import sys
import subprocess

def ensure(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'eralchemy2', 'psycopg[binary]'])

ensure('eralchemy2')

from eralchemy2 import render_er

url = os.environ.get('DATABASE_URL', 'postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db')
url = url.replace('postgresql+asyncpg://', 'postgresql://')

os.makedirs('docs/db', exist_ok=True)
render_er(url, 'docs/db/erd.png')
print('ERD exported to docs/db/erd.png')
PY
