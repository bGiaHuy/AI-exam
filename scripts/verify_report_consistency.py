#!/usr/bin/env python3
"""
scripts/verify_report_consistency.py
------------------------------------
Sprint 4.0B Consistency Check Script.
Checks target files for forbidden words, patterns, or prohibited claims:
1. Forbidden phrases (including Sprint 4.0B telemetry/privacy/performance claims).
2. D-02 definition (must not require out-of-distribution / ngoài phân phối as prerequisite).
3. 3-frame discrepancy (must not contain unproven network backlog speculations).
4. References classification (distinguishes IMPLEMENTATION_VERIFIED vs BIBLIOGRAPHY_PENDING_VERIFICATION).
5. Readiness Matrix (verifies exact 9 rows and statuses in REPORT_EVIDENCE_PACK.md).
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

TARGET_FILES = [
    Path('reports/BAO_CAO_KHKT_DRAFT_V0_1.md'),
    Path('reports/REPORT_SOURCE_PACK.md'),
    Path('reports/REPORT_CLAIM_EVIDENCE_MATRIX.md'),
    Path('reports/REPORT_EVIDENCE_PACK.md'),
    Path('reports/REPORT_GAP_REGISTER.md'),
    Path('reports/SYSTEM_SCOPE_FREEZE.md')
]

# Patterns that indicate forbidden content
FORBIDDEN_PATTERNS = [
    (r'\bFaceNet\b', 'FaceNet mention (prohibited in active scope)'),
    (r'\bRAG\b', 'RAG mention (prohibited in active scope)'),
    (r'sinh biên bản|lập biên bản', 'Protocol/minutes generation (prohibited in active scope)'),
    (r'chữ ký số', 'Digital signature (prohibited in active scope)'),
    (r'100% chính xác', '100% accurate claim (prohibited)'),
    (r'zero technical debt', 'Zero technical debt claim (prohibited)'),
    (r'production[- ]ready', 'Production ready claim (prohibited)'),
    (r'không có rủi ro', 'Zero risk claim (prohibited)'),
    (r'khớp 100%', 'khớp 100% claim (prohibited)'),
    (r'giống nhau 100%', 'giống nhau 100% claim (prohibited)'),
    (r'phục hồi đầy đủ', 'phục hồi đầy đủ claim (prohibited)'),
    (r'kiểm chứng thực nghiệm 100%', 'kiểm chứng thực nghiệm 100% (prohibited)'),
    (r'tách biệt độc lập 100%', 'tách biệt độc lập 100% (prohibited)'),
    (r'vận hành ngoại tuyến 100%', 'vận hành ngoại tuyến 100% (prohibited)'),
    (r'loại bỏ hoàn toàn', 'loại bỏ hoàn toàn (prohibited)'),
    (r'bằng chứng khách quan', 'bằng chứng khách quan (prohibited)'),
    (r'xóa ngay lập tức', 'xóa ngay lập tức (prohibited)'),
    (r'Face\s*Yaw', 'Face Yaw angle claim (prohibited)'),
    (r'góc\s*mặt', 'góc mặt claim (prohibited)'),
    (r'đo góc quay đầu', 'đo góc quay đầu claim (prohibited)'),
    # Sprint 4.0B Specific Forbidden Patterns
    (r'ẩn danh tuyệt đối', 'ẩn danh tuyệt đối (prohibited Sprint 4.0B)'),
    (r'không xử lý PII', 'không xử lý PII (prohibited Sprint 4.0B)'),
    (r'packet loss\s*0%|0%\s*packet loss', 'packet loss 0% (prohibited Sprint 4.0B)'),
    (r'mất gói\s*0%|0%\s*mất gói', 'mất gói 0% (prohibited Sprint 4.0B)'),
    (r'WebSocket reliability 100%', 'WebSocket reliability 100% (prohibited Sprint 4.0B)'),
    (r'không có frame mất trên toàn tuyến', 'không có frame mất trên toàn tuyến (prohibited Sprint 4.0B)'),
    (r'giải phóng hoàn toàn khỏi RAM', 'giải phóng hoàn toàn khỏi RAM (prohibited Sprint 4.0B)'),
    (r'triệt tiêu độ trễ', 'triệt tiêu độ trễ (prohibited Sprint 4.0B)'),
    (r'còn trên đường truyền khi socket đóng', 'còn trên đường truyền khi socket đóng (unproven speculation Sprint 4.0B)'),
    (r'tồn đọng trên network buffer', 'tồn đọng trên network buffer (unproven speculation Sprint 4.0B)')
]

def check_forbidden_patterns(path: Path) -> int:
    print(f"\n=== CHECKING FORBIDDEN PATTERNS: {path.name} ===")
    if not path.exists():
        print(f"File not found: {path}")
        return 1
    
    lines = path.read_text(encoding='utf-8').splitlines()
    matches_found = []
    active_errors = 0
    
    for idx, line in enumerate(lines, 1):
        for pattern, desc in FORBIDDEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if it is in an explicit negation / exclusion / audit context
                line_lower = line.lower()
                negation_words = [
                    'không', 'tuyệt đối không', 'loại bỏ', 'cấm', 'out-of-scope', 
                    'chưa', 'bác bỏ', 'unsupported', 'do not publish', 'legacy asset',
                    'gap-', 'khiếm khuyết', 'thành phần loại bỏ', 'ngoài phạm vi', 'non-goals',
                    'hạn chế', 'ranh giới', 'quy tắc', 'tránh'
                ]
                is_negation = any(nw in line_lower for nw in negation_words)
                # Specific check: if the pattern itself begins with 'không' (e.g. 'không xử lý PII'),
                # check if there's an outer rejection
                if pattern in [r'không xử lý PII', r'không có frame mất trên toàn tuyến']:
                    rejection_words = ['cấm', 'bỏ toàn bộ', 'loại', 'không dùng', 'tránh']
                    is_negation = any(rw in line_lower for rw in rejection_words)
                
                if not is_negation:
                    active_errors += 1
                matches_found.append({
                    'line_num': idx,
                    'line': line.strip(),
                    'pattern': pattern,
                    'desc': desc,
                    'is_negated_or_prohibited_context': is_negation
                })
    
    if not matches_found:
        print("[OK] No forbidden pattern matches found.")
    else:
        for m in matches_found:
            status = "[OK: NEGATED / OUT-OF-SCOPE CONTEXT]" if m['is_negated_or_prohibited_context'] else "[ERROR: ACTIVE OCCURRENCE]"
            print(f"  Line {m['line_num']} | {status} | Pattern: '{m['pattern']}' ({m['desc']})")
            print(f"    Content: {m['line'][:100]}...")
    
    return active_errors

def check_d02_definition(path: Path) -> int:
    """Check that D-02 does not mandate OOD as a prerequisite."""
    print(f"\n=== CHECKING D-02 DEFINITION IN {path.name} ===")
    text = path.read_text(encoding='utf-8')
    errors = 0
    
    for idx, line in enumerate(text.splitlines(), 1):
        if 'D-02' in line or 'D02' in line:
            line_lower = line.lower()
            # If OOD is mentioned, it MUST state it is a separate/additional evaluation
            if 'out-of-distribution' in line_lower or 'ngoài phân phối' in line_lower or 'ood' in line_lower:
                if 'bổ sung' not in line_lower and 'tách biệt' not in line_lower and 'riêng' not in line_lower:
                    print(f"  [ERROR: Line {idx}] D-02 mentions OOD without clarifying it is separate/additional: {line.strip()[:100]}")
                    errors += 1
    if errors == 0:
        print("[OK] D-02 definition verified (OOD not required as prerequisite).")
    return errors

def check_readiness_matrix() -> int:
    """Verify 9-row Readiness Matrix in REPORT_EVIDENCE_PACK.md."""
    print("\n=== CHECKING READINESS MATRIX IN REPORT_EVIDENCE_PACK.md ===")
    path = Path('reports/REPORT_EVIDENCE_PACK.md')
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return 1
    
    text = path.read_text(encoding='utf-8')
    expected_rows = [
        ("Kiến trúc / backend / database / UI runtime", "READY_VERIFIED_WITH_DEFINED_SCOPE"),
        ("Historical training setup", "READY_VERIFIED_WITH_CAVEATS"),
        ("Logic head-turning trong code", "READY_VERIFIED_WITH_DEFINED_SCOPE"),
        ("Cơ sở lý thuyết và bibliography", "DRAFTABLE_PENDING_CITATIONS"),
        ("Phone independent evaluation", "BLOCKED_D02"),
        ("Head-turning ground-truth evaluation", "BLOCKED_D03"),
        ("Tóm tắt (Abstract)", "DRAFTABLE_WITH_CAVEAT"),
        ("Kết luận (Conclusion)", "DRAFTABLE_WITH_CAVEAT"),
        ("Báo cáo Word cuối", "PENDING_PM_REVIEW"),
    ]
    
    errors = 0
    for item_name, expected_status in expected_rows:
        pattern = re.compile(rf"\|\s*{re.escape(item_name)}\s*\|\s*`?{re.escape(expected_status)}`?\s*\|", re.IGNORECASE)
        if not pattern.search(text):
            print(f"  [ERROR] Missing or incorrect Readiness Matrix row for: '{item_name}' (expected '{expected_status}')")
            errors += 1
        else:
            print(f"  [OK] Found row: {item_name} -> {expected_status}")
            
    return errors

def check_references_classification() -> int:
    """Verify references section in BAO_CAO_KHKT_DRAFT_V0_1.md distinguishes implementation vs bibliography."""
    print("\n=== CHECKING REFERENCES CLASSIFICATION IN BAO_CAO_KHKT_DRAFT_V0_1.md ===")
    path = Path('reports/BAO_CAO_KHKT_DRAFT_V0_1.md')
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return 1
    
    text = path.read_text(encoding='utf-8')
    has_impl_verified = "IMPLEMENTATION_VERIFIED" in text
    has_bib_pending = "BIBLIOGRAPHY_PENDING_VERIFICATION" in text
    
    errors = 0
    if not has_impl_verified:
        print("  [ERROR] Missing IMPLEMENTATION_VERIFIED marker in Section 14")
        errors += 1
    else:
        print("  [OK] IMPLEMENTATION_VERIFIED marker found.")
        
    if not has_bib_pending:
        print("  [ERROR] Missing BIBLIOGRAPHY_PENDING_VERIFICATION marker in Section 14")
        errors += 1
    else:
        print("  [OK] BIBLIOGRAPHY_PENDING_VERIFICATION marker found.")
        
    return errors

def main():
    print("=== SPRINT 4.0B COMPREHENSIVE REPORT CONSISTENCY CHECK ===")
    total_errors = 0
    
    # 1. Check forbidden patterns across all report files
    for target in TARGET_FILES:
        total_errors += check_forbidden_patterns(target)
        total_errors += check_d02_definition(target)

    # 2. Check 9-row Readiness Matrix
    total_errors += check_readiness_matrix()
    
    # 3. Check references distinction
    total_errors += check_references_classification()

    print(f"\n==========================================")
    if total_errors == 0:
        print(f"RESULT: PASS (All {len(TARGET_FILES)} report files clean, 0 active errors)")
        sys.exit(0)
    else:
        print(f"RESULT: FAIL ({total_errors} active errors found)")
        sys.exit(1)

if __name__ == '__main__':
    main()

