document.addEventListener('DOMContentLoaded', function() {
    loadLatestRelease();
});

function toggleDescription(element) {
    var description = element.querySelector('.release-description');
    if (description.style.display === 'block') {
        description.style.display = 'none';
    } else {
        description.style.display = 'block';
    }
}

function loadLatestRelease() {
    fetch('static/js/note/note.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const releaseDiv = document.getElementById('latestRelease');
            releaseDiv.className += " release latest"; // Menambahkan class jika perlu
            releaseDiv.innerHTML = `
                <div class="release-title">${data.latest.version}</div>
                <div class="release-date">${data.latest.date}</div>
                <div class="release-description" style="display: none;">
                    ${data.latest.changes.map(change => `<p>- ${change}</p>`).join('')}
                </div>
            `;
        })
        .catch(error => {
            console.error('Error loading the release data:', error);
            const releaseDiv = document.getElementById('latestRelease');
            releaseDiv.textContent = 'Failed to load release data. Please try again later.';
        });
}
