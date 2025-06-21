from flask import Flask, request
import numpy as np
import os

app = Flask(__name__)
UPLOAD_FOLDER = "chunks"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

chunk_data = []

@app.route('/stream_chunk', methods=['POST'])
def receive_chunk():
    global chunk_data
    chunk_id = int(request.headers.get("X-Chunk-Id", -1))
    if chunk_id == -1:
        return "❌ No chunk ID", 400

    data = np.frombuffer(request.data, dtype=np.int16)
    chunk_data.append((chunk_id, data))

    if len(chunk_data) == 5:
        # Sort and concatenate
        chunk_data.sort(key=lambda x: x[0])
        full_data = np.concatenate([chunk for _, chunk in chunk_data])
        chunk_data.clear()

        return run_analysis(full_data), 200

    return f"✅ Chunk {chunk_id} received", 200

def run_analysis(mic_data):
    import matplotlib.pyplot as plt

    dc_bias = np.mean(mic_data)
    normalized = (mic_data - dc_bias) / np.max(np.abs(mic_data - dc_bias))
    y = normalized
    sr = 22050

    center_freqs = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    ref_pressure = 20e-6
    N = len(y)

    fft_vals = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(N, d=1/sr)
    fft_spectrum = np.abs(fft_vals)
    power_spectrum = fft_spectrum**2 / N

    spls = []
    for fc in center_freqs:
        f_low = fc / np.sqrt(2)
        f_high = fc * np.sqrt(2)
        band_indices = np.where((freqs >= f_low) & (freqs <= f_high))[0]
        band_power = np.sum(power_spectrum[band_indices])
        rms = np.sqrt(band_power) if band_power > 0 else 1e-12
        spl = 20 * np.log10(rms * 0.165 / ref_pressure)
        spls.append(spl)

    # A-weighting
    a_weighting = [-39.4, -26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1, -1.1, -6.6]
    a_weighted_spl = [spl + corr for spl, corr in zip(spls, a_weighting)]

    total_spl = 10 * np.log10(np.sum(10**(np.array(spls) / 10)))
    total_a_spl = 10 * np.log10(np.sum(10**(np.array(a_weighted_spl) / 10)))

    print("SPLs per band (dB):", spls)
    print("A-weighted SPLs per band:", a_weighted_spl)
    print(f"Total SPL: {total_spl:.2f} dB")
    print(f"Total A-weighted SPL: {total_a_spl:.2f} dB(A)")

    return f"Total SPL: {total_spl:.2f} dB | A-weighted: {total_a_spl:.2f} dB(A)"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)













