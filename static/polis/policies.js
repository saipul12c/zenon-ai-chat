fetch('policies.json')
.then(response => response.json())
.then(data => {
    const container = document.getElementById('policies-container');
    data.forEach(section => {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'section';
        const contents = section.content.map(p => `<p>${p}</p>`).join('');
        sectionDiv.innerHTML = `<div class="section-title">${section.title}</div><div class="section-content">${contents}</div>`;
        container.appendChild(sectionDiv);
    });
})
.catch(error => console.error('Error loading the policies:', error));