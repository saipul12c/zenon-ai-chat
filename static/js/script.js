$(document).ready(function() {
    // Event Handler untuk tombol Enter pada input pengguna
    $('#user-input').on('keydown', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });

    // Menghandle klik pada tombol untuk menampilkan/menyembunyikan konten bantuan
    $('.help-button').click(function(event) {
        event.stopPropagation(); // Menghentikan event dari bubbling ke elemen lain
        $('.help-content').toggle(); // Menampilkan atau menyembunyikan konten
    });

    // Menghandle penekanan tombol keyboard pada tombol bantuan (enter dan spasi)
    $('.help-button').keypress(function(event) {
        if (event.key === "Enter" || event.key === " ") { // "Enter" atau spasi
            $(this).click();
            event.preventDefault(); // Mencegah scroll halaman jika menekan spasi
        }
    });

    // Optional: Menutup pop-up jika klik di luar area konten bantuan
    $(document).click(function(event) {
        if (!$(event.target).closest('.help-button, .help-content').length) {
            $('.help-content').hide();
        }
    });

    // Mengirimkan pertanyaan pengguna
    async function sendQuestion() {
        const userInput = $('#user-input').val().trim();
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
                $('#user-input').val('');
            }
        }
    }

    // Menambahkan formulir feedback
    function appendFeedbackForm(question) {
        const feedbackFormHtml = `
            <div class="feedback-form">
                <input type="text" placeholder="Feedback Anda" class="feedback-input" />
                <button onclick="sendFeedback('${escapeHtml(question)}', this)">Kirim Feedback</button>
            </div>`;
        $('#chat-output').append(feedbackFormHtml);
    }

    // Mengirim feedback pengguna
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

    // Menampilkan pesan kesalahan server
    function handleServerError(error) {
        const errorMessage = error.responseJSON?.error || error.statusText;
        showError(`Gagal memproses permintaan Anda: ${escapeHtml(errorMessage)}`);
    }

    // Menampilkan pesan di chat
    function displayMessage(message, className) {
        const chatOutput = $('#chat-output');
        const messageElement = $(`<div class="${className}"></div>`).appendTo(chatOutput);
        
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

    // Menampilkan atau menghilangkan indikator loading
    function showLoading(isLoading) {
        if (isLoading) {
            $('#chat-output').append('<div id="loading">Loading...</div>');
        } else {
            $('#loading').remove();
        }
    }

    // Menampilkan pesan error
    function showError(message) {
        $('#chat-output').append(`<div class="error">${message}</div>`);
    }

    // Gulir chat ke bawah
    function scrollChatToBottom() {
        $('#chat-output').scrollTop($('#chat-output')[0].scrollHeight);
    }

    // Mencegah XSS dengan meng-escape karakter HTML
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
