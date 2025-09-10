document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages-container');
    const newChatBtn = document.getElementById('new-chat-btn');
    const settingsModal = document.getElementById('settings-modal');
    const settingsToggle = document.getElementById('settings-toggle');
    const closeModal = document.querySelector('.close');
    const saveSettingsBtn = document.getElementById('save-settings');
    const cancelSettingsBtn = document.getElementById('cancel-settings');
    const modelSelect = document.getElementById('model-select');
    const temperatureSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');
    const maxTokensInput = document.getElementById('max-tokens');
    const currentModel = document.getElementById('current-model');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const toast = document.getElementById('toast');
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    
    // State
    let isWaitingForResponse = false;
    
    // Initialize the app
    function init() {
        loadSettings();
        setupEventListeners();
        messageInput.focus();
        
        // Add animation to welcome message
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.opacity = '0';
            welcomeMessage.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                welcomeMessage.style.transition = 'all 0.5s ease';
                welcomeMessage.style.opacity = '1';
                welcomeMessage.style.transform = 'translateY(0)';
            }, 300);
        }
    }
    
    // Load saved settings
    function loadSettings() {
        // In a real app, you would load these from a server or localStorage
        const savedSettings = JSON.parse(localStorage.getItem('ace-ai-settings')) || {};
        
        if (savedSettings.model) {
            modelSelect.value = savedSettings.model;
            currentModel.textContent = savedSettings.model;
        }
        
        if (savedSettings.temperature) {
            temperatureSlider.value = savedSettings.temperature;
            tempValue.textContent = savedSettings.temperature;
        }
        
        if (savedSettings.num_predict) {
            maxTokensInput.value = savedSettings.num_predict;
        }
    }
    
    // Save settings to localStorage
    function saveSettingsToStorage(settings) {
        localStorage.setItem('ace-ai-settings', JSON.stringify(settings));
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // Send message on button click
        sendButton.addEventListener('click', sendMessage);
        
        // Send message on Enter key (but allow Shift+Enter for new line)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Update temperature value display
        temperatureSlider.addEventListener('input', function() {
            tempValue.textContent = this.value;
        });
        
        // New chat button
        newChatBtn.addEventListener('click', startNewChat);
        
        // Clear chat button
        clearChatBtn.addEventListener('click', clearChat);
        
        // Settings modal
        settingsToggle.addEventListener('click', openSettings);
        closeModal.addEventListener('click', closeSettings);
        cancelSettingsBtn.addEventListener('click', closeSettings);
        
        // Save settings
        saveSettingsBtn.addEventListener('click', saveSettings);
        
        // Close modal when clicking outside
        window.addEventListener('click', function(e) {
            if (e.target === settingsModal) {
                closeSettings();
            }
        });
        
        // Sidebar toggle for mobile
        sidebarToggle.addEventListener('click', toggleSidebar);
        
        // Suggestion chips
        suggestionChips.forEach(chip => {
            chip.addEventListener('click', () => {
                messageInput.value = chip.textContent;
                messageInput.focus();
                messageInput.dispatchEvent(new Event('input', { bubbles: true }));
            });
        });
    }
    // Add this to your setupEventListeners function
document.getElementById('mic-btn').addEventListener('click', toggleVoiceInput);

