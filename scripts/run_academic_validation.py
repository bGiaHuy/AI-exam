import subprocess
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

cmd1 = [sys.executable, '-X', 'utf8', 'tools/vietnamese-docs-style/scripts/validate_docx.py', 'deliverables/ha_noi/BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx', '--profile', 'academic']
cmd2 = [sys.executable, '-X', 'utf8', 'tools/vietnamese-docs-style/scripts/validate_docx.py', 'deliverables/ha_noi/NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx', '--profile', 'academic']

p1 = subprocess.run(cmd1, capture_output=True, text=True, encoding='utf-8')
p2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8')

report = []
report.append('================================================================================')
report.append('VIETNAMESE-DOCS-STYLE STRUCTURAL VALIDATION REPORT')
report.append('Skill Repository: https://github.com/bGiaHuy/vietnamese-docs-style')
report.append('Commit Hash: d5e47b7')
report.append('Selected Profile: academic')
report.append('================================================================================\n')

report.append('--- 1. BAO_CAO_KHKT_GIAM_SAT_PHONG_THI_HA_NOI_FINAL.docx ---')
report.append('Command: ' + ' '.join(cmd1))
report.append(f'Exit Code: {p1.returncode}')
report.append('STDOUT:')
report.append(p1.stdout.strip())
if p1.stderr.strip():
    report.append('STDERR:')
    report.append(p1.stderr.strip())
report.append('')

report.append('--- 2. NHAT_KY_XAY_DUNG_SAN_PHAM_GIAM_SAT_PHONG_THI_FINAL.docx ---')
report.append('Command: ' + ' '.join(cmd2))
report.append(f'Exit Code: {p2.returncode}')
report.append('STDOUT:')
report.append(p2.stdout.strip())
if p2.stderr.strip():
    report.append('STDERR:')
    report.append(p2.stderr.strip())
report.append('')

report.append('================================================================================')
report.append('OVERALL VALIDATION SUMMARY:')
if p1.returncode == 0 and p2.returncode == 0:
    report.append('ALL DOCUMENTS PASSED STRUCTURAL VALIDATION WITH 0 ERRORS.')
else:
    report.append('VALIDATION FAILED WITH ERRORS.')
report.append('================================================================================')

content = '\n'.join(report)
with open('deliverables/ha_noi/validation_report_academic.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print(content)
