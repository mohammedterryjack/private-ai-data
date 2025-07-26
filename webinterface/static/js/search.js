// Global content store for show more functionality
window.contentStore = {};
let contentStoreIndex = 0;

// Search Module for AI Data Platform
class SearchManager {
    constructor(services) {
        this.services = services;
        this.setupSearch();
    }
    
    setupSearch() {
        const searchForm = document.getElementById('searchForm');
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        
        console.log('Setting up search with elements:', { searchForm, searchInput, searchResults });
        
        if (!searchForm || !searchInput || !searchResults) return;
        
        searchForm.addEventListener('submit', (e) => {
            console.log('Search form submitted, preventing default');
            e.preventDefault();
            this.performSearch();
        });
        
        console.log('Search setup complete');
    }
    
    async performSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        const query = searchInput.value.trim();
        
        if (!query) {
            Utils.showNotification('Please enter a search query', 'warning');
            return;
        }
        
        console.log('Performing search for:', query);
        console.log('Search engine URL:', this.services.searchengine);
        
        // Show loading state
        searchResults.innerHTML = '<div class="loading">Searching...</div>';
        
        try {
            const requestBody = {
                query: query,
                n: 10
            };
            
            console.log('Search request body:', requestBody);
            
            const response = await fetch(`${this.services.searchengine}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log('Search response status:', response.status);
            console.log('Search response headers:', response.headers);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Search response data:', data);
            this.displaySearchResults(data || []);
            
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = `<div class="error">Search failed: ${error.message}</div>`;
            Utils.showNotification(`Search failed: ${error.message}`, 'error');
        }
    }
    
    displaySearchResults(results) {
        const searchResults = document.getElementById('searchResults');
        
        if (!results || results.length === 0) {
            searchResults.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }
        
        // Store search results globally for chat integration
        window.currentSearchResults = results;
        
        // Use the modular renderer
        const resultsHtml = results.map(result => window.renderResultItem(result, this.services)).join('');
        searchResults.innerHTML = resultsHtml;
        
        // Load images for image results
        this.loadResultImages(results);
    }
    
    async loadResultImages(results) {
        const imageResults = results.filter(result => !result.document_id);
        
        console.log('Loading images for results:', imageResults);
        
        for (const result of imageResults) {
            try {
                console.log(`Loading image for result ID: ${result.id}`);
                
                // Try the knowledgebase image serving endpoint
                try {
                    const response = await fetch(`${this.services.knowledgebase}/tables/images/${result.id}`);
                    if (response.ok) {
                        const blob = await response.blob();
                        const imageUrl = URL.createObjectURL(blob);
                        
                        const imgElement = document.getElementById(`image-${result.id}`);
                        if (imgElement) {
                            imgElement.src = imageUrl;
                            console.log(`Image loaded from knowledgebase for ID: ${result.id}`);
                        } else {
                            console.log(`Image element not found for ID: ${result.id}`);
                        }
                    } else {
                        console.log(`Knowledgebase image load failed for ID ${result.id}:`, response.status);
                        // Fallback to database query
                        await this.loadImageFromDatabase(result.id);
                    }
                } catch (kbError) {
                    console.log(`Knowledgebase image load failed for ID ${result.id}:`, kbError);
                    // Fallback to database query
                    await this.loadImageFromDatabase(result.id);
                }
            } catch (error) {
                console.error(`Failed to load image ${result.id}:`, error);
                this.setPlaceholderImage(result.id);
            }
        }
    }
    
    async loadImageFromDatabase(imageId) {
        try {
            const queryResponse = await fetch(`${this.services.knowledgebase}/tables/images/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: `SELECT content FROM images WHERE uuid = '${imageId}'`
                })
            });
            
            if (queryResponse.ok) {
                const queryData = await queryResponse.json();
                console.log(`Image query response for ID ${imageId}:`, queryData);
                
                if (queryData.results && queryData.results.length > 0) {
                    const imageData = queryData.results[0].content;
                    const imageUrl = `data:image/jpeg;base64,${imageData}`;
                    
                    const imgElement = document.getElementById(`image-${imageId}`);
                    if (imgElement) {
                        imgElement.src = imageUrl;
                        console.log(`Image set from database for ID: ${imageId}`);
                    } else {
                        console.log(`Image element not found for ID: ${imageId}`);
                    }
                } else {
                    console.log(`No image data found for ID: ${imageId}`);
                    this.setPlaceholderImage(imageId);
                }
            } else {
                console.log(`Image query failed for ID ${imageId}:`, queryResponse.status);
                this.setPlaceholderImage(imageId);
            }
        } catch (queryError) {
            console.error(`Image query error for ID ${imageId}:`, queryError);
            this.setPlaceholderImage(imageId);
        }
    }
    
    setPlaceholderImage(imageId) {
        const imgElement = document.getElementById(`image-${imageId}`);
        if (imgElement) {
            imgElement.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzY2NzM4NSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
        }
    }
}

