from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from transformers import pipeline  # For question answering
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env
openai.api_key = os.getenv("OPENAI_API_KEY") # Load api_key variables from .env

# Constants
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = 'Sheet1!A2:H1000'
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Setup Google Sheets connection
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
values = result.get('values', [])

# Create DataFrame
columns = values[0]
data = values[1:]
df = pd.DataFrame(data, columns=columns)

# Initialize Flask app
app = Flask(__name__)

# Load QA model
qa_pipeline = pipeline("question-answering")

@app.route('/')
def serve_ui():
    return send_from_directory('.', 'index.html')

@app.route('/categories', methods=['GET'])
def get_categories():
    categories = df['service'].unique().tolist()
    return jsonify(categories)

@app.route('/subcategories', methods=['GET'])
def get_subcategories():
    service = request.args.get('service')
    if not service:
        return jsonify({'error': 'Missing service'}), 400
    filtered = df[df['service'] == service]
    subkeys = filtered['trigger_key'].tolist()
    return jsonify(subkeys)

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

# New QA endpoint
@app.route('/qa', methods=['POST'])
def question_answering():
    data = request.get_json()
    question = data.get('question')
    context = data.get('context')

    if not question or not context:
        return jsonify({'error': 'Missing question or context'}), 400

    result = qa_pipeline(question=question, context=context)

    return jsonify({
        'answer': result['answer'],
        'score': result['score']
    })

# ChatGPT-4 endpoint
@app.route('/chatgpt', methods=['POST'])
def chat_with_gpt():
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Missing prompt'}), 400

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert immigration assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        reply = completion.choices[0].message.content.strip()
        return jsonify({'response': reply})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
