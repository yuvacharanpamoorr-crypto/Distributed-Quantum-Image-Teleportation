const socket = io();

socket.on('connect', () => {
    console.log("Connected to server");
    document.querySelector('.status-dot').style.backgroundColor = '#00ff99';
});

socket.on('disconnect', () => {
    console.log("Disconnected from server");
    document.querySelector('.status-dot').style.backgroundColor = '#ff3366';
});

function setRole(role) {
    const senderPanel = document.getElementById('sender-node');
    const receiverPanel = document.getElementById('receiver-node');
    const roleSelector = document.getElementById('role-selector');
    
    if (role === 'sender') {
        receiverPanel.classList.add('hidden');
        senderPanel.classList.remove('hidden');
    } else {
        senderPanel.classList.add('hidden');
        receiverPanel.classList.remove('hidden');
    }
    
    roleSelector.style.display = 'none';
}

const fileInput = document.getElementById('file-input');
const senderPreview = document.getElementById('sender-preview');
const senderPreviewContainer = document.getElementById('sender-preview-container');
const teleportBtn = document.getElementById('teleport-btn');
const senderStatus = document.getElementById('sender-status');
const receiverStatus = document.getElementById('receiver-status');
const packetLog = document.getElementById('packet-log');
const noiseCanvas = document.getElementById('noise-canvas');
const restoredCanvas = document.getElementById('restored-canvas');
const photon = document.getElementById('photon');

let currentImageData = null;

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            currentImageData = event.target.result;
            senderPreview.src = currentImageData;
            senderPreviewContainer.classList.remove('hidden');
            senderPreview.classList.remove('dissolve');
            senderStatus.innerText = "Ready to teleport.";
        };
        reader.readAsDataURL(file);
    }
});

teleportBtn.addEventListener('click', () => {
    if (!currentImageData) return;

    senderStatus.innerText = "Measuring...";
    
    senderPreview.classList.add('dissolve');
    document.getElementById('quantum-blob').classList.add('animate-teleport');
    
    socket.emit('teleport_request', { image: currentImageData });

    setTimeout(() => {
        senderStatus.innerHTML = "<span style='color: #ff3366'>State destroyed</span><br>Sent to bridge.";
        teleportBtn.disabled = true;
        senderPreviewContainer.classList.add('hidden');
    }, 1000);
});

socket.on('quantum_state_received', (data) => {
    console.log("Packet:", data);
    
    setTimeout(() => {
        document.getElementById('classical-bit').classList.add('animate-teleport');
        
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `[IN] Key: ${data.key} | Scale: ${data.scaling_factor.toFixed(4)}`;
        packetLog.prepend(logEntry);
    }, 800);
    
    receiverStatus.innerText = "Processing state...";

    const n = data.original_size;
    const scrambled = data.scrambled_state;
    const key = data.key;
    const scaling = data.scaling_factor;

    // Show noise
    drawPixels(noiseCanvas, scrambled, n, scaling);

    // 3. Display Restored State (Receiver performs the math!)
    setTimeout(() => {
        const numQubits = Math.log2(scrambled.length);
        const correctedState = applyCorrections(scrambled, key, numQubits);
        
        drawPixels(restoredCanvas, correctedState, n, scaling, true);
        receiverStatus.innerHTML = "<span style='color: #00ff99'>RESTORED SUCCESSFUL</span>";
        
        // Show download button
        document.getElementById('download-btn').classList.remove('hidden');
    }, 1500);
});

function downloadRestored() {
    const canvas = document.getElementById('restored-canvas');
    const link = document.createElement('a');
    link.download = 'quantum_teleported_image.png';
    link.href = canvas.toDataURL();
    link.click();
}

function drawPixels(canvas, stateData, n, scaling, isRestored = false) {
    canvas.width = n;
    canvas.height = n;
    const ctx = canvas.getContext('2d');
    const imgData = ctx.createImageData(n, n);
    
    console.log(`[*] Receiver Measuring ${n}x${n} State...`);

    for (let i = 0; i < stateData.length; i++) {
        let val;
        // Strict Quantum Measurement: 
        // Calculate the probability P = |amplitude|^2 
        // Then take the square root to get intensity.
        if (Array.isArray(stateData[i])) {
            const real = stateData[i][0];
            const imag = stateData[i][1];
            // Find the intensity purely from the received state
            val = Math.sqrt(real*real + imag*imag) * scaling;
        } else {
            val = Math.abs(stateData[i]) * scaling;
        }
        
        imgData.data[i * 4] = val;
        imgData.data[i * 4 + 1] = val;
        imgData.data[i * 4 + 2] = val;
        imgData.data[i * 4 + 3] = 255;
    }
    
    ctx.putImageData(imgData, 0, 0);
}

function applyCorrections(stateData, keyString, numQubits) {
    let state = stateData.map(v => ({re: v[0], im: v[1]}));
    
    const revKey = keyString.split('').reverse().join(''); 
    
    console.log("Applying Pauli corrections");

    for (let i = 0; i < numQubits; i++) {
        const zBit = revKey[2*i] === '1';
        const xBit = revKey[2*i+1] === '1';
        
        if (xBit) {
            const step = 1 << i;
            for (let j = 0; j < state.length; j += (step * 2)) {
                for (let k = 0; k < step; k++) {
                    let temp = state[j + k];
                    state[j + k] = state[j + k + step];
                    state[j + k + step] = temp;
                }
            }
        }
        
        if (zBit) {
            const step = 1 << i;
            for (let j = 0; j < state.length; j++) {
                if ((j >> i) & 1) {
                    state[j].re = -state[j].re;
                    state[j].im = -state[j].im;
                }
            }
        }
    }
    
    return state.map(v => [v.re, v.im]);
}
