from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI
import voyageai
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
        model="claude-sonnet-4-6",
    )

    return message.content[0].text
    
