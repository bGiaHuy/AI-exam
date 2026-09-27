import os
import pypdf

def check_pdf(pdf_path):
    print(f"\n==========================================")
    print(f"Inspecting PDF: {pdf_path}")
    print(f"==========================================")
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")
    
    empty_pages = []
    orphan_headings = []
    
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        text = page.extract_text() or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        # Check empty page
        if len(lines) == 0:
            empty_pages.append(page_num)
            print(f"Page {page_num}: [WARNING] Blank page detected!")
            continue
            
        first_line = lines[0] if lines else ""
        last_line = lines[-1] if lines else ""
        
        # Check orphan heading on last line
        if any(last_line.startswith(prefix) for prefix in ["PHẦN ", "DANH MỤC ", "PHỤ LỤC", "1. ", "2. ", "3. ", "4. ", "5. ", "6. "]):
            if len(last_line) < 80:
                orphan_headings.append((page_num, last_line))
                print(f"Page {page_num}: [POTENTIAL ORPHAN HEADING] Last line: '{last_line}'")
                
        # Sample preview
        print(f"Page {page_num:2d} ({len(lines):2d} lines): First: '{first_line[:40]}...' | Last: '{last_line[:40]}...'")

    print("\nSummary:")
    print(f"- Empty pages: {len(empty_pages)} {empty_pages}")
    print(f"- Potential orphan headings: {len(orphan_headings)} {orphan_headings}")

if __name__ == "__main__":
    check_pdf(r"deliverables\ha_noi\BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.pdf")
    check_pdf(r"deliverables\ha_noi\NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.pdf")
