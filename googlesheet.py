from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class GoogleSheet:
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id=spreadsheet_id
        self.creds = None
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.service = self.__build_service()

    def __build_service(self):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        service = build('sheets', 'v4', credentials=self.creds)
        return service

    def writeSheet(self, range_name:str, values):
        """ Example : 
        values = [
                [
                    'a','b','c',"x\\ny1", '"x\\ny2"', '"xy3"', 'x\\ny4'
                ],
                # Additional rows ...
            ]
        writeSheet('C4', values)
        """
        body = {
            'values': values
        }

        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id, range=range_name,
            valueInputOption='RAW', body=body).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))

    def readSheet(self, range_name: str):
        result = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        rows = result.get('values', [])
        return rows



# readSheet('D:D')