"""Document text extraction and export tools (DOCX, PDF, TXT, MD, HTML).

Zero external dependencies - stdlib Python only.
"""

import io
import re
import xml.etree.ElementTree as ET
import zipfile
import zlib
from typing import Any


def extract_text(data: bytes, filename: str) -> str:
    """Extract clean plain text from any uploaded file format (DOCX, PDF, ODT, EPUB, RTF, HTML, TXT, MD, JSON, CSV)."""
    fn = filename.lower()
    
    # 1. Word Document (.docx), PowerPoint (.pptx), or OpenDocument (.odt)
    if fn.endswith((".docx", ".pptx", ".odt")) or data.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                # Word (.docx)
                if "word/document.xml" in z.namelist():
                    tree = ET.fromstring(z.read("word/document.xml"))
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    paragraphs: list[str] = []
                    for p in tree.iter(f"{{{ns['w']}}}p"):
                        texts = [node.text for node in p.iter(f"{{{ns['w']}}}t") if node.text]
                        if texts:
                            paragraphs.append("".join(texts))
                    if paragraphs:
                        return "\n\n".join(paragraphs)
                
                # PowerPoint Presentation (.pptx)
                slide_keys = [k for k in z.namelist() if k.startswith("ppt/slides/slide") and k.endswith(".xml")]
                if slide_keys:
                    slide_keys.sort(key=lambda x: int(re.search(r"slide(\d+)\.xml", x).group(1)) if re.search(r"slide(\d+)\.xml", x) else 0)
                    slide_texts: list[str] = []
                    for sk in slide_keys:
                        tree = ET.fromstring(z.read(sk))
                        texts = [elem.text for elem in tree.iter() if elem.text and elem.text.strip()]
                        if texts:
                            slide_texts.append(" ".join(texts))
                    if slide_texts:
                        return "\n\n".join(slide_texts)

                # OpenDocument (.odt)
                if "content.xml" in z.namelist():
                    tree = ET.fromstring(z.read("content.xml"))
                    texts = [elem.text for elem in tree.iter() if elem.text and elem.text.strip()]
                    if texts:
                        return "\n\n".join(texts)
        except Exception:
            pass

    # Legacy PowerPoint (.ppt) binary
    if fn.endswith(".ppt"):
        try:
            text_runs = re.findall(rb"[\x20-\x7E\t\r\n]{4,}", data)
            if text_runs:
                clean = [t.decode("latin1", errors="ignore").strip() for t in text_runs if not t.startswith(b"Microsoft") and not t.startswith(b"PowerPoint Document") and len(t.strip()) > 3]
                if clean:
                    return "\n\n".join(clean)
        except Exception:
            pass

    # 2. PDF Document (.pdf)
    if fn.endswith(".pdf") or data.startswith(b"%PDF-"):
        try:
            text_parts: list[str] = []
            # Extract and decompress flatedecompressed streams
            stream_matches = re.findall(rb"stream[\r\n]+([\s\S]*?)[\r\n]+endstream", data)
            for s in stream_matches:
                decompressed = s
                try:
                    decompressed = zlib.decompress(s)
                except Exception:
                    pass
                
                # Tj operators
                for tm in re.findall(rb"\((.*?)\)\s*Tj", decompressed):
                    try:
                        decoded = tm.decode("utf-8", errors="ignore").strip()
                        if decoded:
                            text_parts.append(decoded)
                    except Exception:
                        pass
                
                # TJ array operators
                for tarr in re.findall(rb"\[(.*?)\]\s*TJ", decompressed):
                    for part in re.findall(rb"\((.*?)\)", tarr):
                        try:
                            decoded = part.decode("utf-8", errors="ignore").strip()
                            if decoded:
                                text_parts.append(decoded)
                        except Exception:
                            pass

            if text_parts:
                combined = " ".join(text_parts)
                # Clean up PDF spacing
                combined = re.sub(r"\s+", " ", combined)
                return combined.strip()
            
            # Fallback: regex search across entire raw data for Tj/TJ
            raw_matches = re.findall(rb"\((.*?)\)\s*Tj", data)
            if raw_matches:
                res = [m.decode("latin1", errors="ignore") for m in raw_matches if len(m) > 1]
                if res:
                    return " ".join(res)
        except Exception:
            pass

    # 3. Rich Text Format (.rtf)
    if fn.endswith(".rtf") or data.startswith(b"{\\rtf"):
        try:
            raw_str = data.decode("latin1", errors="ignore")
            # Strip RTF control words
            clean_rtf = re.sub(r"\\[a-zA-Z0-9]+(\s|-[0-9]+)?", " ", raw_str)
            clean_rtf = re.sub(r"[{}]", " ", clean_rtf)
            return re.sub(r"\s+", " ", clean_rtf).strip()
        except Exception:
            pass

    # 4. HTML (.html, .htm)
    if fn.endswith((".html", ".htm")):
        try:
            raw = data.decode("utf-8", errors="replace")
            raw = re.sub(r"<(script|style).*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<[^>]+>", " ", raw)
            return re.sub(r"\s+", " ", raw).strip()
        except Exception:
            pass

    # 5. Plain Text, Markdown, JSON, CSV
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return data.decode("latin1", errors="replace")


