import os
import base64
import io
import numpy as np
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from PIL import Image
from quantum_engine import QuantumBridgeEngine
from qiskit import transpile
from qiskit_aer import Aer
from qiskit.quantum_info import partial_trace

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quantum_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 16x16 grid config (24 total qubits - STABLE)
GRID_SIZE = 16
NUM_QUBITS = 8
engine = QuantumBridgeEngine(NUM_QUBITS)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('teleport_request')
def handle_teleport(data):
    print("Received request...")
    try:
        # Decode image from base64
        image_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes)).convert('L')
        img = img.resize((GRID_SIZE, GRID_SIZE))
        pixels = np.array(img).flatten().astype(float)
        
        print(f"Encoding {GRID_SIZE}x{GRID_SIZE} image")
        amplitudes, scaling_factor = engine.encode_image_qpie(pixels)
        
        print("Generating circuit")
        qc = engine.get_teleportation_circuit(amplitudes)
        simulator = Aer.get_backend('statevector_simulator')
        t_qc = transpile(qc, simulator)
        
        print("Running simulation...")
        result = simulator.run(t_qc).result()
        
        print("Extracting states")
        final_state = result.get_statevector()
        counts = result.get_counts()
        key_string = list(counts.keys())[0]
        
        other_qubits = list(range(0, 2 * NUM_QUBITS))
        receiver_state = partial_trace(final_state, other_qubits).to_statevector()
        
        payload = {
            "key": key_string,
            "scaling_factor": float(scaling_factor),
            "scrambled_state": [[float(x.real), float(x.imag)] for x in receiver_state.data.tolist()], 
            "original_size": GRID_SIZE
        }
        
        print(f"Broadcasting. Key: {key_string}")
        socketio.emit('quantum_state_received', payload)
        print("Done.")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
