from pathlib import Path
import fitz
from PIL import Image, ImageDraw

root = Path(__file__).parent
pdf_path = root / "AI_EXAM_CONTROL_GIAO_AN_CHUYEN_NGANH_5_BUOI.pdf"
pages_dir = root / "pages"
pages_dir.mkdir(exist_ok=True)
doc = fitz.open(pdf_path)
thumbs = []
for index, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.15, 1.15), alpha=False)
    path = pages_dir / f"page-{index + 1:03d}.png"
    pix.save(path)
    img = Image.open(path).convert("RGB")
    img.thumbnail((245, 346))
    tile = Image.new("RGB", (265, 380), "white")
    tile.paste(img, ((265 - img.width) // 2, 22))
    draw = ImageDraw.Draw(tile)
    draw.text((8, 5), f"Trang {index + 1}", fill="black")
    thumbs.append(tile)

per_sheet = 12
for start in range(0, len(thumbs), per_sheet):
    group = thumbs[start:start + per_sheet]
    sheet = Image.new("RGB", (265 * 4, 380 * 3), "#bdbdbd")
    for j, thumb in enumerate(group):
        sheet.paste(thumb, ((j % 4) * 265, (j // 4) * 380))
    sheet.save(root / f"contact-{start // per_sheet + 1:02d}.png")
print(f"pages={len(doc)} sheets={(len(thumbs) + per_sheet - 1) // per_sheet}")
