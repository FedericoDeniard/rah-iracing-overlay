/**
 * Position Reporter for iRacing Telemetry Overlay
 * 
 * This script handles position tracking and saving for overlay windows
 */

let currentX = 0;
let currentY = 0;
let initialX = 0;
let initialY = 0;
let positionReported = false;
let dpiScale = window.pywebview && window.pywebview.dpiScale ? window.pywebview.dpiScale : 1.0;

console.log("DPI Scale in position reporter:", dpiScale);

setTimeout(function() {
    if (window.pywebview && window.pywebview.position) {
        initialX = window.pywebview.position.x;
        initialY = window.pywebview.position.y;
        console.log("Initial position:", initialX, initialY);
    }
}, 1000);

/**
 * Initialize the position tracking and UI elements
 * @param {string} folderName - The folder name for position saving
 */
function initPositionReporter(folderName) {
    createSaveButton(folderName);
    createPositionDisplay();
    
    setInterval(function() {
        try {
            if (window.pywebview && window.pywebview.position) {
                currentX = window.pywebview.position.x;
                currentY = window.pywebview.position.y;
                updatePositionDisplay(currentX, currentY, dpiScale);
            } else {
                currentX = window.screenX || window.screenLeft || 0;
                currentY = window.screenY || window.screenTop || 0;
                
                currentX = Math.round(currentX * dpiScale);
                currentY = Math.round(currentY * dpiScale);
                updatePositionDisplay(currentX, currentY, dpiScale);
            }
        } catch (e) {
            console.error("Error getting position:", e);
        }
    }, 1000);
}

/**
 * Update position display and save button with current position
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 * @param {number} dpi - DPI scaling factor
 */
function updatePositionDisplay(x, y, dpi) {
    currentX = x;
    currentY = y;
    dpiScale = dpi;
    
    const display = document.getElementById('position-display');
    if (display) {
        display.textContent = `Position: (${x}, ${y}) - DPI: ${dpi}x`;
    }
    
    const saveBtn = document.getElementById('position-save-button');
    if (saveBtn) {
        if (!saveBtn.classList.contains('state-saving') && 
            !saveBtn.classList.contains('state-success') && 
            !saveBtn.classList.contains('state-error')) {
            
            const saveSpan = saveBtn.querySelector('.save-position-text');
            if (saveSpan) {
                saveSpan.innerHTML = `Save Position<small style="display:block;font-size:10px;margin-top:2px;">Current: (${x}, ${y})</small>`;
            }
        }
    }
}

/**
 * Create the save position button UI
 * @param {string} folderName - The folder name for saving position
 */
