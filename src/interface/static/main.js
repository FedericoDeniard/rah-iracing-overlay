document.getElementById('overlayForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const selectedOverlays = Array.from(document.querySelectorAll('input[name="overlays"]:checked'))
                                  .map(checkbox => checkbox.value);
    fetch('/launch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ overlays: selectedOverlays })
    }).then(response => {
        if (response.ok) {
            alert('Overlays launched successfully!');
        } else {
            alert('Failed to launch overlays.');
        }
    });
}); 