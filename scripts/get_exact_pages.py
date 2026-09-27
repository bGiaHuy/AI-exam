import os
import json
import win32com.client

path = os.path.abspath(r'deliverables\ha_noi\BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx')
word = win32com.client.Dispatch('Word.Application')
word.Visible = False
word.DisplayAlerts = False
doc = word.Documents.Open(path)

results = {}
total_paragraphs = doc.Paragraphs.Count
print(f"Total paragraphs in document: {total_paragraphs}")

# The first 55 paragraphs contain Cover and TOC.
# Let's inspect paragraphs from index 56 onwards:
for i in range(50, total_paragraphs + 1):
    p = doc.Paragraphs(i)
    text = p.Range.Text.strip()
    if text and (text.startswith("PHẦN") or text.startswith("DANH MỤC") or any(text.startswith(f"{k}.") for k in range(1, 10))):
        page = p.Range.Information(1) # wdActiveEndPageNumber
        # Clean text
        clean_text = text.replace('\r', '').replace('\x07', '').strip()
        if len(clean_text) < 80:
            results[clean_text] = page

doc.Close(False)
word.Quit()

with open('scratch/exact_heading_pages.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Recorded {len(results)} exact heading pages.")
