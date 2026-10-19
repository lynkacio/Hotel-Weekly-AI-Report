"""Run locally once to authorize the Gmail account you want to SEND FROM."""
import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
load_dotenv()
flow = InstalledAppFlow.from_client_secrets_file(
    os.getenv('GMAIL_CLIENT_SECRET_FILE', 'client_secret.json'),
    ['https://www.googleapis.com/auth/gmail.send'])
creds = flow.run_local_server(port=0)
path = os.getenv('GMAIL_TOKEN_FILE', 'token.json')
with open(path, 'w', encoding='utf-8') as f:
    f.write(creds.to_json())
print(f'Token saved to {path}; keep it private. The authorized Gmail account is the sender.')
