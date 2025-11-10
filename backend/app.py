import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# CORS configuration for Railway
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
CORS(app, origins=[allowed_origins] if allowed_origins != '*' else '*')

# Health check endpoint (required for Railway)
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/api/test')
def test():
    return jsonify({'message': 'Backend is working!', 'status': 'success'})

# Example protected route
@app.route('/api/data')
def get_data():
    return jsonify({
        'data': 'Your data here',
        'timestamp': '2025-01-10'
    })

if __name__ == '__main__':
    # This is only for local development
    # Railway will use gunicorn command instead
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
