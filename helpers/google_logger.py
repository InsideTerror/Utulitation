import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables for the service account credentials
credentials_info = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),  # Handle newlines in the private key
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN")
}

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Initialize credentials
creds = service_account.Credentials.from_service_account_info(credentials_info)

# Initialize the Sheets and Docs API services
sheets_service = build('sheets', 'v4', credentials=creds)
docs_service = build('docs', 'v1', credentials=creds)

SPREADSHEET_ID = "1E53HBsjHk7rSxrgFdE1ErW-xRTIsHTjdN2gIDG2rd7w"
DOCUMENT_ID = "1CAwAhxEAclRkmmelN0mkhRjUe74_NhmbAQuKR4KMOEw"

class GoogleLogger:
    async def log_case_to_sheet(self, case_id, judge, parties, status, timestamp):
        body = {
            'values': [[case_id, judge, parties, status, timestamp]]
        }
        try:
            sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range="Sheet1!A:E",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
        except HttpError as e:
            print("Failed to log to sheet:", e)

    async def append_transcript(self, case_id, user, content, timestamp):
        try:
            doc = docs_service.documents().get(documentId=DOCUMENT_ID).execute()
            content_list = doc.get("body").get("content")
            index = self._find_or_create_case_heading(case_id, content_list)
            docs_service.documents().batchUpdate(
                documentId=DOCUMENT_ID,
                body={
                    'requests': [
                        {
                            'insertText': {
                                'location': {'index': index},
                                'text': f"[{timestamp}] {user}: {content}\n"
                            }
                        }
                    ]
                }
            ).execute()
        except HttpError as e:
            print("Failed to append transcript:", e)

    def _find_or_create_case_heading(self, case_id, content_list):
        for element in content_list:
            text = element.get("paragraph", {}).get("elements", [{}])[0].get("textRun", {}).get("content", "")
            if text.strip() == f"Case {case_id}":
                return element.get("startIndex") + len(text)

        # Heading not found; create new heading
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': f"Case {case_id}\n"
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': 1 + len(f"Case {case_id}\n")
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_1'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ]
        docs_service.documents().batchUpdate(documentId=DOCUMENT_ID, body={'requests': requests}).execute()
        return 1 + len(f"Case {case_id}\n")
