"""Convierte un archivo Markdown a PDF usando python-markdown y xhtml2pdf."""
import sys
import markdown
from xhtml2pdf import pisa

def convert(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    css = """
    @page { margin: 2cm 2.2cm; }
    body { font-family: Arial, sans-serif; font-size: 10pt; color: #222; line-height: 1.5; }
    h1 { font-size: 18pt; color: #1a3a5c; border-bottom: 2px solid #1a3a5c; padding-bottom: 6px; margin-top: 0; }
    h2 { font-size: 13pt; color: #1a3a5c; border-bottom: 1px solid #b0c4de; padding-bottom: 3px; margin-top: 18px; }
    h3 { font-size: 11pt; color: #2c5282; margin-top: 14px; }
    h4 { font-size: 10pt; color: #2c5282; margin-top: 10px; }
    table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt; }
    th { background-color: #1a3a5c; color: #fff; padding: 5px 8px; text-align: left; }
    td { border: 1px solid #ccc; padding: 4px 8px; }
    tr:nth-child(even) { background-color: #f2f6fc; }
    code { background: #f4f4f4; padding: 1px 4px; font-family: Courier New, monospace; font-size: 9pt; }
    pre { background: #f4f4f4; padding: 8px; border-left: 3px solid #1a3a5c; font-size: 8.5pt; }
    ul, ol { margin: 6px 0 6px 18px; }
    li { margin-bottom: 2px; }
    p { margin: 6px 0; }
    strong { color: #1a3a5c; }
    hr { border: none; border-top: 1px solid #ccc; margin: 16px 0; }
    """

    html = (
        "<!DOCTYPE html><html><head>"
        '<meta charset="utf-8">'
        "<style>" + css + "</style>"
        "</head><body>"
        + body
        + "</body></html>"
    )

    with open(pdf_path, "wb") as out_f:
        result = pisa.CreatePDF(html.encode("utf-8"), dest=out_f, encoding="utf-8")

    if result.err:
        print(f"ERROR al generar PDF: {result.err}")
        sys.exit(1)
    else:
        print(f"PDF generado: {pdf_path}")


if __name__ == "__main__":
    base = r"c:\Users\John\Downloads\securevault_pro_full\docs"
    convert(
        base + r"\10_Analisis_Cambios_v0.1_v1.0.md",
        base + r"\10_Analisis_Cambios_v0.1_v1.0.pdf",
    )
