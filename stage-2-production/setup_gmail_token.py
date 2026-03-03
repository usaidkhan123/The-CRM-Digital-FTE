"""
Gmail OAuth Token Generator
Run this script to generate gmail_token.json from your gmail_credentials.json

Usage:
  pip install google-api-python-client google-auth-oauthlib
  python3 setup_gmail_token.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials/gmail_credentials.json",
    ["https://www.googleapis.com/auth/gmail.send"]
)

creds = flow.run_local_server(port=0)

with open("credentials/gmail_token.json", "w") as f:
    f.write(creds.to_json())

print("Token saved to credentials/gmail_token.json")
print("Gmail setup complete!")
