import os
import json
import win32com.client

path = os.path.abspath(r'deliverables\ha_noi\BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx')
word = None
try:
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False
    word.DisplayAlerts = False
    doc = word.Documents.Open(path)

    results = []
    total_paragraphs = doc.Paragraphs.Count
    print(f"Total paragraphs in document: {total_paragraphs}")

    # Inspect paragraphs starting after the TOC (approx paragraph 60 onwards)
    for i in range(60, total_paragraphs + 1):
        p = doc.Paragraphs(i)
        text = p.Range.Text.replace('\r', '').replace('\x07', '').strip()
        if not text:
            continue
        # Check if heading
        if text.startswith("PHẦN") or text.startswith("DANH MỤC") or text.startswith("PHỤ LỤC") or any(text.startswith(f"{k}.") for k in range(1, 10)):
            if len(text) < 100:
                page = p.Range.Information(1) # wdActiveEndPageNumber
                results.append((text, page))

    doc.Close(False)
    with open('scratch/exact_headings_v2.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

finally:
    if word:
        try:
            word.Quit()
        except Exception:
            pass

print("Done scanning headings.")
