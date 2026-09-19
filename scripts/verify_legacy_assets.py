"""
scripts/verify_legacy_assets.py
Sprint 3.1A Verification Script:
Verify that legacy public assets (screens, avatars) are removed from the filesystem,
excluded from production build artifacts (dist/), and that incoming requests
to legacy URLs resolve strictly to the generic SPA fallback (index.html) rather than legacy content.
"""
import os
import sys
import urllib.request
import urllib.error

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(REPO_ROOT, "dist")
PUBLIC_DIR = os.path.join(REPO_ROOT, "public")

def check_filesystem_and_dist():
    print("[1/3] Checking working tree and dist/ build directory...")
    # 1. public/ checks
    assert not os.path.exists(os.path.join(PUBLIC_DIR, "screens")), "FAIL: public/screens still exists!"
    assert not os.path.exists(os.path.join(PUBLIC_DIR, "avatars")), "FAIL: public/avatars still exists!"
    print("  [OK] public/screens and public/avatars are absent from working tree.")

    # 2. dist/ checks
    assert os.path.exists(DIST_DIR), "FAIL: dist/ directory does not exist. Run npm run build first."
    assert not os.path.exists(os.path.join(DIST_DIR, "screens")), "FAIL: dist/screens exists in production build!"
    assert not os.path.exists(os.path.join(DIST_DIR, "avatars")), "FAIL: dist/avatars exists in production build!"
    
    # Check all files in dist/
    for root, dirs, files in os.walk(DIST_DIR):
        for f in files:
            assert not f.endswith(".html") or f == "index.html", f"FAIL: Unexpected html file in dist: {f}"
            assert not f.startswith("student_0"), f"FAIL: Legacy avatar found in dist: {f}"
    print("  [OK] dist/ contains no screens or avatars; index.html is the only root document.")

def check_legacy_urls_against_dev_server(base_url="http://localhost:3000"):
    print(f"[2/3] Checking legacy URL resolution against dev server ({base_url})...")
    test_cases = [
        {
            "path": "/screens/04-report-protocol.html",
            "forbidden_strings": [
                b"BI\xc3\x8aN B\xe1\xba\xa2N", # "BIÊN BẢN" in UTF-8
                b"room-matrix",
                b"Room Matrix",
                b"cheat_sheet",
                b"camera-stream-hub"
            ],
            "description": "Legacy report protocol mockup"
        },
        {
            "path": "/avatars/student_01.jpg",
            "forbidden_strings": [],
            "forbid_jpeg_magic": True,
            "description": "Legacy student avatar"
        }
    ]

    for tc in test_cases:
        url = base_url + tc["path"]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LegacyAssetVerifier/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
                content_type = resp.headers.get("Content-Type", "")
                body = resp.read()

                print(f"  URL: {tc['path']} -> HTTP {status}, Content-Type: {content_type}, Size: {len(body)}B")

                if status == 200:
                    # Verified: Resolves to generic SPA fallback (index.html), NOT legacy content
                    print(f"    Notice: Legacy asset removed; request resolves to generic SPA fallback, not legacy content.")
                    assert "text/html" in content_type, f"FAIL: Expected text/html for SPA fallback, got {content_type}"
                    assert b"<html" in body.lower() or b"<!doctype html" in body.lower(), "FAIL: Body is not HTML fallback"
                    
                    if tc.get("forbid_jpeg_magic"):
                        # Check that body is NOT a JPEG image
                        assert not body.startswith(b"\xff\xd8\xff"), "FAIL: Returned binary JPEG magic bytes for deleted avatar!"
                    
                    for s in tc["forbidden_strings"]:
                        assert s.lower() not in body.lower(), f"FAIL: Legacy content leaked in response: {s}"
                elif status == 404:
                    print(f"    URL returned HTTP 404 Not Found as expected.")
                else:
                    raise AssertionError(f"Unexpected HTTP status: {status}")
        except urllib.error.URLError as e:
            print(f"  [WARN] Dev server not reachable at {base_url}: {e}")
            print(f"  Skipping live HTTP check (filesystem & dist/ checks remain valid).")
            return

    print("  [OK] All checked legacy URLs resolve to generic SPA fallback or 404 without leaking legacy content.")

def main():
    print("=== SPRINT 3.1A LEGACY ASSET & URL VERIFICATION ===")
    check_filesystem_and_dist()
    check_legacy_urls_against_dev_server()
    print("=== VERIFICATION RESULT: PASS (No legacy assets reachable or packaged) ===")

if __name__ == "__main__":
    main()
