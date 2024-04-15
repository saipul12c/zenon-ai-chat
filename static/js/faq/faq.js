document.addEventListener('DOMContentLoaded', function() {
    fetch('static/js/faq/faq.json')
    .then(response => response.json())
    .then(data => {
        faqs = data.sort((a, b) => b.popularity - a.popularity);
        currentData = faqs;
        displayFAQs(1);
    })
    .catch(error => {
        console.error('Error loading the FAQ data:', error);
        displayError('Failed to load FAQs. Please try again later.');
    });
});

let currentPage = 1;
const pageSize = 10;
let currentData = [];
let faqs = [];

function displayFAQs(page) {
    currentPage = page;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const faqSlice = currentData.slice(start, end);

    const faqList = document.getElementById('faqList');
    faqList.innerHTML = '';

    faqSlice.forEach(faq => {
        const qElement = document.createElement('div');
        qElement.textContent = faq.question;
        qElement.className = 'question';
        qElement.onclick = function() {
            const answer = this.nextElementSibling;
            answer.style.display = answer.style.display === 'block' ? 'none' : 'block';
            answer.classList.toggle('open'); // Tambahkan animasi saat membuka jawaban
        };

        const aElement = document.createElement('div');
        aElement.innerHTML = `<p>${faq.answer}</p>`;
        aElement.className = 'answer';
        aElement.style.display = 'none'; // Sembunyikan jawaban secara default

        faqList.appendChild(qElement);
        faqList.appendChild(aElement);
    });

    displayPagination(currentData.length, page);
}

function displayPagination(totalItems, currentPage) {
    const pageCount = Math.ceil(totalItems / pageSize);
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    for (let i = 1; i <= pageCount; i++) {
        const li = document.createElement('li');
        li.textContent = i;
        if (i === currentPage) {
            li.classList.add('active');
        }
        li.onclick = () => displayFAQs(i);
        pagination.appendChild(li);
    }
}

function searchTopic() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toUpperCase();

    // Debounce the search to reduce frequent calls
    clearTimeout(searchTopic.debounce);
    searchTopic.debounce = setTimeout(() => {
        currentData = faqs.filter(faq =>
            faq.question.toUpperCase().includes(filter) || faq.answer.toUpperCase().includes(filter)
        );
        displayFAQs(1);
    }, 300); // Wait for 300 ms before executing the search
}

function displayError(message) {
    const faqList = document.getElementById('faqList');
    faqList.innerHTML = `<p class="error">${message}</p>`;
}

document.addEventListener('DOMContentLoaded', () => {
    currentData = faqs;
});
