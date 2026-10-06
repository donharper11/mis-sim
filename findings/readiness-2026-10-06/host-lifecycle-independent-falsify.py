"""Run three actual acceptance tests against isolated predecessor-behavior plants."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import sys

ROOT=Path(__file__).resolve().parents[2]
BACKEND=ROOT/'backend'
TEST=BACKEND/'tests/test_host_lifecycle.py'
PLANTS={
 'timing': 'test_activation_atomic_retry_parity_and_final_horizon[sqlite]',
 'pending_only': 'test_pending_only_writes_and_authoritative_round[sqlite]',
 'reset_inventory': 'test_reset_all_runtime_preservation_rejection_and_rollback[sqlite]',
}
for plant,test in PLANTS.items():
 if len(sys.argv)>1 and plant not in sys.argv[1:]:continue
 with tempfile.TemporaryDirectory(prefix='mis_sim_host_falsify_') as directory:
  root=Path(directory);shutil.copytree(BACKEND/'app',root/'app')
  if plant=='timing':
   p=root/'app/services/host_lifecycle.py';s=p.read_text();s=s[:s.index('    session.execute')]+ '    return None\n';p.write_text(s)
  elif plant=='pending_only':
   p=root/'app/api/runtime_host_platform.py';s=p.read_text().replace('    if platform.status != "pending":\n        raise HTTPException(status_code=409, detail="Only pending platforms can be changed")\n','');p.write_text(s)
  else:
   p=root/'app/services/platform.py';s=p.read_text().replace('RoundScheduleTeam, RoundSchedule, HostPlatformMember, HostPlatform,','RoundScheduleTeam, RoundSchedule,').replace('*reversed(round_models.ALL_TABLES), GradeOverride, GradeConfig,','round_models.RoundResult, GradeOverride, GradeConfig,');p.write_text(s)
  result=subprocess.run(['/tmp/mis-sim-readiness-venv/bin/python','-m','pytest','-q',str(TEST)+'::'+test],cwd=root,env={**os.environ,'PYTHONPATH':str(root)+':'+str(BACKEND/'tests'),'SECRET_KEY':'falsification-only'},capture_output=True,text=True,timeout=240)
  (ROOT/'findings/readiness-2026-10-06'/f'host-lifecycle-independent-falsify-{plant}.log').write_text(result.stdout+result.stderr)
  assert result.returncode==1,(plant,result.returncode,result.stdout,result.stderr)
  assert 'AssertionError' in result.stdout,(plant,result.stdout)
  print(plant+': expected acceptance failure observed',flush=True)
