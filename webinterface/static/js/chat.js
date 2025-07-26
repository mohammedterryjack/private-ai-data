// Chat Module for AI Data Platform
class ChatManager {
    constructor(services) {
        this.services = services;
        this.chatHistory = [];
        this.setupChat();
    }
    
    setupChat() {
        const chatForm = document.getElementById('chatForm');
        const chatInput = document.getElementById('chatInput');
        const chatMessages = document.getElementById('chatMessages');
        
        if (!chatForm || !chatInput || !chatMessages) return;
        
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Add send button click handler
        const sendButton = document.getElementById('sendButton');
        if (sendButton) {
            sendButton.addEventListener('click', () => {
                this.sendMessage();
            });
        }
        
        // Add clear chat button handler
        const clearChatButton = document.getElementById('clearChatButton');
        if (clearChatButton) {
            clearChatButton.addEventListener('click', () => {
                this.clearChat();
            });
        }
    }
    
    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const chatMessages = document.getElementById('chatMessages');
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        chatInput.value = '';
        
        // Show typing indicator
        const typingIndicator = this.addTypingIndicator();
        
        try {
            // Prepare sources from current search results
            let sources = [];
            if (window.currentSearchResults && window.currentSearchResults.length > 0) {
                sources = window.currentSearchResults.map(result => {
                    if (result.document_id) {
                        // PDF document
                        const content = result.structured_json || result.content || 'No content available';
                        const formattedContent = typeof content === 'object' ? JSON.stringify(content, null, 2) : content;
                        return `Document ${result.document_id.substring(0, 8)}... (Score: ${typeof result.similarity === 'number' ? result.similarity.toFixed(3) : 'N/A'}): ${formattedContent}`;
                    } else {
                        // Image
                        const caption = result.caption || 'No caption available';
                        const ocrText = result.ocr_text || '';
                        return `Image ${result.id.substring(0, 8)}... (Score: ${typeof result.similarity === 'number' ? result.similarity.toFixed(3) : 'N/A'}): Caption: ${caption}${ocrText ? ` | OCR: ${ocrText}` : ''}`;
                    }
                });
            }
            
            const response = await fetch(`${this.services.llmagent}/rag/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    chat_history: this.chatHistory,
                    sources: sources
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Check if response is streaming (SSE) or regular JSON
            const contentType = response.headers.get('content-type');
            let data = { response: '' }; // Initialize with empty response
            
            if (contentType && contentType.includes('text/event-stream')) {
                // Handle streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let responseText = '';
                
                try {
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const jsonData = JSON.parse(line.slice(6));
                                    // Handle both formats: {"content": "..."} and {"type": "chunk", "content": "..."}
                                    if (jsonData.content) {
                                        responseText += jsonData.content;
                                        // Update typing indicator with partial response
                                        if (typingIndicator) {
                                            typingIndicator.querySelector('.message-content').innerHTML = Utils.formatMessage(responseText);
                                        }
                                    } else if (jsonData.type === 'chunk' && jsonData.content) {
                                        responseText += jsonData.content;
                                        // Update typing indicator with partial response
                                        if (typingIndicator) {
                                            typingIndicator.querySelector('.message-content').innerHTML = Utils.formatMessage(responseText);
                                        }
                                    } else if (jsonData.type === 'complete') {
                                        data = { response: responseText };
                                    }
                                } catch (e) {
                                    console.log('Non-JSON SSE data:', line.slice(6));
                                }
                            }
                        }
                    }
                    
                    // If we didn't get a complete event, use the accumulated text
                    if (!data.response && responseText) {
                        data = { response: responseText };
                    }
                } catch (streamError) {
                    console.error('Streaming error:', streamError);
                    data = { response: 'Streaming failed, but response may be available' };
                }
            } else {
                // Handle regular JSON response
                try {
                    data = await response.json();
                } catch (jsonError) {
                    console.error('JSON parsing error:', jsonError);
                    data = { response: 'Failed to parse response' };
                }
            }
            
            // Remove typing indicator
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Add AI response to chat
            const responseText = data?.response || 'No response received';
            this.addMessage('assistant', responseText);
            
            // Update chat history
            this.chatHistory.push({ role: 'user', content: message });
            this.chatHistory.push({ role: 'assistant', content: responseText });
            
            // Limit chat history
            if (this.chatHistory.length > CONFIG.maxChatHistory) {
                this.chatHistory = this.chatHistory.slice(-CONFIG.maxChatHistory);
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            
            // Remove typing indicator
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Add error message
            this.addMessage('error', `Failed to get response: ${error.message}`);
            Utils.showNotification(`Chat failed: ${error.message}`, 'error');
        }
    }
    
    addMessage(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message message-${role}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-sender">${role === 'user' ? 'You' : role === 'assistant' ? 'AI Assistant' : 'System'}</div>
            <div class="message-content">${Utils.formatMessage(content)}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    addTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return null;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message message-assistant typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-sender">AI Assistant</div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return typingDiv;
    }
    
    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        this.chatHistory = [];
        Utils.showNotification('Chat history cleared', 'info');
    }
    
    // Load chat history from localStorage
    loadChatHistory() {
        try {
            const saved = localStorage.getItem('chatHistory');
            if (saved) {
                this.chatHistory = JSON.parse(saved);
                this.chatHistory.forEach(msg => {
                    this.addMessage(msg.role, msg.content);
                });
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }
    
    // Save chat history to localStorage
    saveChatHistory() {
        try {
            localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory));
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatManager;
} else {
    window.ChatManager = ChatManager;
} 