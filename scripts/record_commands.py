import subprocess, time, json, hashlib, sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path('.').resolve()
RUNTIME_DIR = REPO_ROOT / 'reports' / 'evidence' / 'report_runtime'
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

COMMANDS = [
    {
        'id': 'backend_regression_tests',
        'command': '.venv\\Scripts\\python.exe -m unittest backend.tests.test_refactored_system',
        'cmd_list': ['.venv/Scripts/python.exe', '-m', 'unittest', 'backend.tests.test_refactored_system'],
        'stdout_artifact': 'test_backend_output.txt',
        'stderr_artifact': None
    },
    {
        'id': 'evaluation_harness_tests',
        'command': '.venv\\Scripts\\python.exe -m unittest scripts.evaluation.tests.test_evaluation_harness',
        'cmd_list': ['.venv/Scripts/python.exe', '-m', 'unittest', 'scripts.evaluation.tests.test_evaluation_harness'],
        'stdout_artifact': 'test_harness_output.txt',
        'stderr_artifact': None
    },
    {
        'id': 'frontend_typecheck',
        'command': 'npx tsc --noEmit',
        'cmd_list': ['cmd.exe', '/c', 'npx tsc --noEmit'],
        'stdout_artifact': 'tsc_output.txt',
        'stderr_artifact': None
    },
    {
        'id': 'frontend_production_build',
        'command': 'npm run build',
        'cmd_list': ['cmd.exe', '/c', 'npm run build'],
        'stdout_artifact': 'build_output.txt',
        'stderr_artifact': None
    },
    {
        'id': 'verify_training_lineage',
        'command': '.venv\\Scripts\\python.exe scripts/verify_training_lineage_handoff.py',
        'cmd_list': ['.venv/Scripts/python.exe', 'scripts/verify_training_lineage_handoff.py'],
        'stdout_artifact': 'verify_lineage_output.txt',
        'stderr_artifact': None
    },
    {
        'id': 'verify_report_consistency',
        'command': '.venv\\Scripts\\python.exe scripts/verify_report_consistency.py',
        'cmd_list': ['.venv/Scripts/python.exe', 'scripts/verify_report_consistency.py'],
        'stdout_artifact': 'verify_consistency_output.txt',
        'stderr_artifact': None
    }
]

results = []

for c in COMMANDS:
    cid = c['id']
    cmd_str = c['command']
    print(f"Running: {cid} -> {cmd_str}")
    start_dt = datetime.now(timezone.utc)
    t0 = time.time()
    
    proc = subprocess.run(
        c['cmd_list'],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    t1 = time.time()
    end_dt = datetime.now(timezone.utc)
    duration = round(t1 - t0, 3)
    
    combined_output = proc.stdout
    if proc.stderr:
        combined_output += ('\n' + proc.stderr if combined_output else proc.stderr)
        
    out_file = RUNTIME_DIR / c['stdout_artifact']
    out_file.write_text(combined_output, encoding='utf-8')
    
    sha256 = hashlib.sha256(out_file.read_bytes()).hexdigest()
    
    res = {
        'id': cid,
        'command': cmd_str,
        'cwd': '.',
        'start_time': start_dt.isoformat(),
        'end_time': end_dt.isoformat(),
        'duration_seconds': duration,
        'exit_code': proc.returncode,
        'stdout_artifact': c['stdout_artifact'],
        'stderr_artifact': c['stderr_artifact'],
        'artifact_sha256': sha256,
        'status': 'PASS' if proc.returncode == 0 else 'FAIL'
    }
    results.append(res)
    print(f"  Status: {res['status']} (exit {proc.returncode}, {duration}s, SHA: {sha256[:16]}...)")

results_payload = {
    'schema_version': '1.0',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'overall_status': 'PASS' if all(r['status'] == 'PASS' for r in results) else 'FAIL',
    'total_commands': len(results),
    'passed_commands': sum(1 for r in results if r['status'] == 'PASS'),
    'failed_commands': sum(1 for r in results if r['status'] == 'FAIL'),
    'results': results
}

cmd_results_file = RUNTIME_DIR / 'COMMAND_RESULTS.json'
cmd_results_file.write_text(json.dumps(results_payload, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"Saved: {cmd_results_file} (Overall status: {results_payload['overall_status']})")
