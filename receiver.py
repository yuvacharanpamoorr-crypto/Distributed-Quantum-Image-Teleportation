import socket
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import matplotlib.pyplot as plt
from config import HOST, PORT, GRID_SIZE, NUM_QUBITS
from quantum_engine import QuantumBridgeEngine

def run_receiver():
    num_qubits = NUM_QUBITS
    engine = QuantumBridgeEngine(num_qubits)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Connecting to {HOST}:{PORT}...")
        s.connect((HOST, PORT))
        
        received_data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            received_data += chunk
        
        data = json.loads(received_data.decode())
        
        key = data["key"]
        scaling_factor = data["scaling_factor"]
        scrambled_raw = [complex(x.replace('(', '').replace(')', '')) for x in data["scrambled_state"]]
        scrambled_sv = Statevector(np.array(scrambled_raw))
        
        print(f"Key: {key}")
        
        # State before correction
        pre_correction = engine.decode_image(scrambled_sv.data, scaling_factor)
        
        # Apply corrections
        correction_qc = QuantumCircuit(num_qubits)
        rev_key = key[::-1]
        
        print("\nApplying correction gates:")
        for i in range(num_qubits):
            m_z = int(rev_key[2*i])
            m_x = int(rev_key[2*i + 1])
            
            if m_x == 1: 
                correction_qc.x(i)
                print(f"Qubit {i}: X")
            if m_z == 1: 
                correction_qc.z(i)
                print(f"Qubit {i}: Z")
        
        unlocked_sv = scrambled_sv.evolve(correction_qc)
        
        reconstructed = engine.decode_image(unlocked_sv.data, scaling_factor)
        reconstructed_grid = reconstructed.reshape(GRID_SIZE, GRID_SIZE)
        
        print(f"\nImage restored.")
        
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1)
        plt.title("Noise")
        plt.imshow(pre_correction.reshape(GRID_SIZE, GRID_SIZE), cmap='gray')
        
        plt.subplot(1, 2, 2)
        plt.title("Restored")
        plt.imshow(reconstructed_grid, cmap='gray')
        
        plt.savefig("quantum_bridge_result.png")
        print("Result saved.")

if __name__ == "__main__":
    run_receiver()
