
import json
import time
import hashlib
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
DOCS = BASE / "documents"
PAGES = DOCS / "webpages"
PDFS = DOCS / "pdfs"
MANIFEST = DOCS / "manifest.json"

START_URL = "https://www.lbrce.ac.in/"
ALLOWED_HOSTS = {"www.lbrce.ac.in", "lbrce.ac.in"}
MAX_PAGES = 500
DELAY_SECONDS = 0.5

for folder in (PAGES, PDFS):
    folder.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers["User-Agent"] = (
    "LBRCECollegeInformationBot/1.0 "
    "(educational project; contact the college if requested)"
)

robots = RobotFileParser()
robots.set_url(urljoin(START_URL, "robots.txt"))

try:
    robots.read()
except Exception:
    print("Could not read robots.txt; verify site crawling rules manually.")
    raise SystemExit(1)


def allowed(url):
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in ALLOWED_HOSTS
        and robots.can_fetch(session.headers["User-Agent"], url)
    )


def stable_name(url, suffix):
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{digest}{suffix}"


queue = deque([START_URL])
visited = set()
records = []
pdf_seen = set()

while queue and len(visited) < MAX_PAGES:
    url = urldefrag(queue.popleft())[0]

    if url in visited or not allowed(url):
        continue

    parsed = urlparse(url)
    if parsed.path.lower().endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".zip", ".docx", ".xlsx")
    ):
        continue

    visited.add(url)

    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"FAILED page: {url} ({exc})")
        continue

    content_type = response.headers.get("Content-Type", "").lower()

    if "application/pdf" in content_type or url.lower().endswith(".pdf"):
        if url not in pdf_seen:
            try:
                filename = stable_name(url, ".pdf")
                path = PDFS / filename
                path.write_bytes(response.content)

                records.append({
                    "type": "pdf",
                    "path": str(path.relative_to(DOCS)),
                    "source_url": url,
                    "title": Path(urlparse(url).path).name,
                })
                pdf_seen.add(url)
                print(f"PDF: {url}")
            except OSError as exc:
                print(f"FAILED PDF save: {url} ({exc})")
        continue

    if "text/html" not in content_type:
        continue

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else url
    text = soup.get_text(" ", strip=True)

    if text:
        filename = stable_name(url, ".txt")
        (PAGES / filename).write_text(
            f"TITLE: {title}\nSOURCE: {url}\n\n{text}",
            encoding="utf-8",
        )

        records.append({
            "type": "html",
            "path": str(Path("webpages") / filename),
            "source_url": url,
            "title": title,
        })

    for link in soup.find_all("a", href=True):
        target = urldefrag(urljoin(url, link["href"]))[0]
        target_parsed = urlparse(target)

        if target_parsed.hostname not in ALLOWED_HOSTS:
            continue

        if target.lower().endswith(".pdf"):
            if target not in pdf_seen and allowed(target):
                try:
                    pdf_response = session.get(target, timeout=30)
                    pdf_response.raise_for_status()

                    if (
                        "application/pdf"
                        not in pdf_response.headers.get(
                            "Content-Type", ""
                        ).lower()
                        and not pdf_response.content.startswith(b"%PDF")
                    ):
                        continue

                    filename = stable_name(target, ".pdf")
                    path = PDFS / filename
                    path.write_bytes(pdf_response.content)

                    records.append({
                        "type": "pdf",
                        "path": str(Path("pdfs") / filename),
                        "source_url": target,
                        "title": Path(target_parsed.path).name,
                    })
                    pdf_seen.add(target)
                    print(f"PDF: {target}")
                except requests.RequestException as exc:
                    print(f"FAILED PDF: {target} ({exc})")
        elif target_parsed.path.lower().endswith(
            (".jpg", ".jpeg", ".png", ".zip", ".docx", ".xlsx")
        ):
            continue
        elif target not in visited:
            queue.append(target)

    print(f"Pages processed: {len(visited)}")
    time.sleep(DELAY_SECONDS)

MANIFEST.write_text(
    json.dumps(records, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("\nCrawl complete.")
print(f"HTML pages saved: {sum(r['type'] == 'html' for r in records)}")
print(f"PDFs saved: {sum(r['type'] == 'pdf' for r in records)}")
print(f"Manifest: {MANIFEST}")
