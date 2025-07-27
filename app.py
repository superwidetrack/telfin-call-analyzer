import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>29ROZ Call Analyzer</h1>
    <p>Automated call analysis system is running.</p>
    <p>Status: Active</p>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "service": "29ROZ Call Analyzer"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
