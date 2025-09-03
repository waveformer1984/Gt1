
from flask import Flask, request, render_template_string, jsonify
import json
from datetime import datetime
import os

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), '../database/ideas.json')

def udp_score(idea_text):
    score = len(idea_text) % 100  # Placeholder scoring logic
    return score

@app.route('/', methods=['GET'])
def index():
    return render_template_string(open('client/form.html').read())

@app.route('/submit', methods=['POST'])
def submit():
    idea = request.form.get('idea')
    contributor = request.form.get('contributor')
    score = udp_score(idea)
    record = {
        "idea": idea,
        "contributor": contributor,
        "score": score,
        "timestamp": datetime.now().isoformat()
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = []
    data.append(record)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return jsonify({"message": "Idea submitted", "score": score})

if __name__ == '__main__':
    app.run(debug=True)
