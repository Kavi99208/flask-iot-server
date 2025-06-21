import numpy as np
import os
import datetime
import requests
import sys

THINGSPEAK_API_KEY = "4W4MHWIL7SLL2RXG"
THINGSPEAK_URL = "https://api.thingspeak.com/update"

def extract_time_from_filename(filename):
    name = os.path.basename(filename).replace(".csv", "")
    dt = datetime.datetime.strptime(name, "%y%m%d_%H%M%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def process_and_send_to_thingspeak(filepath):
    try:
        data = np.loadtxt(filepath, skiprows=1)
        dc_bias = np.mean(data)
        normalized = (data - dc_bias) / np.max(np.abs(data - dc_bias))
        pcm_data = np.int16(normalized * 32767)

        y = normalized
        sr = 22050  # Match with Arduino sample rate

        center_freqs = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        a_weighting = [-39.4, -26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1, -1.1, -6.6]
        ref_pressure = 20e-6

        N = len(y)
        fft_vals = np.fft.rfft(y)
        freqs = np.fft.rfftfreq(N, d=1/sr)
        power_spectrum = np.abs(fft_vals)*2 / N*2

        spls = []
        for fc in center_freqs:
            f_low = fc / np.sqrt(2)
            f_high = fc * np.sqrt(2)
            band_indices = np.where((freqs >= f_low) & (freqs <= f_high))[0]
            band_power = np.sum(power_spectrum[band_indices])
            rms = np.sqrt(band_power) if band_power > 0 else 1e-12
            spl = 20 * np.log10(rms * 0.165 / ref_pressure)
            spls.append(spl)

        a_weighted_spl = [s + a for s, a in zip(spls, a_weighting)]
        total_spl_a = 10 * np.log10(np.sum(10 ** (np.array(a_weighted_spl) / 10)))

        timestamp = extract_time_from_filename(filepath)
        payload = {
            "api_key": THINGSPEAK_API_KEY,
            "field1": f"{total_spl_a:.2f}",
            "field2": timestamp
        }

        r = requests.post(THINGSPEAK_URL, data=payload)
        if r.status_code == 200:
            print(f"📡 Uploaded to ThingSpeak: {total_spl_a:.2f} dB(A) | Time: {timestamp}")
        else:
            print(f"❌ ThingSpeak upload failed: {r.status_code}")

        return total_spl_a

    except Exception as e:
        print(f"❌ Error processing file {filepath}:", e)
        return None






