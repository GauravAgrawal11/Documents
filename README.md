# 🛡️ Watermarks Remover & Multi-Page Document Studio

An enterprise-grade document engineering platform, lossless multi-page editor, file merger, and multi-vendor AI provenance removal suite.

---

## 🌟 Key Capabilities & Studios

### 1. ✍️ Lossless Multi-Page Document Editor
- **Multi-Format Ingestion**: Open PDF, Microsoft Word (`.docx`), PowerPoint (`.pptx`, `.ppt`), OpenDocument (`.odt`), EPUB, HTML, Markdown, and plain text.
- **True A4 & 16:9 Visual Canvas**: Renders documents into distinct, isolated page sheets matching source dimensions ($W \times H$) and styling.
- **Canva-Style Editing Tools**:
  - 🎨 **Text Color & Highlight Markers**: Unlimited RGB/Hex color picker + visual highlighter.
  - 🔤 **Curated Typefaces**: Inter, Outfit, Playfair Display, Merriweather, Roboto, JetBrains Mono, and Caveat with step-wise size adjustments.
  - 📐 **Spacing & Bidirectional Text**: Left/Center/Right/Justify, Line Height presets (1.15 to 2.0), and **`⇄ RTL / LTR`** (Right-to-Left text direction).
  - ➕ **Canva Insert Tools**: Interactive tables, embedded images, callout alert blocks, hyperlinks, and page dividers.
- **Page Management**:
  - `➕ Add Page`: Insert blank page sheets anywhere.
  - `📄 Duplicate`: Clone existing pages with full layout intact.
  - `🗑️ Delete`: Delete pages with dynamic badge renumbering.
  - `⚡ Jump to Page`: 1-click navigation across 10, 40, or 100+ page documents.
- **Multi-Format Vector Export**: Export to vector PDF, Word (`.docx`), Markdown, or download the untouched original file.

---

### 2. 📑 Universal Document Merger
- Combine heterogeneous files (e.g. Word `.docx` + PDF + Markdown + Plain Text) into a single unified publication.
- Drag-and-drop reordering, custom document headers, and 1-click export to PDF, DOCX, or consolidated Markdown.

---

### 3. 🛡️ AI Detector & Provenance Sanitizer
- **Linguistic & Stylometric Analysis**:
  - **Burstiness (CV)**: Sentence length standard deviation & rhythm variance.
  - **Shannon Bigram Entropy**: Information density and token predictability.
  - **Lexical Diversity (Guiraud's Index)**: Type-token richness normalized for length.
  - **AI Marker Detection**: Identification of 40+ transitional LLM signature clichés.
  - **Zero-Width Watermark Scanning**: Deterministic detection of hidden zero-width spaces, joiners, and bidi marks.
- **Layer B Paraphrase & Grammar Engine**: Local rule-based grammatical correction + optional LLM humanizer (Groq / OpenAI / Anthropic / Ollama).

---

## 📂 Supported Formats Matrix

| Category | Supported Extensions |
| :--- | :--- |
| **Documents** | `.pdf`, `.docx`, `.odt`, `.rtf`, `.epub`, `.html`, `.htm`, `.txt`, `.md`, `.json`, `.csv` |
| **Presentations** | `.pptx`, `.ppt` |
| **Spreadsheets** | `.xlsx` |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.webp`, `.avif`, `.heic`, `.bmp`, `.gif`, `.tiff`, `.svg` |
| **Audio / Video** | `.mp4`, `.mov`, `.m4a`, `.m4v`, `.wav`, `.mp3`, `.flac` |

---

## 🚀 Quickstart

### 1. Run with 1-Click (Windows)
Double-click `start-server.bat` or run:
```cmd
start-server.bat
```

### 2. Run via Python CLI (macOS / Linux / Windows)
```bash
# Clone the repository
git clone https://github.com/guillaumemeyer/watermarks-remover.git
cd watermarks-remover

# Install optional packages
pip install -r requirements.txt

# Start the server (Python 3.10+ stdlib)
python service/scripts/server.py --host 127.0.0.1 --port 8765
```

Open your browser at: **`http://localhost:8765`**

---

## 🌐 API Reference

| Endpoint | Method | Payload | Description |
| :--- | :--- | :--- | :--- |
| **`/analyze`** | `POST` | `{"text": "..."}` | Runs statistical AI probability & watermark inspection. |
| **`/inspect`** | `POST` | `{"file": "<b64>", "name": "..."}` or `{"text": "..."}` | Scans for hidden zero-width marks, C2PA, EXIF, and provenance. |
| **`/clean`** | `POST` | `{"file": "<b64>", "name": "..."}` or `{"text": "..."}` | Strips zero-width marks, metadata, and provenance tags. |
| **`/export/pdf`** | `POST` | `{"text": "<html>", "name": "doc.pdf"}` | Generates a multi-page vector PDF binary. |
| **`/export/docx`** | `POST` | `{"text": "<html>", "name": "doc.docx"}` | Generates a Microsoft Word `.docx` binary with page breaks. |
| **`/extract`** | `POST` | `{"file": "<b64>", "name": "file.pdf"}` | Extracts raw text from documents or presentation files. |
| **`/merge`** | `POST` | `{"files": [...], "exportFormat": "pdf"}` | Merges multiple files and compiles output. |
| **`/rewrite`** | `POST` | `{"text": "...", "strength": "grammar"}` | Runs grammar analysis and AI humanization. |

---

## 🧪 Automated Testing

Run the full integration test suite against the live server:
```bash
python service/scripts/test_full_suite.py
```

---

## 🚢 Deployment Strategies

Refer to [`DEPLOYMENT.md`](DEPLOYMENT.md) for detailed instructions on deploying with:
- **Docker Compose**
- **Cloud Platforms** (Render, Railway, Fly.io)
- **Nginx Reverse Proxy & Systemd** on Linux VPS.

---

## 📜 License
Distributed under the MIT License.
