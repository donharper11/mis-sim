"""Isolated fault plants; source tree is never changed by the experiment."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
backend = root / 'backend'
plants = [
    ('generation', 'app/simulation/generation.py',
     'if expected_started_at is UNSPECIFIED_GENERATION:', 'if True:',
     'test_instructor_start.py::test_generation_mutations_refuse_recreated_run[sqlite]', 'DID NOT RAISE'),
    ('atomicity', 'app/simulation/service.py',
     '        return run\n\n    def initialize(', '        session.commit()\n        return run\n\n    def initialize(',
     'test_instructor_start.py::test_atomic_start_state_parity_rollback_retry[sqlite]', 'assert snapshot(db)==before'),
    ('runtime_inventory', 'app/services/instructor_start.py',
     '    for model in RUNTIME_TABLES:', '    for model in ():',
     'test_instructor_start.py::test_every_runtime_inventory_blocks_start_and_reset_recovers[sqlite]', 'AssertionError: round_schedule'),
    ('student_eligibility', 'app/services/instructor_start.py',
     'if user is None or not user.is_active or user.role != "student":', 'if user is None:',
     'test_instructor_start.py::test_readiness_eligibility_and_invalid_choices_are_read_only[sqlite]', 'assert (not True)'),
]
for name, filename, old, new, node, expected in plants:
    with tempfile.TemporaryDirectory(prefix=f'mis_sim_start_plant_{name}_') as directory:
        isolated = Path(directory)
        shutil.copytree(backend / 'app', isolated / 'app')
        (isolated / 'packs').symlink_to(backend / 'packs', target_is_directory=True)
        path = isolated / filename
        source = path.read_text()
        assert old in source, (name, 'plant target absent')
        path.write_text(source.replace(old, new, 1))
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', str(backend/'tests'/node)],
            cwd=isolated, env={**os.environ, 'PYTHONPATH': str(isolated)+':'+str(backend/'tests'),
            'SECRET_KEY':'instructor-start-isolated-plant', 'CASEPACK_ROOT': str(backend/'packs')},
            capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        (root/f'findings/instructor-start-2026-10-07/falsify-{name}.log').write_text(output)
        assert result.returncode == 1 and expected in output, (name, output)
        print(f'{name}: expected acceptance failure observed', flush=True)
