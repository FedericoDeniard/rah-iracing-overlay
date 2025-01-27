document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_overlays')
        .then(response => response.json())
        .then(overlays => {
            const overlayList = document.getElementById('overlayList');
            overlays.forEach(overlay => {
                const overlayDiv = document.createElement('div');
                overlayDiv.className = 'overlay-option';
                overlayDiv.innerHTML = `
                    <h2>${overlay.name}</h2>
                    <p>URL: <a href="${overlay.url}" target="_blank">${overlay.url}</a></p>
                    <button onclick="launchOverlay('${overlay.name}')">Open Overlay</button>
                `;
                overlayList.appendChild(overlayDiv);
            });
        });
});

function launchOverlay(overlayName) {
    fetch('/launch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ overlay: overlayName })
    });
} 