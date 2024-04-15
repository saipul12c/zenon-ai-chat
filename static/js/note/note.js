function toggleDescription(element) {
    var description = element.querySelector('.release-description');
    if (description.style.display === 'block') {
        description.style.display = 'none';
    } else {
        description.style.display = 'block';
    }
}

// Fungsi untuk memuat data dari JSON
function loadLatestRelease() {
    fetch('note.json')
        .then(response => response.json())
        .then(data => {
            const releaseDiv = document.getElementById('latestRelease');
            releaseDiv.innerHTML = `
                <div class="release-title">${data.latest.version}</div>
                <div class="release-date">${data.latest.date}</div>
                <div class="release-description">
                    ${data.latest.changes.map(change => `<p>- ${change}</p>`).join('')}
                </div>
            `;
        })
        .catch(error => console.error('Error loading the release data:', error));
}

loadLatestRelease();