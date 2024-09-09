// //handle sending messages
// async function handleSendMessage() {
//     const messageInput = document.getElementById('messageInput');
//     const userMessage = messageInput.value.trim();

//     if (userMessage === '') return; // If input is empty, do nothing

//     // Display user message
//     displayMessage(userMessage, 'user-message');

//     // Clear input field
//     messageInput.value = '';

//     // Call the Gemini API and get the response
//     const geminiResponse = await sendMessageToGemini(userMessage);

//     // Display Gemini's response
//     displayMessage(geminiResponse, 'gemini-message');
// }

// //send button click
// document.getElementById('sendButton').addEventListener('click', async () => {
//     await handleSendMessage();
// });

// //Enter key press
// document.getElementById('messageInput').addEventListener('keydown', async (event) => {
//     if (event.key === 'Enter') {
//         event.preventDefault(); // Prevent the default behavior of the Enter key
//         await handleSendMessage();
//     }
// });

// //display messages
// function displayMessage(message, className) {
//     const chatContainer = document.getElementById('chatContainer');
//     const messageElement = document.createElement('div');
//     messageElement.classList.add(className);
//     messageElement.textContent = message;
//     chatContainer.appendChild(messageElement);
//     chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to the bottom
// }

// //call the Gemini API and get a response
// async function sendMessageToGemini(userMessage) {
//     try {
//         const response = await fetch('/send-chat', { // Ensure this matches your Flask endpoint
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({ message: userMessage })
//         });

//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }

//         const data = await response.json();
//         return data.response || "Sorry, I didn't get a response from the server.";
//     } catch (error) {
//         console.error('Error fetching Gemini response:', error);
//         return "I'm sorry, I couldn't process that message right now.";
//     }
// }

// Function to handle sending messages
// async function handleSendMessage() {
//     const messageInput = document.getElementById('messageInput');
//     const userMessage = messageInput.value.trim();

//     if (userMessage === '') return; // If input is empty, do nothing

//     // Display user message
//     displayMessage(userMessage, 'user-message');

//     // Clear input field
//     messageInput.value = '';

//     // Call the Gemini API and get the response
//     const geminiResponse = await sendMessageToGemini(userMessage);

//     // Display Gemini's response
//     displayMessage(geminiResponse, 'gemini-message');
// }

// // Function to display messages
// function displayMessage(message, className) {
//     const chatContainer = document.getElementById('chatContainer');
//     const messageElement = document.createElement('div');
//     messageElement.classList.add(className);
//     messageElement.textContent = message;
//     chatContainer.appendChild(messageElement);
//     chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to the bottom
// }

// // Function to call the Gemini API and get a response
// async function sendMessageToGemini(userMessage) {
//     try {
//         const response = await fetch('/send-chat', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({ message: userMessage })
//         });

//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }

//         const data = await response.json();
//         return data.response || "Sorry, I didn't get a response from the server.";
//     } catch (error) {
//         console.error('Error fetching Gemini response:', error);
//         return "I'm sorry, I couldn't process that message right now.";
//     }
// }

// // Function to fetch and display the initial message
// async function displayInitialMessage() {
//     try {
//         const response = await fetch('/initial-message');
//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }

//         const data = await response.json();
//         displayMessage(data.response, 'gemini-message');
//     } catch (error) {
//         console.error('Error fetching initial message:', error);
//     }
// }

// // Fetch the initial message when the page loads
// window.addEventListener('DOMContentLoaded', (event) => {
//     displayInitialMessage();
// });

// // Send button click
// document.getElementById('sendButton').addEventListener('click', async () => {
//     await handleSendMessage();
// });

// // Enter key press
// document.getElementById('messageInput').addEventListener('keydown', async (event) => {
//     if (event.key === 'Enter') {
//         event.preventDefault(); // Prevent the default behavior of the Enter key
//         await handleSendMessage();
//     }
// });

// Function to handle sending messages
async function handleSendMessage() {
    const messageInput = document.getElementById('messageInput');
    const userMessage = messageInput.value.trim();

    if (userMessage === '') return; // If input is empty, do nothing

    // Display user message
    displayMessage(userMessage, 'user-message');

    // Clear input field
    messageInput.value = '';

    // Call the Gemini API and get the response
    const geminiResponse = await sendMessageToGemini(userMessage);

    // Display Gemini's response
    displayMessage(geminiResponse, 'gemini-message');
}

// Function to display messages
function displayMessage(message, className) {
    const chatContainer = document.getElementById('chatContainer');
    const messageElement = document.createElement('div');
    messageElement.classList.add(className);
    messageElement.textContent = message;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to the bottom
}

// Function to call the Gemini API and get a response
async function sendMessageToGemini(userMessage) {
    try {
        const response = await fetch('/send-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response || "Sorry, I didn't get a response from the server.";
    } catch (error) {
        console.error('Error fetching Gemini response:', error);
        return "I'm sorry, I couldn't process that message right now.";
    }
}

// Function to fetch and display the initial message
async function displayInitialMessage() {
    try {
        const response = await fetch('/initial-message');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayMessage(data.response, 'gemini-message');
    } catch (error) {
        console.error('Error fetching initial message:', error);
    }
}

// Fetch the initial message when the page loads
window.addEventListener('DOMContentLoaded', (event) => {
    displayInitialMessage();
});

// Send button click
document.getElementById('sendButton').addEventListener('click', async () => {
    await handleSendMessage();
});

// Enter key press
document.getElementById('messageInput').addEventListener('keydown', async (event) => {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent the default behavior of the Enter key
        await handleSendMessage();
    }
});
