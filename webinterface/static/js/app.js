// Main Application for AI Data Platform
// This file orchestrates all the modular components

class AIDataPlatform {
    constructor() {
        this.services = CONFIG.services;
        this.managers = {};
        this.init();
    }
    
    init() {
        // Add notification styles
        Utils.addNotificationStyles();
        
        console.log('Initializing AI Data Platform with services:', this.services);
        
        // Initialize all managers
        try {
            this.managers.fileUpload = new FileUploadManager(this.services);
            console.log('✓ FileUploadManager initialized');
        } catch (error) {
            console.error('✗ FileUploadManager failed:', error);
        }
        
        try {
            this.managers.search = new SearchManager(this.services);
            console.log('✓ SearchManager initialized');
        } catch (error) {
            console.error('✗ SearchManager failed:', error);
        }
        
        try {
            this.managers.chat = new ChatManager(this.services);
            console.log('✓ ChatManager initialized');
        } catch (error) {
            console.error('✗ ChatManager failed:', error);
        }
        
        try {
            this.managers.status = new StatusManager(this.services);
            console.log('✓ StatusManager initialized');
        } catch (error) {
            console.error('✗ StatusManager failed:', error);
        }
        
        // Setup tab navigation
        this.setupTabNavigation();
        
        // Setup upload trigger
        this.setupUploadTrigger();
        
        // Load chat history
        if (this.managers.chat) {
            this.managers.chat.loadChatHistory();
        }
        
        // Show welcome message
        Utils.showNotification('AI Data Platform loaded successfully!', 'success');
        
        console.log('AI Data Platform initialized with modules:', Object.keys(this.managers));
    }
    
    setupTabNavigation() {
        const tabs = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');
                
                // Update active tab button
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Update active tab content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === targetTab) {
                        content.classList.add('active');
                    }
                });
            });
        });
    }
    
    setupUploadTrigger() {
        const uploadTrigger = document.getElementById('uploadTrigger');
        if (uploadTrigger) {
            uploadTrigger.addEventListener('click', () => {
                this.managers.fileUpload.showUploadOverlay();
            });
        }
    }
    
    // Cleanup method
    destroy() {
        if (this.managers.status) {
            this.managers.status.destroy();
        }
        if (this.managers.chat) {
            this.managers.chat.saveChatHistory();
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AIDataPlatform();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.app) {
        window.app.destroy();
    }
});