// Add this function to handle voice input
function toggleVoiceInput() {
    const micBtn = document.getElementById('mic-btn');
    const messageInput = document.getElementById('message-input');
    
    if (micBtn.classList.contains('listening')) {
        // Stop listening
        micBtn.classList.remove('listening');
        micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        // Add your stop listening logic here
    } else {
        // Start listening
        micBtn.classList.add('listening');
        micBtn.innerHTML = '<i class="fas fa-circle"></i>';
        
        // Call the backend /listen endpoint
        fetch('/listen', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            if (data.text) {
                messageInput.value = data.text;
                messageInput.focus();
                messageInput.dispatchEvent(new Event('input', { bubbles: true }));
            } else if (data.error) {
                showToast(data.error, 'error');
            }
            
            // Reset mic button
            micBtn.classList.remove('listening');
            micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        })
        .catch(error => {
            console.error('Voice recognition error:', error);
            showToast('Voice recognition failed', 'error');
            micBtn.classList.remove('listening');
            micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        });
    }
}
    
    // Toggle sidebar visibility on mobile
    function toggleSidebar() {
        sidebar.classList.toggle('active');
    }
    
    // Send message to the server
    // Send message to the server (with streaming support)
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isWaitingForResponse) return;

    // Add user message to chat
    addMessageToChat('user', message);

    // Clear input and reset height
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Disable input and button while processing
    setInputState(false);

    // Show typing indicator
    showTypingIndicator();

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    }).then(response => {
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aiMessage = '';

        // Create assistant message container
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar ai-avatar';
        avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        // Remove typing indicator and add assistant message box
        removeTypingIndicator();
        messagesContainer.appendChild(messageDiv);
        scrollToBottom();

        // Stream tokens
        function processStream({ done, value }) {
            if (done) {
                setInputState(true);
                return;
            }

            const chunk = decoder.decode(value, { stream: true });
            aiMessage += chunk;
            contentDiv.innerHTML = formatMessage(aiMessage); // live typing effect
            scrollToBottom();

            return reader.read().then(processStream);
        }

        return reader.read().then(processStream);
    }).catch(error => {
        removeTypingIndicator();
        addMessageToChat('error', `Error: ${error.message}`);
        setInputState(true);
    });
}

    
    // Enable or disable the input fields
    function setInputState(enabled) {
        messageInput.disabled = !enabled;
        sendButton.disabled = !enabled;
        isWaitingForResponse = !enabled;
        
        if (enabled) {
            messageInput.focus();
        }
    }
    
    // Add a message to the chat UI
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar ' + 
            (role === 'user' ? 'user-avatar' : 
             role === 'assistant' ? 'ai-avatar' : 
             'error-avatar');
        
        if (role === 'user') {
            avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
        } else if (role === 'assistant') {
            avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
        } else if (role === 'error') {
            avatarDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Simple markdown parsing
        contentDiv.innerHTML = formatMessage(content);
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        // Remove welcome message if it exists
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
        
        // Add animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
    }
    
    // Simple markdown formatting
    function formatMessage(content) {
        // Convert **bold** to <strong>bold</strong>
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em>italic</em>
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert `code` to <code>code</code>
        content = content.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Convert ```code blocks``` to <pre><code>code blocks</code></pre>
        content = content.replace(/```([^`]*)```/g, '<pre><code>$1</code></pre>');
        
        // Convert URLs to links
        content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    // Show typing indicator
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
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Scroll to the bottom of the messages container
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Start a new chat
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
                        <div class="welcome-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <h2>Welcome to ACE AI</h2>
                        <p>I'm your helpful AI assistant. How can I help you today?</p>
                        <div class="suggestions">
                            <div class="suggestion-chip">Tell me about yourself</div>
                            <div class="suggestion-chip">What can you help me with?</div>
                            <div class="suggestion-chip">Explain AI in simple terms</div>
                        </div>
                    </div>
                `;
                
                // Re-add event listeners to suggestion chips
                document.querySelectorAll('.suggestion-chip').forEach(chip => {
                    chip.addEventListener('click', () => {
                        messageInput.value = chip.textContent;
                        messageInput.focus();
                        messageInput.dispatchEvent(new Event('input', { bubbles: true }));
                    });
                });
                
                showToast('New conversation started');
            }
        })
        .catch(error => {
            console.error('Error starting new chat:', error);
            showToast('Error starting new chat', 'error');
        });
    }
    
    // Clear the current chat
    function clearChat() {
        messagesContainer.innerHTML = '';
        showToast('Chat cleared');
    }
    
    // Open settings modal
    function openSettings() {
        settingsModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    // Close settings modal
    function closeSettings() {
        settingsModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
    
    // Save settings
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
                
                // Save to localStorage
                saveSettingsToStorage(settings);
                
                // Close modal
                closeSettings();
                
                // Show success message
                showToast('Settings saved successfully');
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            showToast('Error saving settings', 'error');
        });
    }
    
    // Show toast notification
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMessage = toast.querySelector('.toast-message');
        const toastIcon = toast.querySelector('i');
        
        toastMessage.textContent = message;
        
        if (type === 'error') {
            toastIcon.className = 'fas fa-exclamation-circle';
            toastIcon.style.color = '#ef4444';
        } else {
            toastIcon.className = 'fas fa-check-circle';
            toastIcon.style.color = '#10a37f';
        }
        
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    // Initialize the app
    init();
});