function createSaveButton(folderName) {
    if (document.getElementById('position-save-button')) return;
    
    var saveBtn = document.createElement('div');
    saveBtn.id = 'position-save-button';
    saveBtn.style.position = 'absolute';
    saveBtn.style.top = '10px';
    saveBtn.style.right = '10px';
    saveBtn.style.zIndex = '9999999';
    saveBtn.style.padding = '6px 10px';
    saveBtn.style.backgroundColor = 'rgba(46, 204, 113, 0.95)';
    saveBtn.style.color = 'white';
    saveBtn.style.borderRadius = '8px';
    saveBtn.style.cursor = 'pointer';
    saveBtn.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.5)';
    saveBtn.style.fontSize = '13px';
    saveBtn.style.fontFamily = 'Arial, sans-serif';
    saveBtn.style.backdropFilter = 'blur(5px)';
    saveBtn.style.border = '2px solid white';
    saveBtn.style.transition = 'all 0.3s ease';
    saveBtn.style.pointerEvents = 'auto';
    
    // Add a floppy disk icon
    saveBtn.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                <polyline points="17 21 17 13 7 13 7 21"></polyline>
                <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            <div class="save-position-text">
                <span style="font-weight: 500;">Save Position</span>
            </div>
        </div>
    `;
    
    saveBtn.addEventListener('mouseover', function() {
        this.style.backgroundColor = 'rgba(39, 174, 96, 0.95)';
        this.style.transform = 'translateY(-2px)';
    });
    
    saveBtn.addEventListener('mouseout', function() {
        this.style.backgroundColor = 'rgba(46, 204, 113, 0.95)';
        this.style.transform = 'translateY(0)';
    });
    
    saveBtn.addEventListener('click', function() {
        let x = currentX;
        let y = currentY;
        
        updateSaveBtnState('saving', x, y);
        fetch('/report_window_position', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                folder_name: folderName,
                position: {
                    x: x,
                    y: y
                },
                dpi_scale: dpiScale
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateSaveBtnState('success', x, y);
                setTimeout(function() {
                    window.close();
                }, 1000);
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error saving position:', error);
            updateSaveBtnState('error', x, y);
            
            setTimeout(function() {
                updateSaveBtnState('default', currentX, currentY);
            }, 2000);
        });
    });
    
    var overlayContainer = document.querySelector('.telemetry-container');
    if (overlayContainer) {
        if (window.getComputedStyle(overlayContainer).position !== 'relative') {
            overlayContainer.style.position = 'relative';
        }
        overlayContainer.appendChild(saveBtn);
    } else {
        document.body.appendChild(saveBtn);
    }
}

/**
 * Create position display element
 */
function createPositionDisplay() {
    if (document.getElementById('position-display')) return;
    
    var positionDisplay = document.createElement('div');
    positionDisplay.id = 'position-display';
    positionDisplay.style.position = 'fixed';
    positionDisplay.style.bottom = '10px';
    positionDisplay.style.left = '10px';
    positionDisplay.style.zIndex = '9999999';
    positionDisplay.style.padding = '4px 8px';
    positionDisplay.style.backgroundColor = 'rgba(0,0,0,0.8)';
    positionDisplay.style.color = 'white';
    positionDisplay.style.borderRadius = '4px';
    positionDisplay.style.fontSize = '12px';
    positionDisplay.style.fontFamily = 'monospace';
    positionDisplay.style.pointerEvents = 'none';
    positionDisplay.textContent = `Position: (${currentX}, ${currentY}) - DPI: ${dpiScale}x`;
    
    document.body.appendChild(positionDisplay);
}

/**
 * Update the save button state
 * @param {string} state - The button state (saving, success, error, default)
 * @param {number} x - X position
 * @param {number} y - Y position
 */
function updateSaveBtnState(state, x, y) {
    const saveBtn = document.getElementById('position-save-button');
    if (!saveBtn) return;
    
    saveBtn.classList.remove('state-saving', 'state-success', 'state-error');
    
    if (state === 'saving') {
        saveBtn.classList.add('state-saving');
        saveBtn.style.backgroundColor = 'rgba(243, 156, 18, 0.9)';
        saveBtn.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" stroke-dasharray="1, 2"></path>
                </svg>
                <div class="save-position-text">
                    <span style="font-weight: 500;">Saving...</span>
                </div>
            </div>
        `;
    } else if (state === 'success') {
        saveBtn.classList.add('state-success');
        saveBtn.style.backgroundColor = 'rgba(39, 174, 96, 0.95)';
        saveBtn.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 6L9 17l-5-5"></path>
                </svg>
                <div class="save-position-text">
                    <span style="font-weight: 500;">Saved!</span>
                </div>
            </div>
        `;
    } else if (state === 'error') {
        saveBtn.classList.add('state-error');
        saveBtn.style.backgroundColor = 'rgba(231, 76, 60, 0.95)';
        saveBtn.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12" y2="16"></line>
                </svg>
                <div class="save-position-text">
                    <span style="font-weight: 500;">Error!</span>
                </div>
            </div>
        `;
    } else {
        saveBtn.style.backgroundColor = 'rgba(46, 204, 113, 0.95)';
        saveBtn.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                    <polyline points="7 3 7 8 15 8"></polyline>
                </svg>
                <div class="save-position-text">
                    <span style="font-weight: 500;">Save Position</span>
                    <small style="display:block;font-size:10px;margin-top:2px;">Current: (${x}, ${y})</small>
                </div>
            </div>
        `;
    }
} 