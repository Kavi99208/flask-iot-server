from flask import Flask, request
import os

app = Flask(_name_)

# Directory to store incoming CSVs
UPLOAD_FOLDER = "received_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    filename = request.headers.get('X-Filename')
    if not filename:
        return "❌ Missing filename header", 400

    # Path to save file
    filepath = os.path.join(UPLOAD_FOLDER, os.path.basename(filename))

    # Save raw POST body
    with open(filepath, 'wb') as f:
        f.write(request.data)

    print(f"✅ Received and saved: {filename}")
    return "OK", 200

if _name_ == '_main_':
    # Listen on all interfaces (local network), port 5000
    app.run(host='0.0.0.0', port=5000)
