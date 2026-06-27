from qiskit import QuantumCircuit
import matplotlib.pyplot as plt
from quantum_engine import QuantumBridgeEngine

def draw_circuits():
    # 2x2 Circuit
    print("Generating 2x2 circuit...")
    engine_2x2 = QuantumBridgeEngine(num_qubits=2)
    dummy_2x2 = [0.5] * 4
    qc_2x2 = engine_2x2.get_teleportation_circuit(dummy_2x2)
    
    fig2 = qc_2x2.draw(output='mpl', style='iqp')
    plt.title("Circuit: 2x2 Grid")
    plt.savefig("circuit_2x2.png")
    print("Saved circuit_2x2.png")
    
    # 8x8 Circuit
    print("Generating 8x8 circuit...")
    engine_8x8 = QuantumBridgeEngine(num_qubits=6)
    dummy_8x8 = [0.125] * 64
    qc_8x8 = engine_8x8.get_teleportation_circuit(dummy_8x8)
    
    fig8 = qc_8x8.draw(output='mpl', style='iqp', fold=50) 
    plt.title("Circuit: 8x8 Grid")
    plt.savefig("circuit_8x8.png")
    print("Saved circuit_8x8.png")

if __name__ == "__main__":
    draw_circuits()
