# BookGrepper
Bot to grep book information

## How to use
- Create google sheet API key
- Enter the API client_id and client_secret in credentials.json
- Replace the googleSheetId with the target sheet
- run python htmlparser.py

You may encounter "HTTPError: HTTP Error 408: Request Timeout". This is because books.com.tw will drop every 2 connection. A 10-second wait time is added as workaround  
