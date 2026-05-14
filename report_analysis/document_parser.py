from pypdf import PdfReader
from spire.doc import *
import requests
from bs4 import BeautifulSoup
from odf import text, teletype
from odf.opendocument import load
from playwright.sync_api import sync_playwright

def format_as_python_literal(text, max_line_length=80):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 > max_line_length:
            lines.append(f'    "{current.strip()} "')
            current = ""
        current += word + " "

    if current:
        lines.append(f'    "{current.strip()} "')

    formatted = "(\n" + "\n".join(lines) + "\n)"
    return formatted


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

def parseODT(file_name):

    text_doc = load(file_name)
    
    paragraphs = text_doc.getElementsByType(text.P)
    
    file_text = "\n".join([teletype.extractText(p) for p in paragraphs])

    return file_text


def parseWebsite(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        text = page.inner_text("body")
        browser.close()
        return text
    
def parseFile(file_name):

    text = None
    
    if file_name.endswith('.pdf'):
    
        text = parsePDF(file_name)

    elif file_name.endswith('.odt'):
    
        text = parseODT(file_name)  
    
    elif file_name.endswith('.doc') or file_name.endswith('.docx'):
        
        text = parseDOC(file_name)

    elif file_name.startswith("http"):

        text = parseWebsite(file_name)
        
    return text