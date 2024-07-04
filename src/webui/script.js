document.addEventListener('DOMContentLoaded', () => {
    const settingsButton = document.getElementById('settingsButton');
    const settingsPopup = document.getElementById('settingsPopup');
    const closeSettings = document.getElementById('closeSettings');
    const themeSelect = document.getElementById('themeSelect');
    const messageInput = document.getElementById('messageInput');
    const fileInput = document.getElementById('fileInput');
    const sendButton = document.getElementById('sendButton');
    const mainContent = document.querySelector('main');

    let selectedFile = null;

    // Function to open the settings popup
    function openSettings() {
        settingsPopup.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    // Function to close the settings popup
    function closeSettingsPopup() {
        settingsPopup.classList.add('hidden');
        document.body.style.overflow = '';
    }

    // Function to update image sources based on theme
    function updateImageSources(isDark) {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            const src = img.src;
            const filename = src.split('/').pop();
            const [name, ext] = filename.split('.');
            if (isDark) {
                if (!name.endsWith('_inverted')) {
                    img.src = `icon/${name}_inverted.${ext}`;
                }
            } else {
                img.src = `icon/${name.replace('_inverted', '')}.${ext}`;
            }
        });
    }

    // Event listener for opening the settings
    settingsButton.addEventListener('click', openSettings);

    // Event listener for closing the settings
    closeSettings.addEventListener('click', closeSettingsPopup);

    // Event listener for changing the theme
    themeSelect.addEventListener('change', (e) => {
        const isDark = e.target.value === 'dark';
        if (isDark) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        updateImageSources(isDark);
    });

    // Close the popup when clicking outside of it
    settingsPopup.addEventListener('click', (e) => {
        if (e.target === settingsPopup) {
            closeSettingsPopup();
        }
    });

    // Set initial theme based on user preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.classList.add('dark');
        themeSelect.value = 'dark';
        updateImageSources(true);
    }

    // Function to add a message to the chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user-message' : 'bot-message');

        const messagePara = document.createElement('p');
        messagePara.textContent = content;

        const avatar = document.createElement('img');
        avatar.classList.add('avatar');
        avatar.src = isUser ? 'icon/user.png' : 'icon/ico.png';
        avatar.alt = isUser ? 'user' : 'bot';
        avatar.setAttribute('aria-hidden', 'true');

        if (isUser) {
            messageDiv.appendChild(messagePara);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messagePara);
        }

        mainContent.appendChild(messageDiv);
        mainContent.scrollTop = mainContent.scrollHeight;

        // Update the newly added image source if in dark mode
        if (document.documentElement.classList.contains('dark')) {
            updateImageSources(true);
        }
    }

    // Function to clear chat history
    function clearChatHistory() {
        mainContent.innerHTML = '';
        addMessage("Chat history cleared.", false);
    }

    // Function to clear inputs
    function clearInputs() {
        messageInput.value = '';
        fileInput.value = '';
        selectedFile = null;
        messageInput.placeholder = "Type a message...";
    }

    // Function to handle sending a message and file
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message || selectedFile) {
            let content = message;
            if (selectedFile) {
                content += (content ? ' ' : '') + `[File attached: ${selectedFile.name}]`;
            }

            if (content.toLowerCase() === 'clear') {
                clearChatHistory();
            } else {
                addMessage(content, true);

                // Mirror the user's input as a reply
                setTimeout(() => {
                    addMessage(`You said: "${content}"`, false);
                }, 500);
            }

            // Clear inputs after sending
            clearInputs();
        }
    }

    // Function to handle file selection
    function handleFileSelect(e) {
        selectedFile = e.target.files[0];
        if (selectedFile) {
            messageInput.placeholder = `File selected: ${selectedFile.name}. Type your message...`;
        } else {
            messageInput.placeholder = "Type a message...";
        }
    }

    // Event listener for sending messages
    sendButton.addEventListener('click', sendMessage);

    // Event listener for pressing Enter to send message
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Event listener for file input
    fileInput.addEventListener('change', handleFileSelect);
});
