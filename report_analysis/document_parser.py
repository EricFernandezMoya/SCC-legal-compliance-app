from pypdf import PdfReader
from spire.doc import *
import requests
from bs4 import BeautifulSoup

_BLOCKED_PHRASES = [
    "access denied", "403 forbidden", "403 error", "robot", "captcha",
    "cloudflare", "just a moment", "enable javascript",
    "checking your browser", "please enable cookies", "ddos protection",
]


def _is_blocked(text):
    if len(text) <= 500:
        return True
    return any(phrase in text[:2000].lower() for phrase in _BLOCKED_PHRASES)


def parsePDF(file_name):
    
    text = ""

    reader = PdfReader(file_name)

    for page in reader.pages:
        pageText = page.extract_text() or ""
        text += pageText.strip() + " "
    
    return text.strip()

def parseDOC(file_name):

    document = Document()
    document.LoadFromFile(file_name)

    text = document.GetText()

    document.Close()

    return text

def parseWebsite(url):
    _HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Connection": "keep-alive",
    }

    # Stage 1 — fast path via requests
    text = ""
    try:
        response = requests.get(url, headers=_HEADERS, timeout=15)
        if response.status_code == 200:
            text = BeautifulSoup(response.text, "html.parser").get_text(separator="\n", strip=True)
    except Exception:
        pass

    if not _is_blocked(text):
        print(f"URL fetch: used requests for {url}")
        return text

    # Stage 2 — Playwright fallback
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-AU",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_selector("body", timeout=10000)
            html = page.content()
            browser.close()
        text = BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True)
    except Exception as exc:
        raise ValueError(f"Failed to fetch URL with both requests and Playwright: {url} — {exc}")

    if _is_blocked(text):
        raise ValueError(f"Page blocked or returned no usable content after browser render: {url}")

    print(f"URL fetch: used playwright for {url}")
    return text

def parseFile(file_name):

    text = None
    
    if file_name.endswith('.pdf'):
    
        text = parsePDF(file_name)

    elif file_name.endswith('.doc') or file_name.endswith('.docx'):
        
        text = parseDOC(file_name)

    elif file_name.startswith("http"):

        text = parseWebsite(file_name)
        
    return text