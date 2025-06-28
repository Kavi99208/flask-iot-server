import requests
import time
import pytz
from datetime import datetime, timedelta
from math import log10, pow
from supabase import create_client, Client

# ---------------- CONFIG ----------------
SUPABASE_URL = "https://idcrtezkbidtjfkyjvuq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkY3J0ZXprYmlkdGpma3lqdnVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTE0MjQsImV4cCI6MjA2NjI2NzQyNH0.LafFRZYj-bQyr5uhhJT6l4GF7CKkoygeHBGsaliJXNc"
THING_SPEAK_API_KEY = "YOUR_THINGSPEAK_API_KEY"
THING_SPEAK_CHANNEL_URL = "https://api.thingspeak.com/update"

# ---------------- INIT ----------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
IST = pytz.timezone('Asia/Kolkata')

# ---------------- HELPERS ----------------
def get_current_minute():
    now = datetime.now(IST)
    return now.replace(second=0, microsecond=0)

def fetch_data_from_supabase(start, end):
    query = (
        supabase.table("sound_data")
        .select("timestamp, db_value, device_id")
        .gte("timestamp", start.isoformat())
        .lt("timestamp", end.isoformat())
    )
    response = query.execute()
    return response.data

def group_and_log_addition(data):
    result = {1: [], 2: []}
    for row in data:
        dev = row['device_id']
        db = row['db_value']
        if db != -184.87:  # Skip invalid readings
            result[dev].append(db)

    def log_add(values):
        if not values:
            return None
        powers = [pow(10, v / 10) for v in values]
        avg_power = sum(powers) / len(powers)
        return round(10 * log10(avg_power), 2)

    return {dev: log_add(vals) for dev, vals in result.items()}

def send_to_thingspeak(device1_value, device2_value):
    params = {
        'api_key': THING_SPEAK_API_KEY,
        'field1': device1_value if device1_value is not None else '',
        'field2': device2_value if device2_value is not None else '',
    }
    response = requests.get(THING_SPEAK_CHANNEL_URL, params=params)
    if response.status_code == 200:
        print(f"✅ Sent to ThingSpeak: Device 1 = {device1_value}, Device 2 = {device2_value}")
    else:
        print(f"❌ Failed to send to ThingSpeak: {response.text}")

# ---------------- MAIN LOOP ----------------
print("🔁 Starting Real-Time Audio Analysis...")
while True:
    try:
        end_time = get_current_minute()
        start_time = end_time - timedelta(minutes=1)

        print(f"⏳ Fetching from {start_time} to {end_time}...")
        data = fetch_data_from_supabase(start_time, end_time)
        log_added = group_and_log_addition(data)

        print(f"📊 Log-Added Data: {log_added}")
        send_to_thingspeak(log_added.get(1), log_added.get(2))

    except Exception as e:
        print(f"⚠ Error: {e}")

    time.sleep(60)







