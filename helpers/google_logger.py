import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets'
]

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
SPREADSHEET_ID = "1E53HBsjHk7rSxrgFdE1ErW-xRTIsHTjdN2gIDG2rd7w"
DOCUMENT_ID = "1CAwAhxEAclRkmmelN0mkhRjUe74_NhmbAQuKR4KMOEw"

class GoogleLogger:
    def __init__(self):
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        self.sheets_service = build('sheets', 'v4', credentials=creds)
        self.docs_service = build('docs', 'v1', credentials=creds)

    async def log_case_creation(self, case_id, judge, parties, status, timestamp):
        body = {
            'values': [[case_id, judge, parties, status, timestamp]]
        }
        try:
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range="Sheet1!A:E",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
        except HttpError as e:
            print("Failed to log case creation to sheet:", e)

    async def append_transcript(self, case_id, user, content, timestamp):
        try:
            doc = self.docs_service.documents().get(documentId=DOCUMENT_ID).execute()
            content_list = doc.get("body").get("content")
            index = self._find_or_create_case_heading(case_id, content_list)
            self.docs_service.documents().batchUpdate(
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
        self.docs_service.documents().batchUpdate(documentId=DOCUMENT_ID, body={'requests': requests}).execute()
        return 1 + len(f"Case {case_id}\n")
