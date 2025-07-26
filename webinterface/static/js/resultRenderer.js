// Result Renderer Module
// Renders PDF and image results for the search UI

function renderResultItem(result, services) {
    if (result.document_id) {
        // PDF result
        const content = result.structured_json || result.content || 'No content available';
        const formattedContent = typeof content === 'object' ? JSON.stringify(content, null, 2) : content;
        return `
            <div class="result-item">
                <div class="result-content">
                    <div class="result-title">Document ${result.document_id ? result.document_id.substring(0, 8) + '...' : 'Unknown'}</div>
                    <div class="result-text-container">
                        <pre class="result-text-content">${Utils.escapeHtml(formattedContent)}</pre>
                    </div>
                    <div class="result-meta">
                        <span class="result-type">PDF</span>
                        <span class="result-score">Score: ${typeof result.similarity === 'number' ? result.similarity.toFixed(3) : 'N/A'}</span>
                        ${result.file_path ? `<span class="result-path">Path: ${Utils.escapeHtml(result.file_path)}</span>` : ''}
                    </div>
                    <div class="result-actions">
                        <button class="btn btn-small" onclick="togglePdfViewer('${result.document_id}')">
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            View PDF
                        </button>
                        <button class="btn btn-small btn-danger" onclick="deleteResult('${result.document_id || result.id}')" title="Delete this document">
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                            Delete
                        </button>
                    </div>
                    <div id="pdf-viewer-${result.document_id}" class="pdf-viewer" style="display: none;" data-pdf-url="${result.file_path || services.knowledgebase + '/tables/documents/' + result.document_id}?t=${Date.now()}">
                        <iframe 
                            src="${result.file_path || services.knowledgebase + '/tables/documents/' + result.document_id}?t=${Date.now()}" 
                            width="100%" 
                            height="600px"
                            style="border: 1px solid #e5e7eb; border-radius: 8px; background: white;"
                            frameborder="0"
                            allowfullscreen="false">
                        </iframe>
                        <div class="pdf-fallback" style="display: none; padding: 20px; text-align: center; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px;">
                            <p>PDF file not found or service unavailable. 
                                <a href="${result.file_path || services.knowledgebase + '/tables/documents/' + result.document_id}?t=${Date.now()}" target="_blank" class="btn btn-small">Try Download</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Image result
        const caption = result.caption || 'No caption available';
        const ocrText = result.ocr_text || '';
        return `
            <div class="result-item">
                <div class="result-image">
                    <img id="image-${result.id}" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzY2NzM4NSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkxvYWRpbmcuLi48L3RleHQ+PC9zdmc+" alt="Loading..." style="max-width: 200px; max-height: 200px; object-fit: cover; border-radius: 8px;">
                </div>
                <div class="result-content">
                    <div class="result-title">Image ${result.id ? result.id.substring(0, 8) + '...' : 'Unknown'}</div>
                    <div class="result-text">
                        <div class="caption-section">
                            <strong>LLM Caption:</strong> ${Utils.escapeHtml(caption)}
                        </div>
                        ${ocrText ? `
                            <div class="ocr-section">
                                <strong>OCR Text:</strong> ${Utils.escapeHtml(ocrText)}
                            </div>
                        ` : ''}
                    </div>
                    <div class="result-meta">
                        <span class="result-type">Image</span>
                        <span class="result-score">Score: ${typeof result.similarity === 'number' ? result.similarity.toFixed(3) : 'N/A'}</span>
                    </div>
                    <div class="result-actions">
                        <button class="btn btn-small btn-danger" onclick="deleteResult('${result.id}')" title="Delete this image">
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderResultItem };
} else {
    window.renderResultItem = renderResultItem;
} 