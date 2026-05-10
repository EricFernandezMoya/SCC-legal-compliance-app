from pypdf import PdfReader
from spire.doc import *
import requests
from bs4 import BeautifulSoup
from odf import text, teletype
from odf.opendocument import load
from utils import clear_terminal


def parsePDF(file_name):
    
    text = ""

    reader = PdfReader(file_name)

    for page in reader.pages:
        text = text + page.extract_text()
    
    return text

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

    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    return soup.get_text()

def testing():

    not_finished = True

    while not_finished:

        file_name = input("Write file name or website url: ")

        if file_name.endswith('.pdf'):
    
            print(parsePDF(file_name))

        elif file_name.endswith('.odt'):
    
            print(parseODT(file_name))    
    
        elif file_name.endswith('.doc') or file_name.endswith('.docx'):
        
            print(parseDOC(file_name))

        elif file_name.startswith("http"):
    
            print(parseWebsite(file_name))

        else:

            print("file format not suported")

        option = input("\nWhat would you like to do?\npress 1 and enter if you want to read other document or press any key and/or enter to quit: ")

        if(option == "1"):

            clear_terminal()
        
        else:

            not_finished = False



    
testing()