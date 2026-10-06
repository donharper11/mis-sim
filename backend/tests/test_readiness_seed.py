"""The disposable seed must initialize both sections without overlapping writers."""
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
import tempfile


def test_sqlite_readiness_seed_initializes_all_teams_and_refuses_reuse():
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'seed_readiness_demo.py'
    with tempfile.TemporaryDirectory(prefix='mis_sim_browser_', dir='/tmp') as directory:
        database = Path(directory) / 'seed.db'
        command = [sys.executable, str(script), '--database-url', f'sqlite+aiosqlite:///{database}']
        env = {**os.environ, 'SECRET_KEY': 'readiness-seed-test-only'}
        result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=90)
        assert result.returncode == 0, result.stdout + result.stderr
        with sqlite3.connect(database) as connection:
            assert connection.execute('SELECT count(*) FROM simulation_run_v1 WHERE current_round=1').fetchone()[0] == 4
            assert connection.execute("SELECT count(*) FROM simulation_instance WHERE current_round=1 AND status='active'").fetchone()[0] == 2
            before = '\n'.join(connection.iterdump())
        refused = subprocess.run(command, capture_output=True, text=True, env=env, timeout=90)
        assert refused.returncode != 0
        assert 'database already has users' in refused.stdout + refused.stderr
        with sqlite3.connect(database) as connection:
            assert '\n'.join(connection.iterdump()) == before
