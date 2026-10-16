
import json
import re
from collections import Counter
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader

# ==================================================
# 1. PATHS AND SETTINGS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
OUTPUT_FILE = BASE_DIR / "college_docs.json"

POPPLER_PATH = (
    r"C:\Users\Anji\Downloads\Release-26.09.0-0"
    r"\poppler-26.09.0\Library\bin"
)

CHUNK_SIZE = 1800
CHUNK_OVERLAP = 250
OCR_DPI = 200

# ==================================================
# 2. SOURCE URLS
# ==================================================

STUDENT_LIST_URL = (
    "https://www.lbrce.ac.in/csm/csmstudentslist.php"
)

RESULTS_URL = (
    "https://www.lbrce.ac.in/examsection_pages/examresults.php"
)

NOTIFICATIONS_URL = (
    "https://www.lbrce.ac.in/examsection_pages/examnotific.php"
)

SOURCE_URLS = {
    "student_list_cse_aiml_2023_2025_batches.txt":
        STUDENT_LIST_URL,

    "btech_sem1_r17_supplementary_results_april_2026.pdf":
        RESULTS_URL,

    "results_btech_sem4_r17_supplementary_april_2026.pdf":
        RESULTS_URL,

    "results_btech_sem5_r17_supplementary_april_2026.pdf":
        RESULTS_URL,

    "results_btech_sem6_r17_supplementary_april_2026.pdf":
        RESULTS_URL,

    "notification_btech_sem5_sem7_r17_supplementary_examinations_2019_batch_2026.pdf":
        NOTIFICATIONS_URL,

    "notification_btech_sem7_r23_regular_examinations_2026.pdf":
        NOTIFICATIONS_URL,

    "notification_btech_sem7_r23_regular_minor_honors_examinations_2026.pdf":
        NOTIFICATIONS_URL,
}


def get_source_url(path):
    """Find the source URL for a file."""
    if path.name in SOURCE_URLS:
        return SOURCE_URLS[path.name]

    name = path.name.lower()

    if "student" in name or "studentslist" in name:
        return STUDENT_LIST_URL

    if "result" in name:
        return RESULTS_URL

    if "notification" in name or "examination" in name:
        return NOTIFICATIONS_URL

    return None


# ==================================================
# 3. DOCUMENT CATEGORIES
# ==================================================

def get_category(filename):
    name = filename.lower()

    if "student" in name or "studentslist" in name:
        return "student_information"

    if "result" in name:
        return "results"

    if "exam" in name or "notification" in name:
        return "examinations"

    if "admission" in name:
        return "admissions"

    if "placement" in name:
        return "placements"

    if "event" in name or "lakshya" in name:
        return "events"

    return "general"


# ==================================================
# 4. TEXT CLEANING AND CHUNKING
# ==================================================

def clean_text(text):
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


# ==================================================
# 5. OCR FOR A SINGLE PDF PAGE
# ==================================================

def ocr_pdf_page(pdf_path, page_number):
    """Convert one scanned PDF page to an image and OCR it."""
    images = convert_from_path(
        str(pdf_path),
        first_page=page_number,
        last_page=page_number,
        dpi=OCR_DPI,
        poppler_path=POPPLER_PATH,
        fmt="png",
        thread_count=1,
    )

    if not images:
        return ""

    try:
        text = pytesseract.image_to_string(
            images[0],
            lang="eng",
            config="--psm 6",
        )
        return clean_text(text)
    finally:
        for image in images:
            image.close()


# ==================================================
# 6. EXTRACT TEXT FROM TXT AND PDF
# ==================================================

def extract_file(path):
    """
    Return (page_number, text) pairs.
    OCR is used when a PDF page has no selectable text.
    """

    extension = path.suffix.lower()

    if extension == ".txt":
        text = path.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )
        text = clean_text(text)

        return [(None, text)] if text else []

    if extension != ".pdf":
        return []

    reader = PdfReader(str(path))

    if reader.is_encrypted:
        try:
            result = reader.decrypt("")
            if result == 0:
                raise ValueError("PDF is password-protected.")
        except Exception as exc:
            raise ValueError(
                "Cannot read encrypted PDF."
            ) from exc

    extracted_pages = []

    for page_number, page in enumerate(
        reader.pages, start=1
    ):
        text = clean_text(page.extract_text() or "")

        if len(text) < 30:
            print(
                f"    Page {page_number}: little/no text; "
                "trying OCR..."
            )

            try:
                ocr_text = ocr_pdf_page(path, page_number)

                if len(ocr_text) > len(text):
                    text = ocr_text

            except Exception as exc:
                print(
                    f"    OCR failed on page {page_number}: "
                    f"{type(exc).__name__}: {exc}"
                )

        if text:
            extracted_pages.append((page_number, text))
        else:
            print(
                f"    WARNING: No text extracted "
                f"from page {page_number}."
            )

    return extracted_pages


# ==================================================
# 7. BUILD THE KNOWLEDGE BASE
# ==================================================

def main():
    if not DOCUMENTS_DIR.exists():
        print(f"ERROR: Folder not found: {DOCUMENTS_DIR}")
        return

    files = sorted(
        path
        for path in DOCUMENTS_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".txt", ".pdf"}
    )

    print(f"Documents folder: {DOCUMENTS_DIR}")
    print(f"Files found: {len(files)}")
    print("-" * 60)

    documents = []
    skipped_files = []
    failed_files = []
    empty_files = []

    for path in files:
        print(f"\nReading: {path.name}")

        source_url = get_source_url(path)

        if not source_url or not source_url.startswith("https://"):
            print("  SKIPPED: No valid HTTPS source URL.")
            skipped_files.append(path.name)
            continue

        try:
            pages = extract_file(path)
        except Exception as exc:
            print(
                f"  ERROR: {type(exc).__name__}: {exc}"
            )
            failed_files.append(path.name)
            continue

        file_chunks = 0

        for page_number, page_text in pages:
            for chunk_number, chunk in enumerate(
                split_text(page_text), start=1
            ):
                documents.append({
                    "title": path.stem.replace("_", " ").title(),
                    "category": get_category(path.name),
                    "source_url": source_url,
                    "page": page_number,
                    "chunk": chunk_number,
                    "text": chunk,
                })

                file_chunks += 1

        print(f"  Pages with text: {len(pages)}")
        print(f"  Chunks created: {file_chunks}")

        if file_chunks == 0:
            empty_files.append(path.name)

    # Save in the JSON list format required by main.py.
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    print(f"Files discovered: {len(files)}")
    print(f"Total chunks indexed: {len(documents)}")
    print(f"Skipped files: {len(skipped_files)}")
    print(f"Failed files: {len(failed_files)}")
    print(f"Files with no text: {len(empty_files)}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nChunks by document:")
    for title, count in Counter(
        doc["title"] for doc in documents
    ).items():
        print(f"  {title}: {count}")

    if skipped_files:
        print("\nSkipped files:")
        for name in skipped_files:
            print(f"  - {name}")

    if failed_files:
        print("\nFailed files:")
        for name in failed_files:
            print(f"  - {name}")

    if empty_files:
        print("\nFiles requiring further checks:")
        for name in empty_files:
            print(f"  - {name}")

    print("\nIngestion finished.")


if __name__ == "__main__":
    main()
