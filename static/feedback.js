let conversationHistory = [];
let userExchangeCount = 0; // Counter to track user messages
const MAX_USER_EXCHANGES = 5; // Limit to 5 user messages
let visitId = null; // Store visit ID

function updateConversation(role, message) {
    let chatContainer = document.getElementById('chatContainer');
    let messageDiv = document.createElement('div');
    messageDiv.className = role + '-message';
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendMessage(userMessage = null) {
    let inputMessage = userMessage || document.getElementById('userMessage').value.trim();
    if (!inputMessage || userExchangeCount >= MAX_USER_EXCHANGES) return;

    if (!userMessage) {
        updateConversation('user', inputMessage);
        userExchangeCount++;
    }

    if (userExchangeCount >= MAX_USER_EXCHANGES) {
        updateConversation('system', "Thank you for your feedback. The conversation has ended.");
        document.getElementById('userMessage').disabled = true;
        document.querySelector('.send-button').disabled = true;
        sendConversationHistory();
        return;
    }

    fetch('/send-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: inputMessage,
            exchange_count: userExchangeCount,
            visit_id: visitId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        console.log('Response from bot:', data.response); // Debugging log
        updateConversation('gemini', data.response);
        conversationHistory.push({ 'message': inputMessage, 'role': 'user' });
        conversationHistory.push({ 'message': data.response, 'role': 'assistant' });

        document.getElementById('userMessage').value = '';
    })
    .catch(error => console.error('Error:', error));
}

document.getElementById('feedbackForm').addEventListener('submit', function(event) {
    event.preventDefault();
    visitId = document.getElementById('visitId').value.trim();

    if (!visitId) {
        alert('Please enter a valid Visit ID.');
        return;
    }

    fetch('/start-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ visitId: visitId })  // Use JSON for POST request
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
        } else {
            console.log('Feedback start response:', data); // Debugging log
            document.querySelector('.feedback-container').style.display = 'none';
            document.querySelector('.chat-container').style.display = 'block';
            document.querySelector('.input-section').style.display = 'block';

            // Trigger Ava's initial message
            initializeChat();
        }
    })
    .catch(error => console.error('Error:', error));
});

function initializeChat() {
    console.log('Initializing chat...'); // Debugging log
    sendMessage("Hello! I'm Ava, and I'm here to gather your feedback about your recent experience at Serene hospital. How would you rate your overall experience on a scale of 1 to 10?");
}
