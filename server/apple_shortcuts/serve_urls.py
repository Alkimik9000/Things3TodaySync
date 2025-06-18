#!/usr/bin/env python3
"""Flask server to serve unprocessed Things3 URLs to iOS/iPadOS devices.

This server reads from processed_tasks.csv and serves URLs where Processed='No'.
After serving, it updates the Processed column to 'Yes'.
"""

from __future__ import annotations

from flask import Flask, jsonify, request
import pandas as pd
from pathlib import Path
import os
from typing import List, Dict

app = Flask(__name__)

# Configuration
BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR.parent / "outputs" / "processed_tasks.csv"
API_KEY = os.environ.get('THINGS_API_KEY', 'default-api-key')  # Set via environment variable

def authenticate_request() -> bool:
    """Check if the request has a valid API key."""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        return token == API_KEY
    return False


@app.route('/new_urls', methods=['GET'])
def get_new_urls() -> tuple:
    """Return unprocessed URLs and mark them as processed."""
    # Simple authentication
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not CSV_FILE.exists():
        return jsonify({'error': 'CSV file not found'}), 404
    
    try:
        # Read the CSV
        df = pd.read_csv(CSV_FILE)
        
        # Check if required columns exist
        if 'GenUrl' not in df.columns or 'Processed' not in df.columns:
            return jsonify({'error': 'Required columns missing in CSV'}), 500
        
        # Filter for unprocessed URLs
        unprocessed = df[df['Processed'] == 'No']
        
        # Get the URLs
        urls = []
        indices_to_update = []
        
        for idx, row in unprocessed.iterrows():
            if pd.notna(row['GenUrl']) and row['GenUrl'] != '':
                urls.append({
                    'task_number': str(row.get('TaskNumber', '')),
                    'title': str(row.get('TaskTitle', '')),
                    'url': str(row['GenUrl'])
                })
                indices_to_update.append(idx)
        
        # Update the Processed column for served URLs
        if indices_to_update:
            df.loc[indices_to_update, 'Processed'] = 'Yes'
            df.to_csv(CSV_FILE, index=False)
            print(f"Served {len(urls)} URLs and marked as processed")
        
        return jsonify({
            'urls': urls,
            'count': len(urls)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def get_status() -> tuple:
    """Return server status and task statistics."""
    if not CSV_FILE.exists():
        return jsonify({'status': 'error', 'message': 'CSV file not found'}), 404
    
    try:
        df = pd.read_csv(CSV_FILE)
        
        # Calculate statistics
        total_tasks = len(df)
        with_urls = len(df[df['GenUrl'].notna() & (df['GenUrl'] != '')])
        processed = len(df[df['Processed'] == 'Yes']) if 'Processed' in df.columns else 0
        unprocessed = len(df[df['Processed'] == 'No']) if 'Processed' in df.columns else 0
        
        return jsonify({
            'status': 'ok',
            'statistics': {
                'total_tasks': total_tasks,
                'tasks_with_urls': with_urls,
                'processed': processed,
                'unprocessed': unprocessed
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/', methods=['GET'])
def index() -> str:
    """Simple index page."""
    return '''
    <h1>Things3 URL Server</h1>
    <p>Endpoints:</p>
    <ul>
        <li>GET /new_urls - Get unprocessed URLs (requires Authorization header)</li>
        <li>GET /status - Get server status and statistics</li>
    </ul>
    '''


if __name__ == '__main__':
    # Run the server
    port = int(os.environ.get('FLASK_PORT', 5000))
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    
    print(f"Starting Things3 URL server on {host}:{port}")
    print(f"API Key: {API_KEY}")
    print("Set THINGS_API_KEY environment variable to change the API key")
    
    app.run(host=host, port=port, debug=False) 