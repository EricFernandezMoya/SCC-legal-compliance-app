from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI
import os

###############################################################################
# This is a function that take a Query to the AI by text and returns the      #
# answer in text format                                                       #
#                                                                             #
###############################################################################

def textQueryToAntropic(textQuery):
    
# to access to the Anthropic session it is required a key that is saved in a .env file
# load_dotenv() access to the .env file to obtein the key    
    
    load_dotenv()

    client = Anthropic()

    message = client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": textQuery,
            }
        ],
        model="claude-sonnet-4-20250514",
    )

    return message.content[0].text

def queryVoyage(textquery):
    load_dotenv()
    
    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        raise ValueError("VOYAGE_API_KEY not found in .env file")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.aimlapi.com",
    )
    print(client.models.list())

    try:
        response = client.embeddings.create(
            input=textquery,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    except Exception as e:
        print("Error querying Voyage:", e)
        return None
