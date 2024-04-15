$(document).ready(function() {
    const chatOutput = $('#chat-output');
    const userInputField = $('#user-input');

    userInputField.on('keydown', handleUserInput);
    $('.help-button').on('click', toggleHelpContent).keypress(handleHelpButtonKeypress);
    $(document).click(hideHelpContentOnClickOutside);

    async function handleUserInput(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            await sendQuestion();
        }
    }

    function toggleHelpContent(event) {
        event.stopPropagation();
        $('.help-content').toggle();
    }

    function handleHelpButtonKeypress(event) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            $(this).click();
        }
    }

    function hideHelpContentOnClickOutside(event) {
        if (!$(event.target).closest('.help-button, .help-content').length) {
            $('.help-content').hide();
        }
    }

    async function sendQuestion() {
        const userInput = userInputField.val().trim();
        if (userInput) {
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
                userInputField.val('');
            }
        }
    }

    function appendFeedbackForm(question) {
        const feedbackFormHtml = `
            <div class="feedback-form">
                <input type="text" placeholder="Feedback Anda" class="feedback-input" />
                <button onclick="sendFeedback('${escapeHtml(question)}', this)">Kirim Feedback</button>
            </div>`;
        chatOutput.append(feedbackFormHtml);
    }

    async function sendFeedback(question, buttonElement) {
        const feedbackInput = $(buttonElement).prev('.feedback-input').val().trim();
        if (feedbackInput) {
            try {
                const response = await $.ajax({
                    url: '/feedback',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ question, feedback: feedbackInput })
                });
                alert('Feedback terkirim: ' + response.message);
                $(buttonElement).parent('.feedback-form').remove();
            } catch (error) {
                showError('Gagal mengirim feedback: ' + error.statusText);
            }
        } else {
            alert('Silakan masukkan feedback sebelum mengirim.');
        }
    }

    function handleServerError(error) {
        const errorMessage = error.responseJSON?.error || error.statusText;
        showError(`Gagal memproses permintaan Anda: ${escapeHtml(errorMessage)}`);
    }

    function displayMessage(message, className) {
        const messageElement = $('<div>').addClass(className).appendTo(chatOutput);
        let i = 0;
        function typing() {
            if (i < message.length) {
                messageElement.html(messageElement.html() + escapeHtml(message[i]));
                i++;
                setTimeout(typing, 50);
            }
        }
        typing();
    }

    function showLoading(isLoading) {
        if (isLoading) {
            chatOutput.append('<div id="loading">Loading...</div>');
        } else {
            $('#loading').remove();
        }
    }

    function showError(message) {
        chatOutput.append(`<div class="error">${message}</div>`);
    }

    function scrollChatToBottom() {
        chatOutput.scrollTop(chatOutput[0].scrollHeight);
    }

    function escapeHtml(text) {
        return text.replace(/[&<>"']/g, match => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        })[match]);
    }

    window.sendQuestion = sendQuestion;
    window.sendFeedback = sendFeedback;
});
