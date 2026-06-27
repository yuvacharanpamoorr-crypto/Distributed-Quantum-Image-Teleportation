import socket
import json
import numpy as np
from qiskit.quantum_info import Statevector, partial_trace
from qiskit_aer import Aer
from PIL import Image
import os
from config import HOST, PORT, NUM_QUBITS, GRID_SIZE
from quantum_engine import QuantumBridgeEngine

def run_sender():
    engine = QuantumBridgeEngine(NUM_QUBITS)
    
    image_path = "input_image.png"
    if os.path.exists(image_path):
        print(f"Loading: {image_path}")
        img = Image.open(image_path).convert('L')
        img = img.resize((GRID_SIZE, GRID_SIZE))
        image = np.array(img).flatten().astype(float)
    else:
        print("input_image.png not found. Using default gradient.")
        x = np.linspace(0, 255, GRID_SIZE)
        y = np.linspace(0, 255, GRID_SIZE)
        xv, yv = np.meshgrid(x, y)
        image = ((xv + yv) / 2).flatten()
    
    print(f"Image {GRID_SIZE}x{GRID_SIZE} loaded.")
    
    amplitudes, scaling_factor = engine.encode_image_qpie(image)
    
    qc = engine.get_teleportation_circuit(amplitudes)
    
    from qiskit import transpile
    simulator = Aer.get_backend('statevector_simulator')
    t_qc = transpile(qc, simulator)
    result = simulator.run(t_qc).result()
    
    final_state = result.get_statevector()
    counts = result.get_counts()
    key_string = list(counts.keys())[0]
    
    print(f"Key: {key_string}")
    
    other_qubits = list(range(0, 2 * NUM_QUBITS))
    receiver_state = partial_trace(final_state, other_qubits).to_statevector()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}...")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            
            payload = {
                "key": key_string,
                "scaling_factor": float(scaling_factor),
                "scrambled_state": receiver_state.data.tolist()
            }
            
            conn.sendall(json.dumps(payload, default=lambda x: str(x)).encode())
            print("Packet sent.")

if __name__ == "__main__":
    run_sender()
