# Quick sanity check: confirms your Anthropic API key works.
#
# Before running this:
#   1. Copy .env.example to .env
#   2. Open .env and paste in your real Anthropic API key
#
# We'll add a similar check for Nebius later, in Step 3.

import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=50,
    messages=[{"role": "user", "content": "Say 'connection successful' and nothing else."}]
)

print(response.content[0].text)