def create_docx(content: str) -> bytes:
    """Create a valid Microsoft Word (.docx) document preserving styles, alignments, colors, headings, and tables."""
    out = io.BytesIO()
    body_xml_parts: list[str] = []
    
    # Helper to parse hex color
    def extract_color(style_str: str) -> str:
        m = re.search(r"color\s*:\s*#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", style_str)
        if m:
            hex_c = m.group(1)
            if len(hex_c) == 3:
                hex_c = "".join([c*2 for c in hex_c])
            return hex_c.upper()
        if "red" in style_str: return "DC2626"
        if "blue" in style_str: return "1E40AF"
        if "green" in style_str: return "16A34A"
        if "purple" in style_str: return "9333EA"
        return ""

    page_cards = re.findall(r'<div[^>]*class="[^"]*doc-page-card[^"]*"[^>]*>([\s\S]*?)</div>(?=\s*<div[^>]*class="[^"]*doc-page-card|\s*$)', content, flags=re.IGNORECASE)
    if not page_cards:
        page_cards = [content]

    for p_idx, page_content in enumerate(page_cards):
        page_content = re.sub(r'<div[^>]*class="[^"]*doc-page-header-bar[^"]*"[\s\S]*?</div>', '', page_content, flags=re.IGNORECASE)
        if p_idx > 0 and body_xml_parts:
            body_xml_parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

        if "<" in page_content and ">" in page_content and any(tag in page_content for tag in ("<p", "<h1", "<h2", "<h3", "<b", "<strong", "<i", "<em", "<u", "<li", "<div", "<table", "<blockquote")):
            parts = re.split(r"(<table[\s\S]*?</table>)", page_content, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if part.lower().startswith("<table"):
                    tbl_xml = ['<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/></w:tblBorders></w:tblPr>']
                    rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", part, flags=re.IGNORECASE)
                    for r_idx, row in enumerate(rows):
                        tbl_xml.append('<w:tr>')
                        cells = re.findall(r"<(?:td|th)[^>]*>([\s\S]*?)</(?:td|th)>", row, flags=re.IGNORECASE)
                        for cell in cells:
                            is_th = "<th" in row.lower() or r_idx == 0
                            shd = '<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="1E40AF"/></w:tcPr>' if is_th else ''
                            clean_c = re.sub(r"<[^>]+>", " ", cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            rPr = '<w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr>' if is_th else ''
                            tbl_xml.append(f'<w:tc>{shd}<w:p><w:r>{rPr}<w:t xml:space="preserve">{clean_c.strip()}</w:t></w:r></w:p></w:tc>')
                        tbl_xml.append('</w:tr>')
                    tbl_xml.append('</w:tbl>')
                    body_xml_parts.append("".join(tbl_xml))
                    continue

                blocks = re.split(r"(<(?:h1|h2|h3|p|li|blockquote|div)[^>]*>[\s\S]*?</(?:h1|h2|h3|p|li|blockquote|div)>)", part, flags=re.IGNORECASE)
                for block in blocks:
                    block = block.strip()
                    if not block or "doc-page-badge" in block:
                        continue
                    
                    tag_match = re.match(r"^<([a-zA-Z0-9]+)([^>]*)>", block)
                    tag = tag_match.group(1).lower() if tag_match else "p"
                    attr = tag_match.group(2) if tag_match else ""
                    
                    pPr_items = []
                    if "center" in attr:
                        pPr_items.append('<w:jc w:val="center"/>')
                    elif "right" in attr:
                        pPr_items.append('<w:jc w:val="right"/>')
                    elif "justify" in attr:
                        pPr_items.append('<w:jc w:val="both"/>')
                    
                    if tag == "h1":
                        pPr_items.append('<w:pStyle w:val="Heading1"/><w:spacing w:before="240" w:after="120"/>')
                    elif tag == "h2":
                        pPr_items.append('<w:pStyle w:val="Heading2"/><w:spacing w:before="200" w:after="100"/>')
                    elif tag == "h3":
                        pPr_items.append('<w:pStyle w:val="Heading3"/><w:spacing w:before="160" w:after="80"/>')
                    elif tag == "li":
                        pPr_items.append('<w:pStyle w:val="ListParagraph"/>')
                    elif tag == "blockquote":
                        pPr_items.append('<w:pBdr><w:left w:val="single" w:sz="18" w:space="15" w:color="1E40AF"/></w:pBdr>')
                    
                    pPr = f"<w:pPr>{''.join(pPr_items)}</w:pPr>" if pPr_items else ""
                    inner = re.sub(r"^<[^>]+>", "", block)
                    inner = re.sub(r"</[^>]+>$", "", inner)
                    
                    runs: list[str] = []
                    tokens = re.split(r"(<[^>]+>)", inner)
                    is_bold = False
                    is_italic = False
                    is_underline = False
                    current_color = "1E40AF" if tag == "h2" else ""
                    
                    for token in tokens:
                        if not token:
                            continue
                        low = token.lower()
                        if low.startswith("<span") or low.startswith("<font"):
                            c = extract_color(token)
                            if c: current_color = c
                        elif low in ("</span>", "</font>"):
                            current_color = "1E40AF" if tag == "h2" else ""
                        elif low in ("<b>", "<strong>"):
                            is_bold = True
                        elif low in ("</b>", "</strong>"):
                            is_bold = False
                        elif low in ("<i>", "<em>"):
                            is_italic = True
                        elif low in ("</i>", "</em>"):
                            is_italic = False
                        elif low == "<u>":
                            is_underline = True
                        elif low == "</u>":
                            is_underline = False
                        elif low in ("<br>", "<br/>", "<br />"):
                            runs.append("<w:r><w:br/></w:r>")
                        elif not token.startswith("<"):
                            clean_text = token.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                            rPr_parts = []
                            if is_bold or tag in ("h1", "h2", "h3"):
                                rPr_parts.append("<w:b/>")
                            if is_italic:
                                rPr_parts.append("<w:i/>")
                            if is_underline:
                                rPr_parts.append('<w:u w:val="single"/>')
                            if current_color:
                                rPr_parts.append(f'<w:color w:val="{current_color}"/>')
                            if tag == "h1":
                                rPr_parts.append('<w:sz w:val="32"/><w:szCs w:val="32"/>')
                            elif tag == "h2":
                                rPr_parts.append('<w:sz w:val="26"/><w:szCs w:val="26"/>')
                            elif tag == "h3":
                                rPr_parts.append('<w:sz w:val="22"/><w:szCs w:val="22"/>')
                            
                            rPr = f"<w:rPr>{''.join(rPr_parts)}</w:rPr>" if rPr_parts else ""
                            runs.append(f'<w:r>{rPr}<w:t xml:space="preserve">{clean_text}</w:t></w:r>')
                    
                    body_xml_parts.append(f"<w:p>{pPr}{''.join(runs)}</w:p>")
        else:
            paragraphs = page_content.split("\n")
            for p in paragraphs:
                p_strip = p.strip()
                pPr = ""
                if p_strip.startswith("### "):
                    p_text = p_strip[4:]
                    pPr = '<w:pPr><w:pStyle w:val="Heading3"/></w:pPr>'
                    rPr = '<w:rPr><w:b/><w:sz w:val="22"/></w:rPr>'
                elif p_strip.startswith("## "):
                    p_text = p_strip[3:]
                    pPr = '<w:pPr><w:pStyle w:val="Heading2"/></w:pPr>'
                    rPr = '<w:rPr><w:b/><w:color w:val="1E40AF"/><w:sz w:val="26"/></w:rPr>'
                elif p_strip.startswith("# "):
                    p_text = p_strip[2:]
                    pPr = '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
                    rPr = '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr>'
                else:
                    p_text = p
                    rPr = ""
                
                clean_text = p_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                body_xml_parts.append(f'<w:p>{pPr}<w:r>{rPr}<w:t xml:space="preserve">{clean_text}</w:t></w:r></w:p>')
    
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        '<w:body>\n'
        + "".join(body_xml_parts) +
        '<w:sectPr/>\n'
        '</w:body>\n'
        '</w:document>'
    )
    
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '<Default Extension="xml" ContentType="application/xml"/>\n'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
        '</Types>'
    )
    
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
        '</Relationships>'
    )
    
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml)
        z.writestr("_rels/.rels", rels_xml)
        z.writestr("word/document.xml", document_xml)
    
    return out.getvalue()


