// Status Module for AI Data Platform
class StatusManager {
    constructor(services) {
        this.services = services;
        this.statusInterval = null;
        this.setupStatusMonitoring();
    }
    
    setupStatusMonitoring() {
        // Initial status check
        this.checkAllServices();
        
        // Set up periodic status checking
        this.statusInterval = setInterval(() => {
            this.checkAllServices();
        }, CONFIG.statusUpdateInterval);
        
        // Add manual refresh button handler
        const refreshButton = document.getElementById('refreshStatusButton');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.checkAllServices();
            });
        }
        
        // Add toggle functionality for status panel
        const toggleButton = document.getElementById('toggleStatusButton');
        const statusContent = document.getElementById('dependencyTree');
        if (toggleButton && statusContent) {
            toggleButton.addEventListener('click', () => {
                const isCollapsed = statusContent.style.display === 'none';
                statusContent.style.display = isCollapsed ? 'block' : 'none';
                
                // Update button icon
                const svg = toggleButton.querySelector('svg');
                if (svg) {
                    svg.innerHTML = isCollapsed ? 
                        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>' :
                        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>';
                }
                
                // Update button title
                toggleButton.title = isCollapsed ? 'Collapse status panel' : 'Expand status panel';
            });
        }
    }
    
    async checkAllServices() {
        const services = [
            { name: 'Web Interface', url: window.location.origin, icon: '🌐' },
            { name: 'Knowledge Base', url: this.services.knowledgebase, icon: '🗄️' },
            { name: 'Search Engine', url: this.services.searchengine, icon: '🔍' },
            { name: 'LLM Agent', url: this.services.llmagent, icon: '🧠' },
            { name: 'File Ingestor', url: this.services.fileingestor, icon: '📁' },
            { name: 'Ollama', url: this.services.ollama, icon: '🦙' },
            { name: 'EasyOCR', url: this.services.easyocr, icon: '👁️' },
            { name: 'PostgreSQL', url: 'http://localhost:5432', icon: '🐘' }
        ];
        
        const statusPromises = services.map(service => this.checkService(service));
        const results = await Promise.allSettled(statusPromises);
        
        this.updateDependencyTree(services, results);
    }
    
    async checkService(service) {
        try {
            // Special handling for different services
            let healthUrl = `${service.url}/health/`;
            
            if (service.name === 'Ollama') {
                healthUrl = `${service.url}/api/tags`; // Ollama uses /api/tags as health check
            } else if (service.name === 'PostgreSQL') {
                // PostgreSQL doesn't have a health endpoint, so we'll check if the port is accessible
                // We'll use a simple TCP connection check via a HEAD request to the knowledgebase
                // since it depends on PostgreSQL and will fail if PostgreSQL is down
                try {
                    const response = await fetch(`${this.services.knowledgebase}/health/`, {
                        method: 'GET',
                        timeout: 3000
                    });
                    
                    if (response.ok) {
                        return {
                            name: service.name,
                            icon: service.icon,
                            status: 'healthy',
                            details: 'connected',
                            responseTime: Date.now()
                        };
                    } else {
                        return {
                            name: service.name,
                            icon: service.icon,
                            status: 'error',
                            details: 'database error',
                            responseTime: Date.now()
                        };
                    }
                } catch (dbError) {
                    return {
                        name: service.name,
                        icon: service.icon,
                        status: 'error',
                        details: 'connection failed',
                        responseTime: Date.now()
                    };
                }
            }
            
            const response = await fetch(healthUrl, {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                let data;
                try {
                    data = await response.json();
                } catch (e) {
                    // Some services return plain text instead of JSON
                    data = { status: 'OK' };
                }
                
                return {
                    name: service.name,
                    icon: service.icon,
                    status: 'healthy',
                    details: data.status || 'healthy',
                    responseTime: Date.now()
                };
            } else {
                // For Ollama, try alternative endpoint if first one fails
                if (service.name === 'Ollama' && response.status === 404) {
                    try {
                        const altResponse = await fetch(`${service.url}/api/version`, {
                            method: 'GET',
                            timeout: 3000
                        });
                        
                        if (altResponse.ok) {
                            return {
                                name: service.name,
                                icon: service.icon,
                                status: 'healthy',
                                details: 'healthy',
                                responseTime: Date.now()
                            };
                        }
                    } catch (altError) {
                        console.log('Ollama alternative endpoint also failed:', altError);
                    }
                }
                
                return {
                    name: service.name,
                    icon: service.icon,
                    status: 'error',
                    details: `HTTP ${response.status}`,
                    responseTime: Date.now()
                };
            }
        } catch (error) {
            return {
                name: service.name,
                icon: service.icon,
                status: 'error',
                details: error.message || 'Connection failed',
                responseTime: Date.now()
            };
        }
    }
    
    updateDependencyTree(services, results) {
        const treeContainer = document.getElementById('dependencyTree');
        if (!treeContainer) return;
        
        // Create a map of service statuses
        const serviceStatusMap = new Map();
        services.forEach((service, index) => {
            const result = results[index];
            const statusData = result.status === 'fulfilled' ? result.value : {
                name: service.name,
                icon: service.icon,
                status: 'error',
                details: 'Check failed',
                responseTime: Date.now()
            };
            serviceStatusMap.set(service.name, statusData);
        });
        
        // Define the hierarchy structure
        const hierarchy = {
            name: 'Web Interface',
            icon: '🌐',
            children: [
                {
                    name: 'File Ingestor',
                    icon: '📁',
                    children: [
                        {
                            name: 'EasyOCR',
                            icon: '👁️',
                            children: []
                        },
                        {
                            name: 'LLM Agent',
                            icon: '🧠',
                            children: [
                                {
                                    name: 'Ollama',
                                    icon: '🦙',
                                    children: []
                                }
                            ]
                        }
                    ]
                },
                {
                    name: 'Search Engine',
                    icon: '🔍',
                    children: [
                        {
                            name: 'Knowledge Base',
                            icon: '🗄️',
                            children: [
                                {
                                    name: 'PostgreSQL',
                                    icon: '🐘',
                                    children: []
                                }
                            ]
                        }
                    ]
                }
            ]
        };
        
        const treeHtml = this.renderTree(hierarchy, serviceStatusMap, 0);
        treeContainer.innerHTML = `
            <div class="dependency-tree">
                <h3>Service Dependencies</h3>
                ${treeHtml}
            </div>
        `;
        
        // Add status styles if not already present
        this.addStatusStyles();
    }
    
    renderTree(node, serviceStatusMap, level) {
        const status = serviceStatusMap.get(node.name);
        const statusClass = status && status.status === 'healthy' ? 'status-healthy' : 'status-error';
        const indent = level * 20;
        
        let html = `
            <div class="tree-node" style="margin-left: ${indent}px;">
                <div class="tree-item ${statusClass}">
                    <div class="tree-icon">${node.icon}</div>
                    <div class="tree-info">
                        <div class="tree-name">${node.name}</div>
                        ${status ? `<div class="tree-status">${status.details}</div>` : ''}
                    </div>
                    ${status ? `<div class="tree-indicator"><span class="status-dot ${statusClass}"></span></div>` : ''}
                </div>
        `;
        
        if (node.children && node.children.length > 0) {
            html += '<div class="tree-children">';
            node.children.forEach(child => {
                html += this.renderTree(child, serviceStatusMap, level + 1);
            });
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }
    
    addStatusStyles() {
        if (!document.getElementById('status-styles')) {
            const styles = document.createElement('style');
            styles.id = 'status-styles';
            styles.textContent = `
                /* Status Panel Layout */
                .grid {
                    display: grid;
                    grid-template-columns: 1fr auto 1fr;
                    gap: 20px;
                    align-items: start;
                }
                
                .status-section {
                    min-width: 280px;
                    max-width: 320px;
                }
                
                .status-card {
                    position: sticky;
                    top: 20px;
                }
                
                .status-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                }
                
                .status-header .card-title {
                    margin: 0;
                    font-size: 16px;
                }
                
                .status-header .card-subtitle {
                    margin: 0;
                    font-size: 12px;
                    color: #6b7280;
                }
                
                .toggle-button {
                    padding: 4px;
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    background: white;
                    color: #6b7280;
                    cursor: pointer;
                    transition: all 0.2s;
                    flex-shrink: 0;
                }
                
                .toggle-button:hover {
                    background: #f9fafb;
                    border-color: #d1d5db;
                    color: #374151;
                }
                
                .status-content {
                    padding: 0;
                    transition: all 0.3s ease;
                }
                
                /* Dependency Tree Styles */
                .dependency-tree {
                    padding: 12px 0;
                }
                
                .dependency-tree h3 {
                    margin: 0 0 12px 0;
                    font-size: 14px;
                    font-weight: 600;
                    color: #1e293b;
                }
                
                .tree-node {
                    margin-bottom: 6px;
                }
                
                .tree-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 4px 8px;
                    border-radius: 4px;
                    border: 1px solid #e5e7eb;
                    background: white;
                    transition: all 0.2s;
                    font-size: 12px;
                    position: relative;
                }
                
                .tree-item:hover {
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }
                
                .tree-item::before {
                    content: '';
                    position: absolute;
                    left: -8px;
                    top: 50%;
                    width: 8px;
                    height: 1px;
                    background: #d1d5db;
                }
                
                .tree-node:first-child .tree-item::before {
                    display: none;
                }
                
                .tree-children {
                    position: relative;
                }
                
                .tree-children::before {
                    content: '';
                    position: absolute;
                    left: 8px;
                    top: 0;
                    bottom: 0;
                    width: 1px;
                    background: #d1d5db;
                }
                
                .tree-icon {
                    font-size: 16px;
                    width: 24px;
                    text-align: center;
                }
                
                .tree-info {
                    flex: 1;
                    min-width: 0;
                }
                
                .tree-name {
                    font-weight: 500;
                    color: #374151;
                    margin-bottom: 1px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                
                .tree-status {
                    font-size: 9px;
                    color: #6b7280;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                
                .tree-indicator {
                    display: flex;
                    align-items: center;
                    flex-shrink: 0;
                }
                
                .status-dot {
                    width: 5px;
                    height: 5px;
                    border-radius: 50%;
                }
                
                .status-dot.status-healthy {
                    background: #10b981;
                }
                
                .status-dot.status-error {
                    background: #ef4444;
                }
                
                .tree-item.status-healthy {
                    border-color: #d1fae5;
                    background: #f0fdf4;
                }
                
                .tree-item.status-error {
                    border-color: #fecaca;
                    background: #fef2f2;
                }
                
                /* Responsive adjustments */
                @media (max-width: 1200px) {
                    .grid {
                        grid-template-columns: 1fr;
                        gap: 16px;
                    }
                    
                    .status-section {
                        min-width: auto;
                        max-width: none;
                    }
                    
                    .status-card {
                        position: static;
                    }
                }
                
                /* Button styles for search and clear */
                .search-input-container {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .upload-trigger {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 8px;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    background: white;
                    color: #374151;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .upload-trigger:hover {
                    background: #f9fafb;
                    border-color: #9ca3af;
                }
                
                .clear-chat-button {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 6px;
                    font-size: 12px;
                    font-weight: 500;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    color: #64748b;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                    width: 32px;
                    height: 32px;
                }
                
                .clear-chat-button:hover {
                    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
                    border-color: #fecaca;
                    color: #dc2626;
                    box-shadow: 0 2px 4px rgba(220, 38, 38, 0.1);
                    transform: translateY(-1px);
                }
                
                .clear-chat-button:active {
                    transform: translateY(0);
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                }
            `;
            document.head.appendChild(styles);
        }
    }
    
    // Clean up interval when needed
    destroy() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StatusManager;
} else {
    window.StatusManager = StatusManager;
} 