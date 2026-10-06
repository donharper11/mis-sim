"""The permanent SQLite barrier test must detect omitted reset reservation."""
from pathlib import Path
import os, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[2]
backend=root/'backend'
with tempfile.TemporaryDirectory(prefix='mis_sim_reset_start_plant_') as directory:
    isolated=Path(directory)
    shutil.copytree(backend/'app', isolated/'app')
    (isolated/'packs').symlink_to(backend/'packs', target_is_directory=True)
    path=isolated/'app/services/platform.py'
    source=path.read_text()
    begin=source.index('    if session.bind.dialect.name == "sqlite":',source.index('async def reset_instance('))
    end=source.index('    # NO KEY UPDATE',begin)
    path.write_text(source[:begin]+source[end:])
    result=subprocess.run(['/tmp/mis-sim-readiness-venv/bin/python','-m','pytest','-q',str(backend/'tests/test_instructor_start_sqlite_reset.py')+'::test_sqlite_reset_eligibility_boundary_blocks_start_until_commit'],cwd=isolated,env={**os.environ,'PYTHONPATH':str(isolated)+':'+str(backend/'tests'),'SECRET_KEY':'independent-reset-plant','CASEPACK_ROOT':str(backend/'packs')},capture_output=True,text=True,timeout=60)
    (root/'findings/instructor-start-2026-10-07/falsify-sqlite-reset.log').write_text(result.stdout+result.stderr)
    assert result.returncode==1 and 'DID NOT RAISE' in result.stdout, result.stdout+result.stderr
    print('PASS removing reset writer reservation defeats actual blocked-writer assertion')