def create_pdf(content: str, title: str = "Document") -> bytes:
    """Generate a clean, valid multi-page PDF document preserving paragraphs, headings, colors, alignments, and lists."""
    
    def parse_pdf_color(style_str: str) -> str:
        m = re.search(r"color\s*:\s*#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", style_str)
        if m:
            hex_c = m.group(1)
            if len(hex_c) == 3:
                hex_c = "".join([c*2 for c in hex_c])
            r = int(hex_c[0:2], 16) / 255.0
            g = int(hex_c[2:4], 16) / 255.0
            b = int(hex_c[4:6], 16) / 255.0
            return f"{r:.2f} {g:.2f} {b:.2f} rg"
        if "red" in style_str: return "0.86 0.15 0.15 rg"
        if "blue" in style_str: return "0.12 0.25 0.68 rg"
        if "green" in style_str: return "0.09 0.64 0.29 rg"
        if "purple" in style_str: return "0.58 0.20 0.92 rg"
        return ""

    def sanitize_pdf_text(txt: str) -> str:
        rep = {
            "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
            "\u2014": " - ", "\u2013": " - ", "\u2026": "...", "\u2022": "*",
            "\u00a0": " ", "\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": ""
        }
        for k, v in rep.items():
            txt = txt.replace(k, v)
        clean = []
        for ch in txt:
            code = ord(ch)
            if code < 128:
                if ch in ("\\", "(", ")"):
                    clean.append("\\" + ch)
                else:
                    clean.append(ch)
            elif 160 <= code <= 255:
                clean.append(ch)
            else:
                clean.append(" ")
        return "".join(clean)

    def wrap_line(txt: str, max_chars: int) -> list[str]:
        words = txt.split()
        if not words:
            return [""]
        lines = []
        cur: list[str] = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + (1 if cur else 0) <= max_chars:
                cur.append(w)
                cur_len += len(w) + (1 if len(cur) > 1 else 0)
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
        if cur:
            lines.append(" ".join(cur))
        return lines

    page_w, page_h = 595.28, 841.89
    margin_x, margin_top, margin_bottom = 50.0, 48.0, 48.0
    usable_w = page_w - (margin_x * 2)
    pages_stream: list[str] = []
    current_page_commands: list[str] = []
    y = page_h - margin_top

    def new_page():
        nonlocal current_page_commands, y
        if current_page_commands:
            pages_stream.append("\n".join(current_page_commands))
        current_page_commands = []
        y = page_h - margin_top

    page_cards = re.findall(r'<div[^>]*class="[^"]*doc-page-card[^"]*"[^>]*>([\s\S]*?)</div>(?=\s*<div[^>]*class="[^"]*doc-page-card|\s*$)', content, flags=re.IGNORECASE)
    if not page_cards:
        page_cards = [content]

    for p_idx, page_content in enumerate(page_cards):
        page_content = re.sub(r'<div[^>]*class="[^"]*doc-page-header-bar[^"]*"[\s\S]*?</div>', '', page_content, flags=re.IGNORECASE)
        is_rtl_page = 'dir="rtl"' in page_content.lower() or "direction: rtl" in page_content.lower()
        if p_idx > 0 and (current_page_commands or pages_stream):
            new_page()

        blocks: list[dict[str, Any]] = []
        if "<" in page_content and ">" in page_content and any(t in page_content for t in ("<p", "<h1", "<h2", "<h3", "<li", "<div", "<blockquote", "<table")):
            raw_blocks = re.split(r"(<(?:h1|h2|h3|p|li|blockquote|div|tr)[^>]*>[\s\S]*?</(?:h1|h2|h3|p|li|blockquote|div|tr)>)", page_content, flags=re.IGNORECASE)
            for b in raw_blocks:
                b = b.strip()
                if not b or "doc-page-badge" in b or "doc-page-header-bar" in b:
                    continue
                m = re.match(r"^<([a-zA-Z0-9]+)([^>]*)>", b)
                tag = m.group(1).lower() if m else "p"
                attr = m.group(2) if m else ""
                
                align = "right" if is_rtl_page else "left"
                if "center" in attr: align = "center"
                elif "right" in attr: align = "right"
                elif "left" in attr: align = "left"
                
                color = parse_pdf_color(attr)
                
                inner = re.sub(r"<[^>]+>", " ", b)
                inner = re.sub(r"\s+", " ", inner).strip()
                if inner:
                    blocks.append({"tag": tag, "text": inner, "align": align, "color": color})
        else:
            for p in page_content.split("\n"):
                p_str = p.strip()
                if not p_str:
                    blocks.append({"tag": "empty", "text": "", "align": "left", "color": ""})
                elif p_str.startswith("### "):
                    blocks.append({"tag": "h3", "text": p_str[4:], "align": "left", "color": ""})
                elif p_str.startswith("## "):
                    blocks.append({"tag": "h2", "text": p_str[3:], "align": "left", "color": ""})
                elif p_str.startswith("# "):
                    blocks.append({"tag": "h1", "text": p_str[2:], "align": "left", "color": ""})
                elif p_str.startswith("- ") or p_str.startswith("* "):
                    blocks.append({"tag": "li", "text": p_str[2:], "align": "left", "color": ""})
                else:
                    blocks.append({"tag": "p", "text": p_str, "align": "left", "color": ""})

        for item in blocks:
            tag = item["tag"]
            text = item["text"]
            align = item["align"]
            custom_color = item["color"]

            if tag == "empty":
                y -= 8
                if y < margin_bottom:
                    new_page()
                continue

            if tag == "h1":
                font, size, line_height, space_before, space_after, max_c, default_color = "/F2", 13.5, 17, 8, 4, 65, "0.08 0.10 0.15 rg"
            elif tag == "h2":
                font, size, line_height, space_before, space_after, max_c, default_color = "/F2", 11.5, 15, 8, 3, 75, "0.12 0.25 0.68 rg" # Dark Blue
            elif tag == "h3":
                font, size, line_height, space_before, space_after, max_c, default_color = "/F2", 10.5, 14, 6, 2, 80, "0.15 0.18 0.25 rg"
            elif tag == "li":
                font, size, line_height, space_before, space_after, max_c, default_color, text = "/F1", 9.5, 13.5, 2, 2, 88, "0.10 0.10 0.12 rg", "• " + text
            elif tag == "blockquote":
                font, size, line_height, space_before, space_after, max_c, default_color = "/F3", 9.5, 13.5, 4, 4, 85, "0.25 0.30 0.40 rg"
            else:
                font, size, line_height, space_before, space_after, max_c, default_color = "/F1", 9.5, 13.5, 2, 4, 90, "0.10 0.10 0.12 rg"

            color_cmd = custom_color if custom_color else default_color
            y -= space_before
            wrapped = wrap_line(text, max_c)

            for line in wrapped:
                if y < margin_bottom + line_height:
                    new_page()
                clean_str = sanitize_pdf_text(line)
                
                approx_line_w = len(line) * (size * 0.52)
                if align == "center":
                    x_pos = margin_x + max(0, (usable_w - approx_line_w) / 2)
                elif align == "right":
                    x_pos = margin_x + max(0, usable_w - approx_line_w)
                else:
                    x_pos = margin_x

                current_page_commands.append(f"BT {color_cmd} {font} {size} Tf {x_pos:.2f} {y:.2f} Td ({clean_str}) Tj ET")
                y -= line_height

            y -= space_after

    if current_page_commands or not pages_stream:
        pages_stream.append("\n".join(current_page_commands))

    num_pages = len(pages_stream)
    objects: list[str] = ["<< /Type /Catalog /Pages 2 0 R >>"]
    kids_refs = " ".join([f"{4 + i * 2} 0 R" for i in range(num_pages)])
    objects.append(f"<< /Type /Pages /Kids [ {kids_refs} ] /Count {num_pages} >>")
    objects.append("<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >> /F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >> /F3 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >> >> >>")
    
    for i, p_stream in enumerate(pages_stream):
        page_obj_num = 4 + i * 2
        content_obj_num = page_obj_num + 1
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [ 0 0 {page_w:.2f} {page_h:.2f} ] /Resources 3 0 R /Contents {content_obj_num} 0 R >>")
        stream_bytes = p_stream.encode("latin1", errors="replace")
        objects.append(f"<< /Length {len(stream_bytes)} >>\nstream\n{p_stream}\nendstream")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for idx, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{idx} 0 obj\n{obj}\nendobj\n".encode("latin1", errors="replace"))
    
    xref_offset = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin1"))
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode("latin1"))
    
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))
    return out.getvalue()



def merge_files(files: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge up to 10 files into a combined text, DOCX and PDF document."""
    extracted_sections: list[str] = []
    file_summaries: list[dict[str, Any]] = []

    for idx, item in enumerate(files[:10], 1):
        name = item.get("name", f"Document_{idx}")
        raw_b64 = item.get("file", "")
        import base64
        try:
            data = base64.b64decode(raw_b64)
            text = extract_text(data, name)
            if not text.strip():
                text = f"[Empty or Binary Content: {name}]"
        except Exception as e:
            text = f"[Error reading {name}: {e}]"

        file_summaries.append({
            "name": name,
            "char_count": len(text),
            "word_count": len(text.split()),
        })

        header = f"=== File {idx}: {name} ==="
        extracted_sections.append(f"{header}\n\n{text.strip()}")

    merged_text = "\n\n" + ("\n\n" + "=" * 50 + "\n\n").join(extracted_sections) + "\n"
    docx_bytes = create_docx(merged_text)
    pdf_bytes = create_pdf(merged_text)
    import base64
    return {
        "ok": True,
        "text": merged_text,
        "docx_base64": base64.b64encode(docx_bytes).decode("ascii"),
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
        "files_count": len(file_summaries),
        "files": file_summaries,
    }

