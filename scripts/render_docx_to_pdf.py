import os
import subprocess
import win32com.client

deliverables_dir = os.path.abspath(r"deliverables\ha_noi")
docx_files = [
    os.path.join(deliverables_dir, "BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx"),
    os.path.join(deliverables_dir, "NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx")
]

for docx_path in docx_files:
    if not os.path.exists(docx_path):
        print(f"File not found: {docx_path}")
        continue
    
    # Kill any dangling Word/preview processes before each doc
    subprocess.run(["powershell", "-Command", "Stop-Process -Name 'prevhost', 'wps', 'WINWORD' -Force -ErrorAction SilentlyContinue"], capture_output=True)
    
    word = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False
        
        pdf_path = docx_path.replace(".docx", ".pdf")
        print(f"\nOpening in Word: {docx_path}")
        doc = word.Documents.Open(docx_path)
        
        for s in doc.Sections:
            try:
                s.Headers(1).Range.Fields.Update()
                s.Footers(1).Range.Fields.Update()
            except Exception:
                pass
        try:
            doc.Fields.Update()
        except Exception:
            pass
        
        page_count = doc.ComputeStatistics(2) # 2 = wdStatisticPages
        print(f"Computed page count: {page_count} pages")
        
        print(f"Exporting to PDF: {pdf_path}")
        doc.SaveAs(pdf_path, FileFormat=17)
        doc.Close(False)
        print(f"Successfully generated PDF: {pdf_path} (File size: {os.path.getsize(pdf_path)} bytes)")
    except Exception as e:
        print(f"Error processing {docx_path}: {e}")
    finally:
        if word:
            try:
                word.Quit()
            except Exception:
                pass

print("\nRender verification complete.")