// Global function for toggling PDF viewer
function togglePdfViewer(documentId) {
    const viewer = document.getElementById(`pdf-viewer-${documentId}`);
    const resultItem = viewer?.closest('.result-item');
    
    if (viewer) {
        if (viewer.style.display === 'none') {
            viewer.style.display = 'block';
            // Expand the result item when PDF viewer is shown
            if (resultItem) {
                resultItem.classList.add('pdf-expanded');
            }
            
            // Check if PDF viewer is working after a short delay
            setTimeout(() => {
                const pdfIframe = viewer.querySelector('iframe');
                const fallback = viewer.querySelector('.pdf-fallback');
                
                if (pdfIframe && fallback) {
                    // Add cache-busting timestamp to iframe src
                    const currentSrc = pdfIframe.src;
                    const separator = currentSrc.includes('?') ? '&' : '?';
                    pdfIframe.src = currentSrc + separator + 't=' + Date.now();
                    
                    // Try to detect if PDF viewer is working
                    pdfIframe.addEventListener('error', () => {
                        console.log('PDF viewer failed to load, showing fallback');
                        pdfIframe.style.display = 'none';
                        fallback.style.display = 'block';
                    });
                    
                    // Also check if the iframe has loaded content
                    pdfIframe.addEventListener('load', () => {
                        console.log('PDF viewer loaded successfully');
                    });
                    
                    // Check for 404 errors by testing the URL
                    const pdfUrl = viewer.getAttribute('data-pdf-url');
                    if (pdfUrl) {
                        fetch(pdfUrl, { method: 'GET' })
                            .then(response => {
                                if (!response.ok) {
                                    console.log(`PDF file not found (${response.status}), showing fallback`);
                                    pdfIframe.style.display = 'none';
                                    fallback.style.display = 'block';
                                }
                            })
                            .catch(error => {
                                console.log('PDF service unavailable, showing fallback:', error);
                                pdfIframe.style.display = 'none';
                                fallback.style.display = 'block';
                            });
                    }
                }
            }, 1000);
            
        } else {
            viewer.style.display = 'none';
            // Reset the result item height when PDF viewer is hidden
            if (resultItem) {
                resultItem.classList.remove('pdf-expanded');
            }
        }
    }
}

// Global function for toggling full content display
function toggleFullContent(button, fullContent) {
    console.log('toggleFullContent called with:', { button, fullContent: fullContent.substring(0, 50) + '...' });
    
    // Simple HTML escape function
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    const container = button.parentElement;
    console.log('Container:', container);
    
    // Find the content element - try multiple selectors
    let contentElement = container.querySelector('.result-text-content') || 
                        container.querySelector('.caption-section') || 
                        container.querySelector('.ocr-section');
    
    console.log('Content element found:', contentElement);
    
    // If no content element found, try to find it in the parent
    if (!contentElement) {
        contentElement = container.parentElement.querySelector('.caption-section') || 
                        container.parentElement.querySelector('.ocr-section');
        console.log('Content element found in parent:', contentElement);
    }
    
    // If we're in a caption or OCR section, we need to handle the HTML structure
    if (contentElement && (contentElement.classList.contains('caption-section') || contentElement.classList.contains('ocr-section'))) {
        console.log('Processing caption/OCR section');
        const strongElement = contentElement.querySelector('strong');
        if (strongElement) {
            console.log('Strong element found:', strongElement.textContent);
            
            if (button.textContent === 'Show more') {
                console.log('Showing full content');
                // Show full content
                const fullText = fullContent;
                // Replace everything after the strong element with the full content
                const strongText = strongElement.textContent;
                contentElement.innerHTML = `<strong>${strongText}</strong> ${escapeHtml(fullText)}`;
                // Re-add the button
                const newButton = document.createElement('button');
                newButton.className = 'btn btn-small show-more-btn showing-full';
                newButton.textContent = 'Show less';
                const contentId = button.getAttribute('data-content-id');
                if (contentId) {
                    newButton.setAttribute('data-content-id', contentId);
                }
                newButton.onclick = function() { 
                    const id = this.getAttribute('data-content-id');
                    if (id && window.contentStore[id]) {
                        toggleFullContent(this, window.contentStore[id]);
                    }
                };
                contentElement.appendChild(newButton);
            } else {
                console.log('Showing truncated content');
                // Show truncated content
                const maxLength = contentElement.classList.contains('caption-section') ? 200 : 150;
                const truncatedContent = fullContent.length > maxLength ? fullContent.substring(0, maxLength) + '...' : fullContent;
                const strongText = strongElement.textContent;
                contentElement.innerHTML = `<strong>${strongText}</strong> ${escapeHtml(truncatedContent)}`;
                // Re-add the button
                const newButton = document.createElement('button');
                newButton.className = 'btn btn-small show-more-btn';
                newButton.textContent = 'Show more';
                const contentId = button.getAttribute('data-content-id');
                if (contentId) {
                    newButton.setAttribute('data-content-id', contentId);
                }
                newButton.onclick = function() { 
                    const id = this.getAttribute('data-content-id');
                    if (id && window.contentStore[id]) {
                        toggleFullContent(this, window.contentStore[id]);
                    }
                };
                contentElement.appendChild(newButton);
            }
        } else {
            console.log('No strong element found');
        }
        return;
    }
    
    // Handle pre elements (for PDF content)
    if (contentElement && contentElement.tagName === 'PRE') {
        console.log('Processing PRE element');
        if (button.textContent === 'Show more') {
            // Show full content
            contentElement.textContent = fullContent;
            button.textContent = 'Show less';
            button.classList.add('showing-full');
        } else {
            // Show truncated content
            const maxLength = 500;
            const truncatedContent = fullContent.length > maxLength ? fullContent.substring(0, maxLength) + '...' : fullContent;
            contentElement.textContent = truncatedContent;
            button.textContent = 'Show more';
            button.classList.remove('showing-full');
        }
    }
    
    console.log('Function completed');
}

