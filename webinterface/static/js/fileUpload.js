// File Upload Module for AI Data Platform
class FileUploadManager {
    constructor(services) {
        this.services = services;
        this.setupFileUpload();
    }
    
    setupFileUpload() {
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        
        if (!uploadZone || !fileInput) return;
        
        // File input change event
        fileInput.addEventListener('change', (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
                this.handleFiles(files);
            }
        });
        
        // Drag and drop functionality
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        
        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            this.handleFiles(files);
            this.hideUploadOverlay();
        });
        
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });
    }
    
    async handleFiles(files) {
        if (!files || files.length === 0) return;
        
        const fileList = document.getElementById('fileList');
        if (!fileList) return;
        
        // Clear previous files
        fileList.innerHTML = '';
        
        // Process files and upload them
        await this.uploadFiles(files);
    }
    
    async uploadFiles(files) {
        const fileList = document.getElementById('fileList');
        if (!fileList) return;
        
        const uploadPromises = [];
        const fileItems = [];
        
        // Create file items and prepare upload promises
        Array.from(files).forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-info">
                    <span class="file-name">${Utils.escapeHtml(file.name)}</span>
                    <span class="file-size">${Utils.formatFileSize(file.size)}</span>
                </div>
                <div class="file-status">
                    <span class="status-text">Pending...</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                </div>
            `;
            fileList.appendChild(fileItem);
            fileItems.push(fileItem);
            
            // Check file type and route to appropriate upload function
            console.log(`File: ${file.name}, Type: ${file.type}, Size: ${file.size}`);
            
            const fileName = file.name.toLowerCase();
            const fileType = file.type.toLowerCase();
            
            console.log(`Enhanced detection - File name: ${fileName}, File type: ${fileType}`);
            
            if (fileType.startsWith('image/')) {
                console.log('Detected as image file');
                uploadPromises.push(this.uploadImageWithStreaming(file, fileItem));
            } else if (fileType === 'application/pdf' || fileName.endsWith('.pdf')) {
                console.log('Detected as PDF file');
                uploadPromises.push(this.uploadPdfWithStreaming(file, fileItem));
            } else {
                console.log('Unsupported file type');
                fileItem.querySelector('.status-text').textContent = 'Unsupported file type';
                fileItem.classList.add('file-error');
            }
        });
        
        // Wait for all uploads to complete
        try {
            const results = await Promise.allSettled(uploadPromises);
            
            // Process results
            results.forEach((result, index) => {
                const fileItem = fileItems[index];
                if (result.status === 'fulfilled') {
                    fileItem.querySelector('.status-text').textContent = 'Uploaded successfully';
                    fileItem.classList.add('file-success');
                    Utils.showNotification(`File "${files[index].name}" uploaded successfully!`, 'success');
                } else {
                    fileItem.querySelector('.status-text').textContent = `Upload failed: ${result.reason}`;
                    fileItem.classList.add('file-error');
                    Utils.showNotification(`Failed to upload "${files[index].name}": ${result.reason}`, 'error');
                }
            });
            
            // Clear file input
            document.getElementById('fileInput').value = '';
            
            // Add click handler to dismiss upload results
            const dismissUploadResults = (e) => {
                const clickedElement = e.target;
                const isClickInsideFileItem = fileItems.some(item => item.contains(clickedElement));
                const isClickInsideUploadTrigger = document.getElementById('uploadTrigger')?.contains(clickedElement);
                
                if (!isClickInsideFileItem && !isClickInsideUploadTrigger) {
                    fileItems.forEach(item => item.remove());
                    document.removeEventListener('click', dismissUploadResults);
                }
            };
            
            setTimeout(() => {
                document.addEventListener('click', dismissUploadResults);
            }, 1000);
        } catch (error) {
            console.error('Upload error:', error);
            Utils.showNotification(`Upload failed: ${error.message}`, 'error');
        }
    }
    
    async uploadImageWithStreaming(file, fileItem) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            const progressFill = fileItem.querySelector('.progress-fill');
            const statusText = fileItem.querySelector('.status-text');
            const xhr = new XMLHttpRequest();
            let buffer = '';
            let captionBuffer = '';
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    const totalProgress = percentComplete * 0.2;
                    progressFill.style.width = totalProgress + '%';
                    statusText.textContent = `Uploading file... ${Math.round(percentComplete)}%`;
                }
            });
            
            xhr.addEventListener('readystatechange', () => {
                if (xhr.readyState === 3 || xhr.readyState === 4) {
                    const newData = xhr.responseText.substring(buffer.length);
                    buffer = xhr.responseText;
                    
                    if (newData) {
                        console.log('New streaming data received:', newData);
                    }
                    
                    const lines = newData.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                console.log('Parsed streaming data:', data);
                                
                                if (data.type === 'progress') {
                                    const totalProgress = 20 + (data.percent * 0.8);
                                    progressFill.style.width = totalProgress + '%';
                                    
                                    if (data.stage && data.stage.startsWith('CAPTION_CHUNK:')) {
                                        const captionChunk = data.stage.replace('CAPTION_CHUNK:', '');
                                        captionBuffer += captionChunk;
                                        
                                        const wordCount = captionBuffer.trim().split(/\s+/).length;
                                        const captionProgress = Math.min(wordCount / 30, 1);
                                        const totalProgress = 20 + (30 * 0.8) + (captionProgress * 30 * 0.8);
                                        
                                        progressFill.style.width = totalProgress + '%';
                                        statusText.textContent = captionBuffer;
                                        statusText.style.color = '#10b981';
                                    } else if (data.stage && data.stage.startsWith('OCR_TEXT:')) {
                                        const ocrText = data.stage.replace('OCR_TEXT:', '');
                                        console.log('OCR text received:', ocrText);
                                        statusText.textContent = `OCR Text: ${ocrText}`;
                                        statusText.style.color = '#3b82f6';
                                    } else {
                                        statusText.textContent = data.stage;
                                        statusText.style.color = '';
                                    }
                                } else if (data.type === 'complete') {
                                    progressFill.style.width = '100%';
                                    statusText.textContent = 'Upload complete!';
                                    this.displayUploadResults(fileItem, data);
                                    resolve(data);
                                } else if (data.type === 'error') {
                                    reject(data.detail || 'Upload failed');
                                }
                            } catch (e) {
                                console.error('Error parsing stream data:', e);
                            }
                        }
                    }
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status !== 200) {
                    reject(`HTTP ${xhr.status}: ${xhr.statusText}`);
                }
            });
            
            xhr.addEventListener('error', () => {
                reject('Network error');
            });
            
            xhr.addEventListener('abort', () => {
                reject('Upload cancelled');
            });
            
            xhr.open('POST', `${this.services.fileingestor}/ingest_image/stream/`);
            xhr.send(formData);
        });
    }
    
    async uploadPdfWithStreaming(file, fileItem) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            const progressFill = fileItem.querySelector('.progress-fill');
            const statusText = fileItem.querySelector('.status-text');
            const xhr = new XMLHttpRequest();
            let buffer = '';
            let jsonBuffer = '';
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    const totalProgress = percentComplete * 0.2;
                    progressFill.style.width = totalProgress + '%';
                    statusText.textContent = `Uploading file... ${Math.round(percentComplete)}%`;
                }
            });
            
            xhr.addEventListener('readystatechange', () => {
                if (xhr.readyState === 3 || xhr.readyState === 4) {
                    const newData = xhr.responseText.substring(buffer.length);
                    buffer = xhr.responseText;
                    
                    if (newData) {
                        console.log('New PDF streaming data received:', newData);
                    }
                    
                    const lines = newData.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                console.log('Parsed PDF streaming data:', data);
                                
                                if (data.type === 'progress') {
                                    progressFill.style.width = data.percent + '%';
                                    
                                    if (data.stage && data.stage.startsWith('STRUCTURED_CHUNK:')) {
                                        const jsonChunk = data.stage.substring('STRUCTURED_CHUNK:'.length);
                                        jsonBuffer += jsonChunk;
                                        
                                        const jsonLength = jsonBuffer.length;
                                        const maxExpectedLength = 2000;
                                        const jsonProgress = Math.min(jsonLength / maxExpectedLength, 1);
                                        const totalProgress = 20 + 30 + (jsonProgress * 40);
                                        
                                        progressFill.style.width = totalProgress + '%';
                                        this.displayStreamingJsonChunk(fileItem, jsonChunk, jsonBuffer);
                                        statusText.textContent = 'Structuring document...';
                                        statusText.style.color = '#10b981';
                                    } else if (data.stage && data.stage !== 'Extracting text from PDF' && 
                                        data.stage !== 'Text extraction complete' && 
                                        data.stage !== 'Structuring text with LLM' &&
                                        data.stage !== 'Generating keywords' &&
                                        data.stage !== 'Keywords generated' &&
                                        data.stage !== 'Generating vector embeddings' &&
                                        data.stage !== 'Vector embeddings generated' &&
                                        data.stage !== 'Saving to database' &&
                                        data.stage !== 'PDF processing complete') {
                                        
                                        jsonBuffer += data.stage;
                                        const jsonLength = jsonBuffer.length;
                                        const maxExpectedLength = 2000;
                                        const jsonProgress = Math.min(jsonLength / maxExpectedLength, 1);
                                        const totalProgress = 20 + 30 + (jsonProgress * 40);
                                        
                                        progressFill.style.width = totalProgress + '%';
                                        this.displayStreamingJsonChunk(fileItem, data.stage, jsonBuffer);
                                        statusText.textContent = 'Structuring document...';
                                        statusText.style.color = '#10b981';
                                    } else {
                                        statusText.textContent = data.stage;
                                        statusText.style.color = '';
                                    }
                                } else if (data.type === 'complete') {
                                    progressFill.style.width = '100%';
                                    statusText.textContent = 'Upload complete!';
                                    this.displayUploadResults(fileItem, data);
                                    resolve(data);
                                } else if (data.type === 'error') {
                                    reject(data.detail || 'Upload failed');
                                }
                            } catch (e) {
                                console.error('Error parsing PDF stream data:', e);
                            }
                        }
                    }
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status !== 200) {
                    reject(`HTTP ${xhr.status}: ${xhr.statusText}`);
                }
            });
            
            xhr.addEventListener('error', () => {
                reject('Network error');
            });
            
            xhr.addEventListener('abort', () => {
                reject('Upload cancelled');
            });
            
            xhr.open('POST', `${this.services.fileingestor}/ingest_pdf/stream/`);
            xhr.send(formData);
        });
    }
    
    displayUploadResults(fileItem, data) {
        const existingResults = fileItem.querySelector('.upload-results');
        if (existingResults) {
            existingResults.remove();
        }
        
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'upload-results';
        
        if (data.document_id) {
            // PDF results
            resultsContainer.innerHTML = `
                <strong>Upload Results:</strong>
                <div class="result-item"><strong>Document ID:</strong> ${data.document_id}</div>
                <div class="result-item"><strong>Content Length:</strong> ${data.content_length} characters</div>
                <div class="result-item"><strong>Keywords:</strong> ${data.keywords ? data.keywords.join(', ') : 'None'}</div>
                <div class="result-item"><strong>Vector Length:</strong> ${data.vector_length}</div>
                <div class="result-item"><strong>File Path:</strong> ${data.file_path || 'N/A'}</div>
            `;
        } else {
            // Image results
            resultsContainer.innerHTML = `
                <strong>Upload Results:</strong>
                <div class="result-item"><strong>Image ID:</strong> ${data.image_id}</div>
                <div class="result-item"><strong>Caption:</strong> ${Utils.escapeHtml(data.caption)}</div>
                ${data.ocr_text ? `<div class="result-item"><strong>OCR Text:</strong> ${Utils.escapeHtml(data.ocr_text)}</div>` : ''}
                <div class="result-item"><strong>Keywords:</strong> ${data.keywords ? data.keywords.join(', ') : 'None'}</div>
                <div class="result-item"><strong>Vector Length:</strong> ${data.vector_length}</div>
            `;
        }
        fileItem.appendChild(resultsContainer);
    }
    
    displayStreamingJsonChunk(fileItem, chunk, jsonBuffer) {
        const existing = fileItem.querySelector('.streaming-json');
        if (existing) existing.remove();

        const jsonDisplay = document.createElement('div');
        jsonDisplay.className = 'streaming-json';
        jsonDisplay.style.cssText = `
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
            max-height: 200px;
            overflow: auto;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.4;
        `;
        
        try {
            const parsed = JSON.parse(chunk);
            jsonDisplay.textContent = JSON.stringify(parsed, null, 2);
        } catch (e) {
            let cleanContent = chunk;
            let braceCount = 0;
            let bracketCount = 0;
            let lastCompleteIndex = -1;
            
            for (let i = 0; i < chunk.length; i++) {
                const char = chunk[i];
                if (char === '{') braceCount++;
                else if (char === '}') braceCount--;
                else if (char === '[') bracketCount++;
                else if (char === ']') bracketCount--;
                
                if (braceCount === 0 && bracketCount === 0 && (char === '}' || char === ']')) {
                    lastCompleteIndex = i;
                }
            }
            
            if (lastCompleteIndex > 0) {
                cleanContent = chunk.substring(0, lastCompleteIndex + 1);
                
                try {
                    const parsed = JSON.parse(cleanContent);
                    jsonDisplay.textContent = JSON.stringify(parsed, null, 2);
                    
                    if (cleanContent.length < chunk.length) {
                        jsonDisplay.textContent += '\n\n... (streaming)';
                    }
                } catch (e2) {
                    jsonDisplay.textContent = cleanContent;
                    if (cleanContent.length < chunk.length) {
                        jsonDisplay.textContent += '\n\n... (streaming)';
                    }
                }
            } else {
                jsonDisplay.textContent = chunk + '\n\n... (streaming)';
            }
        }
        
        const progressBar = fileItem.querySelector('.file-status');
        if (progressBar) {
            progressBar.parentNode.insertBefore(jsonDisplay, progressBar);
        }
        
        jsonDisplay.scrollTop = jsonDisplay.scrollHeight;
    }
    
    showUploadOverlay() {
        const overlay = document.getElementById('uploadOverlay');
        if (overlay) {
            overlay.style.display = 'flex';
            document.addEventListener('click', this.handleDocumentClick);
        }
    }
    
    hideUploadOverlay() {
        const overlay = document.getElementById('uploadOverlay');
        if (overlay) {
            overlay.style.display = 'none';
            document.removeEventListener('click', this.handleDocumentClick);
        }
    }
    
    handleDocumentClick = (e) => {
        const overlay = document.getElementById('uploadOverlay');
        const uploadZone = document.getElementById('uploadZone');
        
        if (overlay && overlay.style.display === 'flex') {
            if (!uploadZone.contains(e.target) && !e.target.closest('#uploadTrigger')) {
                this.hideUploadOverlay();
            }
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FileUploadManager;
} else {
    window.FileUploadManager = FileUploadManager;
} 