"""Prove the new scheduler test detects a missing metadata-generation guard."""
from pathlib import Path
import os,shutil,subprocess,tempfile
root=Path(__file__).resolve().parents[2]
backend=root/'backend'
with tempfile.TemporaryDirectory(prefix='mis_sim_start_scheduler_plant_') as directory:
    isolated=Path(directory)
    shutil.copytree(backend/'app',isolated/'app')
    (isolated/'packs').symlink_to(backend/'packs', target_is_directory=True)
    path=isolated/'app/scheduling/service.py'
    source=path.read_text()
    begin=source.index('    def _guard_generation(')
    end=source.index('    def _conditional_participant_update(',begin)
    source=source[:begin]+'    def _guard_generation(self, schedule_id, instance_id, expected_started_at):\n        return None\n\n'+source[end:]
    path.write_text(source)
    result=subprocess.run(['/tmp/mis-sim-readiness-venv/bin/python','-m','pytest','-q',str(backend/'tests/test_instructor_start_scheduler.py')+'::test_scheduler_captured_entry_rejects_replacement_metadata[sqlite-lock_now]'],cwd=isolated,env={**os.environ,'PYTHONPATH':str(isolated)+':'+str(backend/'tests'),'SECRET_KEY':'independent-scheduler-plant','CASEPACK_ROOT':str(backend/'packs')},capture_output=True,text=True,timeout=120)
    (root/'findings/instructor-start-2026-10-07/falsify-scheduler-metadata.log').write_text(result.stdout+result.stderr)
    assert result.returncode==1 and 'assert snapshot(db) == replacement' in result.stdout,result.stdout+result.stderr
    print('PASS expected replacement-snapshot failure with metadata guard removed; production source unchanged')
