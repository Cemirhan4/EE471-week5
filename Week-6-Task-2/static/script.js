const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const dropContent = document.getElementById('dropContent');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const btnRemove = document.getElementById('btnRemove');
const btnClassify = document.getElementById('btnClassify');
const emptyState = document.getElementById('emptyState');
const resultsContainer = document.getElementById('resultsContainer');
const predictionList = document.getElementById('predictionList');
const topBreedName = document.getElementById('topBreedName');
const topConfidence = document.getElementById('topConfidence');

let selectedFile = null;

// Click drop zone to browse
dropZone.addEventListener('click', (e) => {
    if (e.target !== btnRemove) {
        fileInput.click();
    }
});

// File input change
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Drag & Drop
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });
});

dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file (PNG, JPG, WEBP).');
        return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        dropContent.style.display = 'none';
        previewContainer.style.display = 'flex';
        btnClassify.disabled = false;
    };
    reader.readAsDataURL(file);
}

// Remove Image
btnRemove.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    previewContainer.style.display = 'none';
    dropContent.style.display = 'flex';
    btnClassify.disabled = true;
    emptyState.style.display = 'flex';
    resultsContainer.style.display = 'none';
});

// Quick sample cat images
function loadSampleCat(breed) {
    // Generate an illustrative canvas preview or sample image
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');

    // Create colored gradient placeholder representing cat
    const grad = ctx.createLinearGradient(0, 0, 400, 400);
    if (breed === 'tiger_cat') {
        grad.addColorStop(0, '#f97316');
        grad.addColorStop(0.5, '#ea580c');
        grad.addColorStop(1, '#7c2d12');
    } else if (breed === 'tabby') {
        grad.addColorStop(0, '#a8a29e');
        grad.addColorStop(0.5, '#78716c');
        grad.addColorStop(1, '#44403c');
    } else {
        grad.addColorStop(0, '#fef08a');
        grad.addColorStop(0.5, '#fde047');
        grad.addColorStop(1, '#ca8a04');
    }
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 400, 400);

    // Draw cute cat face icon on canvas
    ctx.fillStyle = '#ffffff';
    ctx.font = '72px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('🐱', 200, 210);
    ctx.font = '24px system-ui';
    ctx.fillText(breed.replace('_', ' ').toUpperCase(), 200, 270);

    canvas.toBlob((blob) => {
        const file = new File([blob], `${breed}.jpg`, { type: 'image/jpeg' });
        handleFile(file);
    }, 'image/jpeg');
}

// Classify Button
btnClassify.addEventListener('click', async () => {
    if (!selectedFile) return;

    const btnText = btnClassify.querySelector('.btn-text');
    const btnSpinner = btnClassify.querySelector('.btn-spinner');

    btnText.textContent = 'Analyzing with Cog...';
    btnSpinner.style.display = 'inline-block';
    btnClassify.disabled = true;

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
        const response = await fetch('/api/classify', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            renderPredictions(data.predictions);
        } else {
            alert(data.error || 'Prediction failed. Check container logs.');
        }
    } catch (err) {
        alert('Could not communicate with the server: ' + err.message);
    } finally {
        btnText.textContent = '⚡ Classify Cat Breed';
        btnSpinner.style.display = 'none';
        btnClassify.disabled = false;
    }
});

function renderPredictions(predictions) {
    emptyState.style.display = 'none';
    resultsContainer.style.display = 'block';
    predictionList.innerHTML = '';

    const entries = Object.entries(predictions);
    if (entries.length === 0) return;

    // Top prediction
    const [topBreed, topScore] = entries[0];
    topBreedName.textContent = topBreed.replace(/_/g, ' ');
    topConfidence.textContent = topScore;

    // List all
    entries.forEach(([breed, score]) => {
        const cleanBreed = breed.replace(/_/g, ' ');
        const numVal = parseFloat(score);

        const item = document.createElement('div');
        item.className = 'pred-item';
        item.innerHTML = `
            <div class="pred-header">
                <span>${cleanBreed}</span>
                <span>${score}</span>
            </div>
            <div class="pred-bar-bg">
                <div class="pred-bar-fill" style="width: ${Math.min(numVal, 100)}%;"></div>
            </div>
        `;
        predictionList.appendChild(item);
    });
}
