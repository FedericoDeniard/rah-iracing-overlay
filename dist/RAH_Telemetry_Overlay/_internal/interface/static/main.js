document.addEventListener('DOMContentLoaded', function() {
    // Get all available overlays
    fetch('/get_overlays')
        .then(response => response.json())
        .then(overlays => {
            const overlayList = document.getElementById('overlayList');
            overlays.forEach(overlay => {
                const displayName = overlay.display_name || 'Unknown';
                const description = overlay.description || 'No description available.';
                const hasPosition = overlay.position != null;
                const folderName = overlay.folder_name;
                const dpiInfo = overlay.dpi_info || {scale: 1.0};
                const previewGif = overlay.preview_gif || '/images/default-preview.gif';

                // Store the overlay properties in localStorage for later use
                if (overlay.position) {
                    localStorage.setItem(`overlay_position_${folderName}`, JSON.stringify(overlay.position));
                }

                const cardDiv = document.createElement('div');
                cardDiv.className = 'card'; 
                cardDiv.setAttribute('data-folder', folderName);
                cardDiv.setAttribute('data-name', displayName);
                cardDiv.setAttribute('data-description', description);
                cardDiv.setAttribute('data-preview', previewGif);

                const card2Div = document.createElement('div');
                card2Div.className = 'card2';

                card2Div.innerHTML = `
                    <div class="overlay-info">
                    <h4>${displayName}</h4>
                    ${hasPosition ? `<small>Position saved: (${overlay.position.x}, ${overlay.position.y})</small>` : ''}
                    </div>
                    <div class="button-container">
                        <button id="toggle-${folderName}" class="small-button" data-status="closed" data-name="${displayName}" data-folder="${folderName}">
                            <i class="fa-solid fa-arrow-up"></i>
                        </button>
                        <div class="secondary-buttons">
                            <button onclick="launchOverlay('${displayName}', '${folderName}', false)" title="Position Mode" class="small-button">
                                <i class="fa-solid fa-arrows-up-down-left-right"></i>
                            </button>
                        </div>
                        <button onclick="window.open('${overlay.url}', '_blank')" class="small-button">
                            <i class="fa-solid fa-globe"></i>
                        </button>
                    </div>
                `;

                cardDiv.appendChild(card2Div);
                overlayList.appendChild(cardDiv);

                // Add click event for preview
                cardDiv.addEventListener('click', function(e) {
                    // Prevent click if the user clicked on a button
                    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                        return;
                    }
                    
                    // Update the active card
                    document.querySelectorAll('.card').forEach(card => card.classList.remove('active'));
                    cardDiv.classList.add('active');
                    document.querySelectorAll('.card2').forEach(card2 => card2.classList.remove('active'));
                    card2Div.classList.add('active');
                    
                    // Show the preview
                    showPreview(
                        this.getAttribute('data-name'),
                        this.getAttribute('data-description'),
                        this.getAttribute('data-preview')
                    );
                });
                
                // Add event listener to toggle button after appending to DOM
                setTimeout(() => {
                    const toggleBtn = document.getElementById(`toggle-${folderName}`);
                    if (toggleBtn) {
                        toggleBtn.addEventListener('click', function() {
                            const status = this.getAttribute('data-status');
                            const name = this.getAttribute('data-name');
                            const folder = this.getAttribute('data-folder');
                            
                            if (status === 'closed') {
                                // Launch overlay
                                launchOverlay(name, folder, true);
                                this.setAttribute('data-status', 'open');
                                this.innerHTML = '<i class="fa-solid fa-arrow-down"></i>';
                                this.style.backgroundColor = '#e74c3c'; // Change to red
                                
                                // Store the state in localStorage to track opened overlays
                                localStorage.setItem(`overlay_open_${folder}`, 'true');
                            } else {
                                // Close overlay
                                closeOverlay(name, folder);
                                this.setAttribute('data-status', 'closed');
                                this.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
                                this.style.backgroundColor = '#ED2727'; // Reset to original color
                                
                                // Remove the state from localStorage
                                localStorage.removeItem(`overlay_open_${folder}`);
                            }
                        });
                        
                        // Initialize button state based on localStorage
                        if (localStorage.getItem(`overlay_open_${folderName}`) === 'true') {
                            toggleBtn.setAttribute('data-status', 'open');
                            toggleBtn.innerHTML = '<i class="fa-solid fa-arrow-down"></i>';
                            toggleBtn.style.backgroundColor = '#e74c3c';
                        }
                    }
                }, 0);
            });
            
            // Check for actually active overlays and update UI
            syncActiveOverlays();
            
            // Auto-select the first overlay to display preview
            if (overlays.length > 0) {
                const firstCard = document.querySelector('.card');
                if (firstCard) {
                    firstCard.click();
                }
            }
        });

    // Check if we're in positioning mode and show the save button
    if (localStorage.getItem('positioning_overlay')) {
        const positioningInfo = JSON.parse(localStorage.getItem('positioning_overlay'));
        createSavePositionButton(positioningInfo.displayName, positioningInfo.folderName);
    }
});

