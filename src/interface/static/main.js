document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_overlays')
        .then(response => response.json())
        .then(overlays => {
            const overlayList = document.getElementById('overlayList');
            overlays.forEach(overlay => {
                const displayName = overlay.display_name || 'Unknown';
                const description = overlay.description || 'No description available.';

                const cardDiv = document.createElement('div');
                cardDiv.className = 'card'; 

                const card2Div = document.createElement('div');
                card2Div.className = 'card2';

                card2Div.innerHTML = `
                    <div class="overlay-info">
                    <h4>${displayName}</h4>
                    <p>${description}</p>
                    </div>
                    <div class="button-container">
                        <button onclick="launchOverlay('${overlay.display_name}')" id="launch-${overlay.display_name}">
                            <i class="fa-solid fa-arrow-up"></i> Overlay
                        </button>
                        <button onclick="window.open('${overlay.url}', '_blank')">
                            <i class="fa-solid fa-globe"></i> URL
                        </button>
                    </div>
                `;

                cardDiv.appendChild(card2Div);
                overlayList.appendChild(cardDiv);
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