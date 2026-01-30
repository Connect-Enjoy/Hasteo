import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pwa-demo-key')

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# PWA Routes
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static/js', 'service-worker.js')

# Main Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scanner():
    return render_template('scan.html')

# Vercel requirement
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)