// Function to show overlay preview
function showPreview(name, description, previewUrl) {
    const previewContent = document.querySelector('.preview-content');
    const previewPlaceholder = document.querySelector('.preview-placeholder');
    
    // Update preview content
    document.getElementById('previewTitle').textContent = name;
    document.getElementById('previewDescription').textContent = description;
    
    const previewImg = document.getElementById('previewGif');
    const previewContainer = previewImg.parentElement;
    
    if (previewUrl) {
        // Show the image and hide the "no preview" message
        previewImg.style.display = 'block';
        if (document.getElementById('noPreviewMessage')) {
            document.getElementById('noPreviewMessage').remove();
        }
        
        previewImg.src = previewUrl;
        previewImg.alt = `${name} Preview`;
        
        // Handle image load error
        previewImg.onerror = function() {
            showNoPreviewMessage(previewContainer, previewImg);
        };
    } else {
        // No preview URL available
        showNoPreviewMessage(previewContainer, previewImg);
    }
    
    // Show preview content, hide placeholder
    previewPlaceholder.style.display = 'none';
    previewContent.style.display = 'flex';
}

function showNoPreviewMessage(container, imgElement) {
    // Hide the image element
    imgElement.style.display = 'none';
    
    // Remove existing message if it exists
    if (document.getElementById('noPreviewMessage')) {
        document.getElementById('noPreviewMessage').remove();
    }
    
    // Create a message element
    const message = document.createElement('div');
    message.id = 'noPreviewMessage';
    message.className = 'no-preview-message';
    message.innerHTML = `
        <i class="fa-solid fa-eye-slash"></i>
        <p>No preview available for this overlay</p>
    `;
    
    // Add to container
    container.appendChild(message);
}

// Function to synchronize UI with actual active overlays
function syncActiveOverlays() {
    fetch('/get_active_overlays')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const activeOverlays = data.active_overlays;
                
                // First, reset all buttons to closed state unless they are active
                document.querySelectorAll('[id^="toggle-"]').forEach(btn => {
                    const folderName = btn.getAttribute('data-folder');
                    
                    // If this overlay is not in the active list, ensure it shows as closed
                    if (!activeOverlays[folderName]) {
                        btn.setAttribute('data-status', 'closed');
                        btn.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
                        btn.style.backgroundColor = '#ED2727';
                        localStorage.removeItem(`overlay_open_${folderName}`);
                    }
                });
                
                // Now update buttons for active overlays
                for (const [folderName, overlayInfo] of Object.entries(activeOverlays)) {
                    const toggleBtn = document.getElementById(`toggle-${folderName}`);
                    if (toggleBtn) {
                        toggleBtn.setAttribute('data-status', 'open');
                        toggleBtn.innerHTML = '<i class="fa-solid fa-arrow-down"></i>';
                        toggleBtn.style.backgroundColor = '#e74c3c';
                        localStorage.setItem(`overlay_open_${folderName}`, 'true');
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error fetching active overlays:', error);
        });
}

