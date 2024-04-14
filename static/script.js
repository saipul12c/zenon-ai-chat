$(document).ready(function() {
    $('#user-input').on('keydown', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });

    async function sendQuestion() {
        const userInput = $('#user-input').val().trim();
        if (userInput !== '') {
            showLoading(true);
            try {
                const response = await $.ajax({
                    url: '/ask',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ user_input: userInput })
                });
                displayMessage(userInput, 'user-question');
                displayMessage(response.response, 'ai-response');
                appendFeedbackForm(userInput);
                scrollChatToBottom();
            } catch (error) {
                handleServerError(error);
            } finally {
                showLoading(false);
                $('#user-input').val('');
            }
        }
    }

    function appendFeedbackForm(question) {
        const feedbackFormHtml = `
            <div class="feedback-form">
                <input type="text" placeholder="Feedback Anda" class="feedback-input" />
                <button onclick="sendFeedback('${escapeHtml(question)}', this)">Kirim Feedback</button>
            </div>`;
        $('#chat-output').append(feedbackFormHtml);
    }

    async function sendFeedback(question, buttonElement) {
        const feedbackInput = $(buttonElement).prev('.feedback-input');
        const feedbackForm = $(buttonElement).parent('.feedback-form');
        const userFeedback = feedbackInput.val().trim();
        if (userFeedback) {
            try {
                const response = await $.ajax({
                    url: '/feedback',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ question: question, feedback: userFeedback })
                });
                alert('Feedback terkirim: ' + response.message);
                feedbackForm.remove(); // Menghilangkan form feedback
            } catch (error) {
                showError('Gagal mengirim feedback: ' + error.statusText);
            }
        } else {
            alert('Silakan masukkan feedback sebelum mengirim.');
        }
    }

    function handleServerError(error) {
        const errorMessage = error.responseJSON && error.responseJSON.error ? error.responseJSON.error : error.statusText;
        showError(`Gagal memproses permintaan Anda: ${escapeHtml(errorMessage)}`);
    }

    function displayMessage(message, className) {
        const chatOutput = $('#chat-output');
        const messageElement = $(`<div class="${className}"></div>`);
        chatOutput.append(messageElement);
    
        let i = 0;
        function typing() {
            if (i < message.length) {
                messageElement.html(messageElement.html() + escapeHtml(message[i]));
                i++;
                setTimeout(typing, 50); // Mengatur kecepatan mengetik
            }
        }
        typing();
    }    

    function showLoading(isLoading) {
        if (isLoading) {
            $('#chat-output').append('<div id="loading">Loading...</div>');
        } else {
            $('#loading').remove();
        }
    }

    function showError(message) {
        $('#chat-output').append(`<div class="error">${message}</div>`);
    }

    function scrollChatToBottom() {
        $('#chat-output').scrollTop($('#chat-output')[0].scrollHeight);
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    window.sendQuestion = sendQuestion;
    window.sendFeedback = sendFeedback; // Menjadikan fungsi sendFeedback tersedia secara global
});
