import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from qiskit.quantum_info import Statevector, DensityMatrix

class QuantumBridgeEngine:
    def __init__(self, num_qubits=2):
        self.num_qubits = num_qubits
        self.simulator = Aer.get_backend('statevector_simulator')

    def encode_image_qpie(self, pixels):
        # Normalize pixel vector
        norm = np.linalg.norm(pixels)
        if norm == 0:
            amplitudes = np.ones(2**self.num_qubits) / np.sqrt(2**self.num_qubits)
        else:
            amplitudes = pixels / norm
        return amplitudes, norm

    def create_swapped_bridge(self):
        # 4 qubits: [A1, A2, B1, B2]
        qc = QuantumCircuit(4)
        
        # EPR pair 1
        qc.h(0)
        qc.cx(0, 1)
        
        # EPR pair 2
        qc.h(2)
        qc.cx(2, 3)
        
        # Swapping
        qc.cx(1, 2)
        qc.h(1)
        
        return qc

    def get_teleportation_circuit(self, image_amplitudes):
        n = self.num_qubits
        # Total qubits: n (image) + n (sender) + n (receiver) = 3n
        qc = QuantumCircuit(3*n, 2*n) 
        
        # Init image state
        qc.initialize(image_amplitudes, range(n))
        
        # Shared entanglement
        for i in range(n):
            qc.h(n + i)
            qc.cx(n + i, 2*n + i)
        
        # BSM
        for i in range(n):
            qc.cx(i, n + i)
            qc.h(i)
            qc.measure(i, 2*i)
            qc.measure(n + i, 2*i + 1)
        
        return qc

    def decode_image(self, statevector, scaling_factor):
        # Probs are |amp|^2
        probabilities = np.abs(statevector)**2
        reconstructed = np.sqrt(probabilities) * scaling_factor
        return reconstructed

    def get_mixed_state(self, num_qubits):
        dim = 2**num_qubits
        return DensityMatrix(np.eye(dim) / dim)
