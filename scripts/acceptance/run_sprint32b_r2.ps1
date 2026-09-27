param(
    [switch]$SkipZipPackaging
)

# ==============================================================================
# SPRINT 3.2B-R2 -- MASTER ACCEPTANCE RUNNER (FAIL-CLOSED)
# ==============================================================================
# Executes all test suites, benchmarks, audits, git extractions, and validations
# sequentially with exact timestamps, raw log capture, step exit code accounting,
# isolated database copy created via SQLite Online Backup API, fail-closed isolation
# preflight assertion, and production database guard monitoring.
# ==============================================================================

$projectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $projectRoot

$artifactsDir = Join-Path $projectRoot "artifacts\sprint_3_2b_r2"

# Safe clean of artifacts directory at start
if (Test-Path $artifactsDir) {
    Get-ChildItem -Path $artifactsDir -Recurse | Remove-Item -Force -Recurse
} else {
    New-Item -ItemType Directory -Path $artifactsDir -Force | Out-Null
}

$runId = "sprint32b_r2_" + (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$env:ACCEPTANCE_RUN_ID = $runId
Set-Content -Path (Join-Path $artifactsDir "run_id.txt") -Value $runId -Encoding utf8

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

# ------------------------------------------------------------------------------
# 1. INITIALIZE PRODUCTION DATABASE FAIL-CLOSED GUARD (BEFORE SNAPSHOT)
# ------------------------------------------------------------------------------
$mainDbPath = Join-Path $projectRoot "cheating_system.db"
if (-not (Test-Path $mainDbPath)) {
    Write-Host "[FATAL GUARD] Main database $mainDbPath does not exist!" -ForegroundColor Red
    exit 1
}

$guardFile = Join-Path $artifactsDir "production_db_guard.json"
Write-Host "[*] Recording production database baseline (before snapshot)..." -ForegroundColor Cyan
& "$pythonExe" scripts/acceptance/db_guard.py baseline --guard-file $guardFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL GUARD] Failed to record production DB baseline!" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------------------
# 2. CREATE ISOLATED DATABASE VIA SQLITE ONLINE BACKUP API
# ------------------------------------------------------------------------------
Write-Host "[*] Creating isolated database snapshot via SQLite Online Backup API..." -ForegroundColor Cyan
& "$pythonExe" scripts/acceptance/create_isolated_snapshot.py --run-id $runId
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL GUARD] create_isolated_snapshot.py failed with exit code $LASTEXITCODE!" -ForegroundColor Red
    exit 1
}

# Immediately verify production DB guard after snapshot creation
& "$pythonExe" scripts/acceptance/db_guard.py check --step "SNAPSHOT" --guard-file $guardFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL GUARD] Main DB was mutated during isolated snapshot creation!" -ForegroundColor Red
    exit 1
}

$isolatedDbPath = (Resolve-Path "data\isolated_acceptance\$runId\isolated_acceptance.db").Path
if (-not (Test-Path $isolatedDbPath)) {
    Write-Host "[FATAL GUARD] Isolated database $isolatedDbPath was not found after snapshot creation!" -ForegroundColor Red
    exit 1
}

# Export environment variables for child Python processes
$env:AIEXAM_ISOLATED_DB = $isolatedDbPath
$env:DATABASE_URL = "sqlite:///$($isolatedDbPath.Replace('\', '/'))"
Write-Host "[DB-ISOLATION] Environment set: AIEXAM_ISOLATED_DB = $isolatedDbPath" -ForegroundColor Green
Write-Host "[DB-ISOLATION] Environment set: DATABASE_URL = $env:DATABASE_URL" -ForegroundColor Green

# ------------------------------------------------------------------------------
# 3. FAIL-CLOSED ISOLATION PREFLIGHT CHECK
# ------------------------------------------------------------------------------
Write-Host "[*] Executing fail-closed database isolation preflight..." -ForegroundColor Cyan
& "$pythonExe" scripts/acceptance/preflight_db_isolation.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL GUARD] preflight_db_isolation.py failed! Aborting pipeline before any test runs." -ForegroundColor Red
    exit 1
}

$mainDbInitialHash = (Get-FileHash -Algorithm SHA256 $mainDbPath).Hash
@{
    run_id = $runId
    started_at = (Get-Date).ToUniversalTime().ToString("o")
    platform = "windows"
    python = $pythonExe
    main_db_sha256 = $mainDbInitialHash
    isolated_db = $isolatedDbPath
} | ConvertTo-Json | Set-Content -Path (Join-Path $artifactsDir "run_info.json") -Encoding utf8

