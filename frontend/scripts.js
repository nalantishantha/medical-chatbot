// DOM Elements
const chatBox = document.getElementById('chatBox');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const chatForm = document.getElementById('chatForm');
const loading = document.getElementById('loading');
const suggestionButtons = document.querySelectorAll('.suggestion-btn');

// Initialize welcome time
document.getElementById('welcomeTime').textContent = getCurrentTime();

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    
    // Enable/disable send button based on input
    sendButton.disabled = this.value.trim() === '';
});

// Handle form submission
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input and reset height
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendButton.disabled = true;
    
    // Show loading indicator
    loading.classList.add('active');
    
    // Send message to backend
    try {
        const response = await sendMessageToBackend(message);
        
        // Hide loading indicator
        loading.classList.remove('active');
        
        // Add bot response to chat
        addMessage(response, 'bot');
    } catch (error) {
        console.error('Error:', error);
        loading.classList.remove('active');
        addMessage('Sorry, I encountered an error. Please try again.', 'bot', true);
    }
});

// Handle suggestion button clicks
suggestionButtons.forEach(button => {
    button.addEventListener('click', function() {
        messageInput.value = this.textContent;
        messageInput.focus();
        messageInput.dispatchEvent(new Event('input'));
    });
});

// Handle Enter key (without Shift) to send message
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (this.value.trim() !== '') {
            chatForm.dispatchEvent(new Event('submit'));
        }
    }
});

// Function to add message to chat
function addMessage(text, sender, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = sender === 'user' 
        ? '<i class="fas fa-user"></i>' 
        : '<i class="fas fa-user-md"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    
    if (isError) {
        textDiv.innerHTML = `<p style="color: #ef4444;">${text}</p>`;
    } else {
        // Format the message text (support for basic formatting)
        const formattedText = formatMessage(text);
        textDiv.innerHTML = formattedText;
    }
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();
    
    contentDiv.appendChild(textDiv);
    contentDiv.appendChild(timeDiv);
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatBox.appendChild(messageDiv);
    
    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Function to send message to backend
async function sendMessageToBackend(message) {
    const formData = new FormData();
    formData.append('msg', message);
    
    const response = await fetch('/get', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    
    const data = await response.text();
    return data;
}

// Function to get current time
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
}

// Function to format message text
function formatMessage(text) {
    // Convert newlines to <br>
    text = text.replace(/\n/g, '<br>');
    
    // Split into paragraphs (double line breaks)
    const paragraphs = text.split('<br><br>');
    
    // Wrap each paragraph in <p> tags
    const formatted = paragraphs.map(para => {
        if (para.trim()) {
            return `<p>${para}</p>`;
        }
        return '';
    }).join('');
    
    return formatted || `<p>${text}</p>`;
}

// Add smooth scroll behavior
chatBox.style.scrollBehavior = 'smooth';

// Focus on input when page loads
window.addEventListener('load', () => {
    messageInput.focus();
});
