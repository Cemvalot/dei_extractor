// DEI Extractor Web App JavaScript

class DEIExtractorApp {
    constructor() {
        this.selectedFiles = [];
        this.selectedTransformFile = null;
        this.currentTab = 'extract';
        this.translations = {
            gr: {
                noValidFiles: 'Δεν βρέθηκαν έγκυρα αρχεία. Παρακαλώ επιλέξτε αρχεία PDF ή ZIP.',
                noFilesSelected: 'Δεν επιλέχθηκαν αρχεία',
                processingFailed: 'Η επεξεργασία απέτυχε',
                downloadFailed: 'Η λήψη απέτυχε',
                processingCompleted: 'Η επεξεργασία ολοκληρώθηκε επιτυχώς!',
                processingFiles: 'Επεξεργασία αρχείων...',
                preparingFiles: 'Προετοιμασία αρχείων...',
                validatingInput: 'Επικύρωση εισόδου...',
                creatingOutput: 'Δημιουργία αρχείων εξόδου...',
                creatingZip: 'Δημιουργία αρχείου ZIP...',
                validationFailed: 'Η επικύρωση απέτυχε',
                processingFailedMsg: 'Η επεξεργασία απέτυχε',
                errorDuringProcessing: 'Σφάλμα κατά την επεξεργασία',
                noValidDataFile: 'Δεν βρέθηκε έγκυρο αρχείο δεδομένων. Παρακαλώ επιλέξτε αρχείο XLSX ή CSV.',
                noDataFileSelected: 'Δεν επιλέχθηκε αρχείο δεδομένων',
                transformFailed: 'Ο μετασχηματισμός απέτυχε',
                transformCompleted: 'Ο μετασχηματισμός ολοκληρώθηκε επιτυχώς!',
                transformingData: 'Μετασχηματισμός δεδομένων...'
            },
            en: {
                noValidFiles: 'No valid files selected. Please select PDF or ZIP files.',
                noFilesSelected: 'No files selected',
                processingFailed: 'Processing failed',
                downloadFailed: 'Download failed',
                processingCompleted: 'Processing completed successfully!',
                processingFiles: 'Processing files...',
                preparingFiles: 'Preparing files...',
                validatingInput: 'Validating input...',
                creatingOutput: 'Creating output files...',
                creatingZip: 'Creating ZIP file...',
                validationFailed: 'Validation failed',
                processingFailedMsg: 'Processing failed',
                errorDuringProcessing: 'Error during processing',
                noValidDataFile: 'No valid data file selected. Please select XLSX or CSV file.',
                noDataFileSelected: 'No data file selected',
                transformFailed: 'Transform failed',
                transformCompleted: 'Transform completed successfully!',
                transformingData: 'Transforming data...'
            }
        };
        this.currentLanguage = 'gr'; // Default to Greek
        this.initializeElements();
        this.setupEventListeners();
        this.updateLanguage();
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

        // Language change
        document.getElementById('language').addEventListener('change', (e) => {
            this.currentLanguage = e.target.value;
            this.updateLanguage();
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

    updateLanguage() {
        // Update UI elements based on current language
        const lang = this.translations[this.currentLanguage];

        // Update progress text if visible
        if (this.progressSection.style.display !== 'none') {
            this.progressText.textContent = lang.processingFiles;
        }
    }

    handleFiles(files) {
        // Filter files by type
        const validFiles = files.filter(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            return ext === 'pdf' || ext === 'zip';
        });

        if (validFiles.length === 0) {
            this.showError(this.translations[this.currentLanguage].noValidFiles);
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
            this.showError(this.translations[this.currentLanguage].noFilesSelected);
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

            // Use the new progress endpoint
            const response = await fetch('/api/jobs/progress', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || this.translations[this.currentLanguage].processingFailed);
            }

            // Handle Server-Sent Events for progress updates
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            // Update progress bar
                            this.progressFill.style.width = `${data.percentage}%`;
                            this.progressText.textContent = data.message;

                            // Check if processing is complete
                            if (data.percentage === 100) {
                                if (data.download_ready) {
                                    this.hideProgress();
                                    this.showResults(this.translations[this.currentLanguage].processingCompleted);

                                    // Store download info
                                    this.downloadUrl = null; // Will be downloaded separately
                                    this.downloadFilename = data.filename || 'dei_extractor_results.zip';

                                    // Trigger download
                                    this.downloadResults();
                                } else {
                                    this.hideProgress();
                                    this.showError(data.message);
                                    this.processBtn.disabled = false;
                                }
                                return;
                            }
                        } catch (e) {
                            console.error('Error parsing progress data:', e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Processing error:', error);
            this.hideProgress();
            this.showError(`${this.translations[this.currentLanguage].processingFailed}: ${error.message}`);
            this.processBtn.disabled = false;
        }
    }

    downloadResults() {
        if (this.downloadFilename) {
            // Create a new request to get the ZIP file
            const formData = new FormData();

            // Add files
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            // Add options
            formData.append('apply_filter', document.getElementById('applyFilter').checked);
            formData.append('verbose', document.getElementById('verbose').checked);
            formData.append('language', document.getElementById('language').value);

            // Download the ZIP file
            fetch('/api/jobs/download', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Download failed');
                }
                return response.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = this.downloadFilename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Download error:', error);
                this.showError(this.translations[this.currentLanguage].downloadFailed + ': ' + error.message);
            });
        }
    }

    showProgress() {
        this.progressSection.style.display = 'block';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        this.progressFill.style.width = '0%';
        this.progressText.textContent = this.translations[this.currentLanguage].processingFiles;
    }

    hideProgress() {
        this.progressSection.style.display = 'none';
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