# ------------------------------------------------------------------------------
# 4. PRE-TEST CONTAMINATION AUDIT (IMMEDIATELY AFTER SNAPSHOT, BEFORE STEP-01)
# ------------------------------------------------------------------------------
Write-Host "[*] Auditing database test data contamination (pre-test snapshot)..." -ForegroundColor Cyan
& "$pythonExe" scripts/acceptance/audit_test_data_contamination.py --pre-test
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL AUDIT] Pre-test contamination audit failed!" -ForegroundColor Red
    exit 1
}

$script:results = @()
$script:hasFailed = $false

function Run-AcceptanceStep {
    param (
        [string]$StepId,
        [string]$Description,
        [string]$CommandStr,
        [string]$LogFileName
    )

    $logPath = if ($StepId -eq "STEP-16") {
        Join-Path $projectRoot "step16_exec.log"
    } elseif ($StepId -eq "STEP-17") {
        Join-Path $projectRoot "step17_packaging.log"
    } else {
        Join-Path $artifactsDir $LogFileName
    }

    $startTime = Get-Date
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    Write-Host "`n" ("=" * 80) -ForegroundColor Cyan
    Write-Host "[$StepId] $Description" -ForegroundColor Cyan
    Write-Host "Command: $CommandStr" -ForegroundColor Gray
    Write-Host "Log:     $logPath" -ForegroundColor Gray
    Write-Host ("=" * 80)

    # Execute command with inherited environment variables (including AIEXAM_ISOLATED_DB and DATABASE_URL)
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = "powershell.exe"
    $processInfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"$CommandStr`""
    $processInfo.WorkingDirectory = $projectRoot
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    $process.Start() | Out-Null

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    $process.WaitForExit()
    $sw.Stop()
    $endTime = Get-Date

    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $exitCode = $process.ExitCode

    # Combine log
    $fullLog = "================================================================================`n" +
               "RUN ID:   $runId`n" +
               "COMMAND:  $CommandStr`n" +
               "START:    $($startTime.ToString('o'))`n" +
               "END:      $($endTime.ToString('o'))`n" +
               "DURATION: $($sw.Elapsed.TotalSeconds.ToString('F2'))s`n" +
               "EXIT CODE: $exitCode`n" +
               "================================================================================`n`n" +
               "--- STDOUT ---`n$stdout`n" +
               "--- STDERR ---`n$stderr"

    Set-Content -Path $logPath -Value $fullLog -Encoding utf8

    $status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
    $color = if ($exitCode -eq 0) { "Green" } else { "Red" }

    if ($StepId -eq "STEP-10") {
        if ($exitCode -eq 0) {
            $status = "NOT_CONFIGURED"
            $color = "Yellow"
        } else {
            $status = "FAIL"
            $color = "Red"
            $script:hasFailed = $true
        }
    } else {
        if ($exitCode -ne 0) {
            $script:hasFailed = $true
        }
    }

    # Production DB Guard check after every step
    if ($StepId -eq "STEP-16" -or $StepId -eq "STEP-17") {
        & "$pythonExe" scripts/acceptance/db_guard.py check --step $StepId --guard-file $guardFile --read-only
    } else {
        & "$pythonExe" scripts/acceptance/db_guard.py check --step $StepId --guard-file $guardFile
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[FATAL DB-GUARD VIOLATION] Main DB check failed after $StepId!" -ForegroundColor Red
        $script:hasFailed = $true
        exit 1
    }

    Write-Host ">>> [$StepId] STATUS: $status | Exit Code: $exitCode | Duration: $($sw.Elapsed.TotalSeconds.ToString('F2'))s" -ForegroundColor $color

    $stepResult = [PSCustomObject]@{
        step_id = $StepId
        description = $Description
        command = $CommandStr
        log_file = $LogFileName
        start_time = $startTime.ToString("o")
        end_time = $endTime.ToString("o")
        duration_seconds = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        exit_code = $exitCode
        status = $status
    }
    $script:results += $stepResult
    return $exitCode
}

Write-Host "`n" ("#" * 80) -ForegroundColor Yellow
Write-Host "# STARTING SPRINT 3.2B-R2 EVIDENCE CLOSURE PIPELINE (FAIL-CLOSED)" -ForegroundColor Yellow
Write-Host "# Root:   $projectRoot" -ForegroundColor Yellow
Write-Host "# Run ID: $runId" -ForegroundColor Yellow
Write-Host ("#" * 80)

