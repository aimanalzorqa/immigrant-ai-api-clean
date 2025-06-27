from flask import Flask, request, jsonify
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Constants
SPREADSHEET_ID = '1ydUyiGQ3hyW-IrJwOVSqCYq3bB-ph99qWBwshaI3xXw'
RANGE_NAME = 'Sheet1!A2:H1000'
SERVICE_ACCOUNT_FILE = 'E:/office_work/immigrant-ai-clean/immigrantassistantai-4bd5ca85b629.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Setup Google Sheets connection
creds = Credentials.from_service_account_file('E:/office_work/immigrant-ai-clean/immigrantassistantai-4bd5ca85b629.json', scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
values = result.get('values', [])

# Create DataFrame
columns = values[0]
data = values[1:]
df = pd.DataFrame(data, columns=columns)

# Flask app
app = Flask(__name__)

@app.route('/content', methods=['GET'])
def get_content():
    trigger_key = request.args.get('trigger_key')
    if not trigger_key:
        return jsonify({'error': 'Missing trigger_key'}), 400

    row = df[df['trigger_key'] == trigger_key]
    if row.empty:
        return jsonify({'error': 'No content found'}), 404

    content = {
        'service': row.iloc[0]['service'],
        'subcategory': row.iloc[0]['subcategory'],
        'content_type': row.iloc[0]['content_type'],
        'content': row.iloc[0]['content'],
        'resources': row.iloc[0]['resources']
    }
    return jsonify(content)

if __name__ == '__main__':
    app.run(debug=True)
