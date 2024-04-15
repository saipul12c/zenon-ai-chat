document.addEventListener('DOMContentLoaded', function() {
    fetch('static/js/polis/policies.json')  // Pastikan URL sudah benar sesuai lokasi file Anda
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const container = document.getElementById('policies-container');
        data.forEach(section => {
            // Membuat div untuk setiap section
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'section';

            // Membuat dan mengisi div untuk title
            const titleDiv = document.createElement('div');
            titleDiv.className = 'section-title';
            titleDiv.textContent = section.title;

            // Membuat dan mengisi div untuk content
            const contentDiv = document.createElement('div');
            contentDiv.className = 'section-content';
            section.content.forEach(paragraph => {
                const p = document.createElement('p');
                p.textContent = paragraph;
                contentDiv.appendChild(p);
            });

            // Menyusun struktur dan menambahkan ke container
            sectionDiv.appendChild(titleDiv);
            sectionDiv.appendChild(contentDiv);
            container.appendChild(sectionDiv);
        });
    })
    .catch(error => {
        console.error('Error loading the policies:', error);
        container.textContent = 'Unable to load policies. Please try again later.';
    });
});