# Step 1: Import Side-Effect Audit
Run-AcceptanceStep -StepId "STEP-01" `
    -Description "Import Side-Effect and Metadata Audit (3 Checkpoints, 7 Parameters)" `
    -CommandStr "& `"$pythonExe`" scripts/acceptance/audit_import_side_effects.py" `
    -LogFileName "import_side_effect_audit.log"

# Step 2: Read-Only SQLite Confidence Migration Audit
Run-AcceptanceStep -StepId "STEP-02" `
    -Description "Read-Only SQLite Confidence Migration and Integrity Audit" `
    -CommandStr "& `"$pythonExe`" scripts/acceptance/audit_db_migration.py" `
    -LogFileName "confidence_migration_audit.log"

# Step 3: Backend Aggregate Test Suite
Run-AcceptanceStep -StepId "STEP-03" `
    -Description "Backend All Test Suites (Refactored, DualCamera, Sprint32B, Preview, ConfidenceContract)" `
    -CommandStr "& `"$pythonExe`" -m unittest backend.tests.test_refactored_system backend.tests.test_dual_camera_pipeline backend.tests.test_sprint32b backend.tests.test_preview_transport backend.tests.test_confidence_contract -v" `
    -LogFileName "backend_all_tests.log"

# Step 4: Preview WebSocket Transport Tests
Run-AcceptanceStep -StepId "STEP-04" `
    -Description "Preview WebSocket Deep Integration and Invariants Test" `
    -CommandStr "& `"$pythonExe`" -m unittest backend.tests.test_preview_transport -v" `
    -LogFileName "preview_transport.log"

# Step 5: Evaluation Harness Tests
Run-AcceptanceStep -StepId "STEP-05" `
    -Description "Evaluation Harness Mathematical Contract Tests" `
    -CommandStr "& `"$pythonExe`" -m unittest scripts.evaluation.tests.test_evaluation_harness -v" `
    -LogFileName "evaluation_tests.log"

# Step 6: Frontend TypeScript Strict Type Check
Run-AcceptanceStep -StepId "STEP-06" `
    -Description "Frontend TypeScript Strict Type Check" `
    -CommandStr "npx tsc --noEmit" `
    -LogFileName "tsc.log"

# Step 7: Frontend Telemetry Contract Tests
Run-AcceptanceStep -StepId "STEP-07" `
    -Description "Frontend Telemetry Contract Verification" `
    -CommandStr "npx tsx src/services/__tests__/test_telemetry_contract.ts" `
    -LogFileName "frontend_telemetry.log"

# Step 8: Frontend Dual-Camera Contract Tests
Run-AcceptanceStep -StepId "STEP-08" `
    -Description "Frontend Dual-Camera UI and Protocol Contract Test" `
    -CommandStr "npx tsx src/services/__tests__/test_frontend_dual_camera.ts" `
    -LogFileName "frontend_dual_camera.log"

# Step 9: Frontend Production Bundle Build
Run-AcceptanceStep -StepId "STEP-09" `
    -Description "Vite Production Bundle Build" `
    -CommandStr "npm run build" `
    -LogFileName "build.log"

# Step 10: Frontend lint configuration audit — NOT_CONFIGURED
Run-AcceptanceStep -StepId "STEP-10" `
    -Description "Frontend lint configuration audit — NOT_CONFIGURED" `
    -CommandStr "npm run lint" `
    -LogFileName "lint.log"

# Step 11: Dual-Camera Evidence Clip Generation & Pre/Post-Roll Audit
Run-AcceptanceStep -StepId "STEP-11" `
    -Description "Dual-Camera Evidence Clip Generation and Pre/Post-Roll Audit" `
    -CommandStr "& `"$pythonExe`" scripts/acceptance/generate_evidence_clips_r2.py" `
    -LogFileName "clip_audit.log"

# Step 12: Memory Benchmark Scenario A (640x480 @ 15 FPS, >=62s)
Run-AcceptanceStep -StepId "STEP-12" `
    -Description "Dual-Camera 62s Memory Benchmark Scenario A (640x480 @ 15 FPS)" `
    -CommandStr "& `"$pythonExe`" scripts/benchmark/benchmark_dual_camera.py --scenario A --duration 62.0" `
    -LogFileName "benchmark_640x480.log"

# Step 13: Memory Benchmark Scenario B (1920x1080 @ 15 FPS, >=62s)
Run-AcceptanceStep -StepId "STEP-13" `
    -Description "Dual-Camera 62s Memory Benchmark Scenario B (1920x1080 @ 15 FPS)" `
    -CommandStr "& `"$pythonExe`" scripts/benchmark/benchmark_dual_camera.py --scenario B --duration 62.0" `
    -LogFileName "benchmark_1920x1080.log"

