// Configuration for AI Data Platform
const CONFIG = {
    services: {
        knowledgebase: 'http://localhost:8002',
        searchengine: 'http://localhost:8001',
        llmagent: 'http://localhost:8003',
        fileingestor: 'http://localhost:8004',
        ollama: 'http://localhost:11434',
        easyocr: 'http://localhost:8005'
    },
    
    // Status monitoring interval (10 seconds)
    statusUpdateInterval: 10000,
    
    // File upload settings
    maxFileSize: 50 * 1024 * 1024, // 50MB
    
    // Search settings
    maxSearchResults: 100,
    
    // Chat settings
    maxChatHistory: 100
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
} 