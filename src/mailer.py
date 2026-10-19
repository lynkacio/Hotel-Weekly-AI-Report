"""Gmail API sender, OAuth user credentials. Recipient is always test address."""
import base64, json, os
from email.message import EmailMessage

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def send_test_email(test_recipient: str, subject: str, body: str) -> str:
    if not test_recipient or '@' not in test_recipient or test_recipient.endswith('@example.com'):
        raise ValueError('Provide your real TEST_RECIPIENT email address')
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    raw = os.getenv('GMAIL_TOKEN_JSON', '').strip()
    if raw:
        creds = Credentials.from_authorized_user_info(json.loads(raw), scopes=SCOPES)
    else:
        with open(os.getenv('GMAIL_TOKEN_FILE', 'token.json'), encoding='utf-8') as f:
            creds = Credentials.from_authorized_user_info(json.load(f), scopes=SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError('Gmail OAuth token missing or expired; see README')
    message = EmailMessage()
    message['To'] = test_recipient
    message['Subject'] = subject
    message.set_content(body)
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode('ascii')
    gmail = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    response = gmail.users().messages().send(userId='me', body={'raw': encoded}).execute()
    return response['id']
