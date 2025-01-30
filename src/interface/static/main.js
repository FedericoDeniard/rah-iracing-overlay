document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_overlays')
        .then(response => response.json())
        .then(overlays => {
            const overlayList = document.getElementById('overlayList');
            overlays.forEach(overlay => {
                const displayName = overlay.display_name || 'Unknown';

                const overlayDiv = document.createElement('div');
                overlayDiv.className = 'col-lg-3 col-sm-6';
                overlayDiv.innerHTML = `
                    <div class="item">
                        <img src="assets/images/overlay-placeholder.jpg" alt="${displayName}">
                        <h4>${displayName}</h4>
                        <button onclick="launchOverlay('${overlay.display_name}')" id="launch-${overlay.display_name}">Open Overlay</button>
                        <button onclick="window.open('${overlay.url}', '_blank')">Open in Web</button>
                        <span id="status-${overlay.display_name}">Status: Not Opened</span>
                    </div>
                `;
                overlayList.appendChild(overlayDiv);
            });
        });
});

function launchOverlay(displayName) {
    fetch('/launch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ overlay: displayName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById(`launch-${displayName}`).disabled = true;
            document.getElementById(`status-${displayName}`).textContent = 'Status: Opened';
        }
    });
} 