# Step 14: Git Status & Diff Evidence Capture
Run-AcceptanceStep -StepId "STEP-14" `
    -Description "Git Repository Status, Diff & Untracked Evidence Capture" `
    -CommandStr "& `"$pythonExe`" scripts/acceptance/capture_git_state_r2.py" `
    -LogFileName "git_capture.log"

# Post-test contamination accounting on isolated database
Write-Host "`n[*] Auditing database test data contamination (post-test delta accounting)..." -ForegroundColor Cyan
& "$pythonExe" scripts/acceptance/audit_test_data_contamination.py --post-test
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL AUDIT] Post-test contamination accounting failed!" -ForegroundColor Red
    exit 1
}

# Dynamically generate SPRINT_3_2B_R2_REPORT.md from actual execution outputs of STEP-01 to STEP-14
Write-Host "`n[*] Dynamically generating SPRINT_3_2B_R2_REPORT.md from live test/benchmark metrics..." -ForegroundColor Cyan
& "$pythonExe" scripts/acceptance/generate_report_r2.py

# Step 15: Secret and Credential Leakage Scan
Run-AcceptanceStep -StepId "STEP-15" `
    -Description "Secret and Credential Leakage Scan Across Code, Dist, DB, Logs, Patch, and Snapshot" `
    -CommandStr "& `"$pythonExe`" scripts/acceptance/secret_scan_r2.py" `
    -LogFileName "secret_scan.log"

# Finalize Production DB Guard before manifest freeze so production_db_guard.json is frozen with final status
Write-Host "`n[*] Finalizing Production DB Guard before artifact manifest freeze..." -ForegroundColor Cyan
& "$pythonExe" scripts/acceptance/db_guard.py finalize --guard-file $guardFile --copy-to (Join-Path $projectRoot "production_db_guard.json")
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL GUARD VIOLATION] Final DB guard check failed!" -ForegroundColor Red
    exit 1
}

# Re-run report generation to capture finalized guard and secret scan stats into final report
& "$pythonExe" scripts/acceptance/generate_report_r2.py

# Step 16: Artifact Integrity & SHA-256 Manifest Generation (Builds acceptance_summary.json, closes artifact_validation.log, freezes manifest)
Run-AcceptanceStep -StepId "STEP-16" `
    -Description "Artifact Integrity and SHA-256 Manifest Generation" `
    -CommandStr "& `"$pythonExe`" scripts/acceptance/validate_artifacts_r2.py" `
    -LogFileName "artifact_validation.log"

if ($SkipZipPackaging -or ($env:SKIP_ZIP_PACKAGING -eq "1")) {
    Write-Host "`n" ("=" * 80) -ForegroundColor Yellow
    Write-Host "[*] SkipZipPackaging is ACTIVE -- halting pipeline before STEP-17." -ForegroundColor Yellow
    Write-Host "    Artifacts frozen and sha256_manifest.txt generated cleanly." -ForegroundColor Yellow
    Write-Host "    Awaiting PM semantic review before packaging SPRINT_3_2B_R2_EVIDENCE.zip." -ForegroundColor Yellow
    Write-Host ("=" * 80)
} else {
    # Step 17: Package Zip Archive and Execute External Cross-Validation (Log and Handoff written OUTSIDE ZIP)
    Run-AcceptanceStep -StepId "STEP-17" `
        -Description "Evidence Zip Packaging and External Integrity Validation" `
        -CommandStr "& `"$pythonExe`" scripts/acceptance/package_and_validate_zip_r2.py" `
        -LogFileName "FINAL_ZIP_VALIDATION.log"
}

# Final Acceptance Summary JSON update (written at project root)
$finalFailed = $script:hasFailed -or (($script:results | Where-Object { $_.status -eq "FAIL" }).Count -gt 0)
$verdictStr = if (-not $finalFailed) { "PASS WITH RESIDUAL RISKS — SOFTWARE/SYNTHETIC ACCEPTANCE" } else { "FAIL" }

Write-Host "`n" ("=" * 80) -ForegroundColor Yellow
Write-Host "FINAL MASTER ACCEPTANCE RUN COMPLETED" -ForegroundColor Yellow
Write-Host "CANDIDATE VERDICT: $verdictStr" -ForegroundColor $(if (-not $finalFailed) { "Green" } else { "Red" })
Write-Host "FINAL PM VERDICT:  PENDING INDEPENDENT ARTIFACT AUDIT" -ForegroundColor Yellow
Write-Host ("=" * 80)

if (-not $finalFailed) {
    exit 0
} else {
    exit 1
}