function launchOverlay(displayName, folderName, isTransparent = true) {
    // Close any existing overlay first
    fetch('/launch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            overlay: displayName,
            transparent: isTransparent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(`${displayName} launched in ${isTransparent ? 'transparent' : 'positioning'} mode`);
            
            // Store the state in localStorage
            if (isTransparent) {
                localStorage.setItem(`overlay_open_${folderName}`, 'true');
                
                // Update the button state if it exists
                const toggleBtn = document.getElementById(`toggle-${folderName}`);
                if (toggleBtn) {
                    toggleBtn.setAttribute('data-status', 'open');
                    toggleBtn.innerHTML = '<i class="fa-solid fa-arrow-down"></i>';
                    toggleBtn.style.backgroundColor = '#e74c3c';
                }
            }
            
            if (!isTransparent) {
                showToast('Move overlay to desired position and click the Save Position button in the overlay window', false, 6000);
            }
        }
    })
    .catch(error => {
        console.error('Error launching overlay:', error);
        showToast('Network error launching overlay', true);
    });
}

function createSavePositionButton(displayName, folderName) {
    // Remove existing button if present
    const existingButton = document.getElementById('savePositionButton');
    if (existingButton) {
        existingButton.remove();
    }
    
    const saveButton = document.createElement('div');
    saveButton.id = 'savePositionButton';
    saveButton.className = 'floating-save-button';
    saveButton.innerHTML = `
        <button onclick="savePositionAndToggle('${displayName}', '${folderName}')">
            <i class="fa-solid fa-floppy-disk"></i> Save Position
        </button>
    `;
    
    document.body.appendChild(saveButton);
}

function savePositionAndToggle(displayName, folderName) {
    // Get current position from localStorage
    const currentPosition = JSON.parse(localStorage.getItem(`overlay_position_${folderName}`)) || { x: 100, y: 100 };
    
    // Set a random position for demo purposes (simulating user moving the window)
    // In production, you would get the actual window position
    currentPosition.x = Math.max(0, Math.min(window.innerWidth - 100, Math.floor(Math.random() * window.innerWidth)));  
    currentPosition.y = Math.max(0, Math.min(window.innerHeight - 100, Math.floor(Math.random() * window.innerHeight)));
    
    // Update localStorage with the new "moved" position
    localStorage.setItem(`overlay_position_${folderName}`, JSON.stringify(currentPosition));
    
    fetch('/toggle_to_transparent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            overlay: displayName,
            position: currentPosition
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(`Position saved and transparent overlay launched at the new position (${currentPosition.x}, ${currentPosition.y})`);
            
            // Remove the save button
            const saveButton = document.getElementById('savePositionButton');
            if (saveButton) {
                saveButton.remove();
            }
            
            // Clear positioning mode
            localStorage.removeItem('positioning_overlay');
            
            // Refresh the page after a delay to show updated position
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast('Error saving position or toggling overlay', true);
        }
    });
}

function closeOverlay(displayName, folderName) {
    // Call the close overlay endpoint
    fetch('/close_overlay', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            overlay: displayName,
            folder_name: folderName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(`${displayName} closed`);
            
            // Update localStorage state
            localStorage.removeItem(`overlay_open_${folderName}`);
            
            // Also update the button state if it exists
            const toggleBtn = document.getElementById(`toggle-${folderName}`);
            if (toggleBtn) {
                toggleBtn.setAttribute('data-status', 'closed');
                toggleBtn.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
                toggleBtn.style.backgroundColor = '#ED2727';
            }
        } else {
            showToast('Error closing overlay', true);
        }
    })
    .catch(error => {
        console.error('Error closing overlay:', error);
        showToast('Network error closing overlay', true);
    });
}

// Simple toast notification
function showToast(message, isError = false, duration = 3000) {
    // Remove existing toast if any
    const existingToast = document.getElementById('toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = isError ? 'toast error' : 'toast';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Show the toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto hide after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, duration);
} 