// Add CSS styles for result containers
function addResultStyles() {
    if (!document.getElementById('search-result-styles')) {
        const style = document.createElement('style');
        style.id = 'search-result-styles';
        style.textContent = `
            .result-item {
                max-height: 400px;
                overflow: hidden;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-bottom: 16px;
                background: white;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                transition: max-height 0.3s ease, overflow 0.3s ease;
            }
            
            .result-content {
                padding: 16px;
            }
            
            .result-text-container {
                max-height: 200px;
                overflow-y: auto;
                border: 1px solid #f3f4f6;
                border-radius: 4px;
                padding: 8px;
                background: #f9fafb;
                margin: 8px 0;
            }
            
            .result-text-content {
                margin: 0;
                font-size: 12px;
                line-height: 1.4;
                white-space: pre-wrap;
                word-wrap: break-word;
                max-height: 150px;
                overflow-y: auto;
            }
            
            .caption-section, .ocr-section {
                max-height: 120px;
                overflow-y: auto;
                padding: 8px;
                background: #f9fafb;
                border-radius: 4px;
                margin: 8px 0;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .show-more-btn {
                margin-top: 8px;
                font-size: 12px;
                padding: 6px 12px;
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: inline-block;
                font-weight: 500;
            }
            
            .show-more-btn:hover {
                background: #2563eb;
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
            }
            
            .show-more-btn.showing-full {
                background: #ef4444;
            }
            
            .show-more-btn.showing-full:hover {
                background: #dc2626;
                box-shadow: 0 2px 4px rgba(220, 38, 38, 0.2);
            }
            
            .result-meta {
                margin-top: 12px;
                padding-top: 8px;
                border-top: 1px solid #e5e7eb;
                font-size: 12px;
                color: #6b7280;
            }
            
            .result-actions {
                margin-top: 12px;
            }
            
            /* Ensure buttons are always visible */
            .result-text-container .show-more-btn,
            .caption-section .show-more-btn,
            .ocr-section .show-more-btn {
                position: relative;
                z-index: 10;
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize styles when the module loads
addResultStyles();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchManager;
} else {
    window.SearchManager = SearchManager;
}

// Global function for deleting results
async function deleteResult(uuid) {
    if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
        return;
    }
    
    try {
        // Get the searchengine URL from the global services
        const searchengineUrl = window.services?.searchengine || 'http://localhost:8001';
        
        const response = await fetch(`${searchengineUrl}/${uuid}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('Delete result:', result);
        
        // Remove the result from the UI
        const resultElement = document.querySelector(`[onclick*="${uuid}"]`)?.closest('.result-item');
        if (resultElement) {
            resultElement.remove();
            Utils.showNotification('Item deleted successfully', 'success');
        } else {
            Utils.showNotification('Item deleted from database', 'success');
        }
        
        // If no results left, show no results message
        const remainingResults = document.querySelectorAll('.result-item');
        if (remainingResults.length === 0) {
            const searchResults = document.getElementById('searchResults');
            searchResults.innerHTML = '<div class="no-results">No results found</div>';
        }
        
    } catch (error) {
        console.error('Delete error:', error);
        Utils.showNotification(`Failed to delete item: ${error.message}`, 'error');
    }
} 