document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages-container');
    const newChatBtn = document.getElementById('new-chat-btn');
    const settingsModal = document.getElementById('settings-modal');
    const settingsToggle = document.getElementById('settings-toggle');
    const closeModal = document.querySelector('.close');
    const saveSettingsBtn = document.getElementById('save-settings');
    const modelSelect = document.getElementById('model-select');
    const temperatureSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');
    const maxTokensInput = document.getElementById('max-tokens');
    const currentModel = document.getElementById('current-model');
    
    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Update temperature value display
    temperatureSlider.addEventListener('input', function() {
        tempValue.textContent = this.value;
    });
    
    // Send message on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send message on Enter key (but allow Shift+Enter for new line)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // New chat button
    newChatBtn.addEventListener('click', startNewChat);
    
    // Settings modal
    settingsToggle.addEventListener('click', function() {
        settingsModal.style.display = 'block';
    });
    
    closeModal.addEventListener('click', function() {
        settingsModal.style.display = 'none';
    });
    
    window.addEventListener('click', function(e) {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });
    
    // Save settings
    saveSettingsBtn.addEventListener('click', saveSettings);
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input and reset height
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Disable input and button while processing
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to server
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            if (data.error) {
                addMessageToChat('error', `Error: ${data.error}`);
            } else {
                addMessageToChat('assistant', data.response);
            }
            
            // Re-enable input and button
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        })
        .catch(error => {
            removeTypingIndicator();
            addMessageToChat('error', `Error: ${error.message}`);
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        });
    }
    
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar ' + (role === 'user' ? 'user-avatar' : role === 'assistant' ? 'ai-avatar' : '');
        
        if (role === 'user') {
            avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
        } else if (role === 'assistant') {
            avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
        } else if (role === 'error') {
            avatarDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            avatarDiv.style.backgroundColor = '#ef4444';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        // Remove welcome message if it exists
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
    }
    
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message';
        typingDiv.id = 'typing-indicator';
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar ai-avatar';
        avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content typing-indicator';
        contentDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        typingDiv.appendChild(avatarDiv);
        typingDiv.appendChild(contentDiv);
        
        messagesContainer.appendChild(typingDiv);
        scrollToBottom();
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function startNewChat() {
        fetch('/new_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Clear chat messages
                messagesContainer.innerHTML = `
                    <div class="welcome-message">
                        <h2>Welcome to ACE AI</h2>
                        <p>I'm your helpful AI assistant. How can I help you today?</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error starting new chat:', error);
        });
    }
    
    function saveSettings() {
        const settings = {
            model: modelSelect.value,
            temperature: parseFloat(temperatureSlider.value),
            num_predict: parseInt(maxTokensInput.value)
        };
        
        fetch('/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Update current model display
                currentModel.textContent = settings.model;
                
                // Close modal
                settingsModal.style.display = 'none';
                
                // Show success message
                alert('Settings saved successfully!');
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            alert('Error saving settings. Please try again.');
        });
    }
    
    // Initialize the app
    messageInput.focus();
});