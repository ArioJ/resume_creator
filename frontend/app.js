// Resume Advisor Platform - Frontend Logic

// State management
let state = {
    currentStep: 1,
    resumeId: null,
    resumeFile: null,
    jobDescription: '',
    analysisId: null
};

// DOM Elements
const elements = {
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    removeFileBtn: document.getElementById('removeFileBtn'),
    jobDescription: document.getElementById('jobDescription'),
    charCount: document.getElementById('charCount'),
    nextBtn1: document.getElementById('nextBtn1'),
    nextBtn2: document.getElementById('nextBtn2'),
    backBtn1: document.getElementById('backBtn1'),
    backBtn2: document.getElementById('backBtn2'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    previewFileName: document.getElementById('previewFileName'),
    previewJobLength: document.getElementById('previewJobLength')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // File upload events
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.fileInput.click();
    });
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.removeFileBtn.addEventListener('click', removeFile);

    // Drag and drop
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);

    // Job description
    elements.jobDescription.addEventListener('input', handleJobDescriptionInput);

    // Navigation buttons
    elements.nextBtn1.addEventListener('click', () => uploadResumeAndNext());
    elements.nextBtn2.addEventListener('click', () => goToStep(3));
    elements.backBtn1.addEventListener('click', () => goToStep(1));
    elements.backBtn2.addEventListener('click', () => goToStep(2));
    elements.analyzeBtn.addEventListener('click', startAnalysis);
}

// File handling
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function handleDragOver(e) {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function validateAndSetFile(file) {
    // Check file type
    const validTypes = ['.pdf', '.docx', '.txt'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        alert('Please upload a PDF, DOCX, or TXT file.');
        return;
    }

    // Check file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB.');
        return;
    }

    state.resumeFile = file;
    elements.fileName.textContent = file.name;
    elements.uploadArea.style.display = 'none';
    elements.fileInfo.style.display = 'flex';
    elements.nextBtn1.disabled = false;
}

function removeFile() {
    state.resumeFile = null;
    state.resumeId = null;
    elements.fileInput.value = '';
    elements.uploadArea.style.display = 'block';
    elements.fileInfo.style.display = 'none';
    elements.nextBtn1.disabled = true;
}

// Job description handling
function handleJobDescriptionInput(e) {
    const text = e.target.value;
    state.jobDescription = text;
    elements.charCount.textContent = text.length;
    
    // Enable next button if minimum length met
    elements.nextBtn2.disabled = text.length < 50;
}

// Step navigation
function goToStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });

    // Show target step
    document.getElementById(`step${stepNumber}`).classList.add('active');

    // Update step indicators
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 < stepNumber) {
            step.classList.add('completed');
        } else if (index + 1 === stepNumber) {
            step.classList.add('active');
        }
    });

    // Update preview in step 3
    if (stepNumber === 3) {
        elements.previewFileName.textContent = state.resumeFile.name;
        elements.previewJobLength.textContent = state.jobDescription.length;
    }

    state.currentStep = stepNumber;
}

// Upload resume and move to next step
async function uploadResumeAndNext() {
    if (!state.resumeFile) {
        alert('Please select a file first.');
        return;
    }

    // Show loading
    elements.nextBtn1.disabled = true;
    elements.nextBtn1.textContent = 'Uploading...';

    try {
        const formData = new FormData();
        formData.append('file', state.resumeFile);

        const response = await fetch('/api/upload-resume', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        state.resumeId = result.resume_id;

        console.log('Resume uploaded successfully:', result);

        // Move to step 2
        goToStep(2);
    } catch (error) {
        console.error('Upload error:', error);
        alert('Failed to upload resume: ' + error.message);
    } finally {
        elements.nextBtn1.disabled = false;
        elements.nextBtn1.textContent = 'Next: Job Description';
    }
}

// Start analysis
async function startAnalysis() {
    if (!state.resumeId || !state.jobDescription) {
        alert('Please complete all steps first.');
        return;
    }

    // Show loading overlay
    elements.loadingOverlay.style.display = 'flex';
    elements.analyzeBtn.disabled = true;

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                resume_id: state.resumeId,
                job_description: state.jobDescription
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const result = await response.json();
        state.analysisId = result.analysis_id;

        console.log('Analysis complete:', result);

        // Redirect to dashboard
        window.location.href = `/dashboard?analysis_id=${state.analysisId}`;
    } catch (error) {
        console.error('Analysis error:', error);
        alert('Failed to analyze resume: ' + error.message);
        elements.loadingOverlay.style.display = 'none';
        elements.analyzeBtn.disabled = false;
    }
}

