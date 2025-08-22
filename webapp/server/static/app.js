// DEI Extractor Web App JavaScript

class DEIExtractorApp {
    constructor() {
        this.selectedFiles = [];
        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        this.uploadZone = document.getElementById('uploadZone');
        this.fileInput = document.getElementById('fileInput');
        this.fileList = document.getElementById('fileList');
        this.selectedFilesList = document.getElementById('selectedFiles');
        this.processBtn = document.getElementById('processBtn');
        this.progressSection = document.getElementById('progressSection');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.resultsSection = document.getElementById('resultsSection');
        this.resultsContent = document.getElementById('resultsContent');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.errorSection = document.getElementById('errorSection');
        this.errorMessage = document.getElementById('errorMessage');
    }

    setupEventListeners() {
        // Drag and drop events
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('dragover');
        });

        this.uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('dragover');
        });

        this.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files);
        });

        // File input change
        this.fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files);
        });

        // Process button
        this.processBtn.addEventListener('click', () => {
            this.processFiles();
        });

        // Download button
        this.downloadBtn.addEventListener('click', () => {
            this.downloadResults();
        });
    }

    handleFiles(files) {
        // Filter files by type
        const validFiles = files.filter(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            return ext === 'pdf' || ext === 'zip';
        });

        if (validFiles.length === 0) {
            this.showError('No valid files selected. Please select PDF or ZIP files.');
            return;
        }

        this.selectedFiles = validFiles;
        this.updateFileList();
        this.processBtn.disabled = false;
        this.hideError();
    }

    updateFileList() {
        if (this.selectedFiles.length === 0) {
            this.fileList.style.display = 'none';
            return;
        }

        this.fileList.style.display = 'block';
        this.selectedFilesList.innerHTML = '';

        this.selectedFiles.forEach(file => {
            const li = document.createElement('li');
            li.textContent = `${file.name} (${this.formatFileSize(file.size)})`;
            this.selectedFilesList.appendChild(li);
        });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async processFiles() {
        if (this.selectedFiles.length === 0) {
            this.showError('No files selected');
            return;
        }

        this.showProgress();
        this.processBtn.disabled = true;

        try {
            const formData = new FormData();

            // Add files
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            // Add options
            formData.append('apply_filter', document.getElementById('applyFilter').checked);
            formData.append('verbose', document.getElementById('verbose').checked);
            formData.append('language', document.getElementById('language').value);

            // Send request
            const response = await fetch('/api/jobs/download', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Processing failed');
            }

            // Get the ZIP file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            // Get filename from response headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'dei_extractor_results.zip';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            // Store for download
            this.downloadUrl = url;
            this.downloadFilename = filename;

            this.hideProgress();
            this.showResults('Processing completed successfully!');

        } catch (error) {
            console.error('Processing error:', error);
            this.hideProgress();
            this.showError(`Processing failed: ${error.message}`);
            this.processBtn.disabled = false;
        }
    }

    downloadResults() {
        if (this.downloadUrl) {
            const a = document.createElement('a');
            a.href = this.downloadUrl;
            a.download = this.downloadFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    }

    showProgress() {
        this.progressSection.style.display = 'block';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';

        // Animate progress bar
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            this.progressFill.style.width = `${progress}%`;
        }, 500);

        this.progressInterval = interval;
    }

    hideProgress() {
        this.progressSection.style.display = 'none';
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        this.progressFill.style.width = '100%';
    }

    showResults(message) {
        this.resultsContent.innerHTML = `<p>${message}</p>`;
        this.resultsSection.style.display = 'block';
        this.processBtn.disabled = false;
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorSection.style.display = 'block';
    }

    hideError() {
        this.errorSection.style.display = 'none';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DEIExtractorApp();
});
