import os
import uuid
from fpdf import FPDF

def sanitize_text(text: str) -> str:
    """Replaces or encodes unsupported UTF-8 characters for standard FPDF core fonts."""
    if not text:
        return ""
    # Smart quotes and common unicode replacements
    replacements = {
        '“': '"', '”': '"', '‘': "'", '’': "'", '—': '-', '–': '-',
        '…': '...', 'é': 'e', 'è': 'e', 'á': 'a', 'à': 'a'
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Encode to latin-1 replacing unrepresentable chars
    return text.encode('latin-1', 'replace').decode('latin-1')


def save_pdf(comic_layout: list) -> str:
    """
    Uses FPDF to compile the comic layout into a multi-page PDF.
    Each panel's title, image, scene description, narration, and dialogue are placed on a page.
    Saves to static/exports/ and returns relative path '/static/exports/<filename>.pdf'.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "static", "exports")
    os.makedirs(output_dir, exist_ok=True)

    unique_id = uuid.uuid4().hex[:8]
    filename = f"comic_{unique_id}.pdf"
    filepath = os.path.join(output_dir, filename)
    relative_path = f"/static/exports/{filename}"

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)

    for panel in comic_layout:
        pdf.add_page()
        
        # Header / Title
        pdf.set_font("Helvetica", style="B", size=18)
        pdf.set_text_color(30, 30, 80)
        panel_title = f"Panel {panel.get('panel_number', '')}: {panel.get('title', '')}"
        pdf.cell(0, 10, sanitize_text(panel_title), ln=True, align="C")
        pdf.ln(5)

        # Image placement
        img_rel_path = panel.get("image_path", "").lstrip("/")
        img_full_path = os.path.join(base_dir, img_rel_path) if img_rel_path else ""

        if img_full_path and os.path.exists(img_full_path):
            # Center 120mm image
            pdf.image(img_full_path, x=45, w=120)
            pdf.ln(5)
        else:
            # Placeholder box if image file isn't on disk
            pdf.set_font("Helvetica", style="I", size=10)
            pdf.cell(0, 10, "[Image File Not Available]", ln=True, align="C")
            pdf.ln(5)

        # Scene Description (Italics)
        scene_desc = panel.get("scene_description", "")
        if scene_desc:
            pdf.set_font("Helvetica", style="I", size=10)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 6, sanitize_text(f"Scene: {scene_desc}"), align="L")
            pdf.ln(3)

        # Narration Box
        narration = panel.get("narration", "")
        if narration:
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.set_fill_color(240, 240, 250)
            pdf.set_draw_color(180, 180, 220)
            pdf.set_text_color(20, 20, 40)
            pdf.multi_cell(0, 7, sanitize_text(f"NARRATION: {narration}"), border=1, fill=True, align="L")
            pdf.ln(3)

        # Dialogue
        dialogue = panel.get("dialogue", "")
        if dialogue:
            pdf.set_font("Helvetica", style="", size=11)
            pdf.set_fill_color(255, 250, 235)
            pdf.set_draw_color(220, 180, 120)
            pdf.set_text_color(50, 30, 10)
            pdf.multi_cell(0, 7, sanitize_text(f"DIALOGUE:\n{dialogue}"), border=1, fill=True, align="L")
            pdf.ln(3)

    pdf.output(filepath)
    print(f"[SUCCESS] PDF successfully created at {filepath}")
    return relative_path
