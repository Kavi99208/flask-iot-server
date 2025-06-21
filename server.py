from flask import Flask, request
import os
from audio_analysis import process_and_send_to_thingspeak

app = Flask(__name__)

UPLOAD_FOLDER = "received_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    filename = request.headers.get("X-Filename")
    if not filename:
        return "❌ Missing filename", 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(request.data)
    print(f"✅ File received: {filename}")

    # Process and send to ThingSpeak
    db_value = process_and_send_to_thingspeak(filepath)
    if db_value is not None:
        print(f"📡 Uploaded to ThingSpeak: {db_value:.2f} dB(A)")
        return f"✅ Processed: {filename} | dB: {db_value:.2f}", 200
    else:
        return "❌ Processing failed", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
