from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from nlp_functions import analyze_customer_note
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'SmartNote NLP'}

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        note_text = data.get('note', '')
        
        if not note_text:
            return jsonify({'error': 'No note text provided'}), 400
        
        result = analyze_customer_note(note_text)
        
        return jsonify({'success': True, 'analysis': result}), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

# For production (Render.com uses this)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)