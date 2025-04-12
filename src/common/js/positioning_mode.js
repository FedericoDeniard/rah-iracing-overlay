/**
 * Positioning Mode UI for iRacing Telemetry Overlay
 * 
 * This script adds visual indicators when the overlay is in positioning mode
 */
function initPositioningMode() {
    console.log("Initializing positioning mode...");
    
    const overlayContainer = document.querySelector('.telemetry-container');
    if (!overlayContainer) {
        console.warn("Could not find telemetry container for positioning mode");
        return;
    }
    
    overlayContainer.style.border = '2px dashed rgba(46, 204, 113, 0.8)';
    overlayContainer.style.position = 'relative';
    
    addPositioningIndicator(overlayContainer);
    addPulseAnimation();
    
    console.log("Positioning mode initialized!");
}

/**
 * Add the positioning indicator element
 * @param {Element} container - The container to add the indicator to
 */
function addPositioningIndicator(container) {
    const existingIndicator = document.getElementById('positioning-mode-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const modeIndicator = document.createElement('div');
    modeIndicator.id = 'positioning-mode-indicator';
    modeIndicator.style.position = 'absolute';
    modeIndicator.style.top = '10px';
    modeIndicator.style.left = '10px';
    modeIndicator.style.backgroundColor = 'rgba(46, 204, 113, 0.9)';
    modeIndicator.style.color = 'white';
    modeIndicator.style.padding = '4px 8px';
    modeIndicator.style.borderRadius = '4px';
    modeIndicator.style.zIndex = '9999';
    modeIndicator.style.fontFamily = 'Arial, sans-serif';
    modeIndicator.style.fontSize = '11px';
    modeIndicator.style.fontWeight = 'bold';
    modeIndicator.style.opacity = '0.9';
    modeIndicator.style.pointerEvents = 'none'; 
    modeIndicator.textContent = 'POSITIONING MODE';
    
    container.appendChild(modeIndicator);
}

/**
 * Add pulse animation to the container
 */
function addPulseAnimation() {
    const existingStyle = document.getElementById('positioning-pulse-style');
    if (existingStyle) {
        existingStyle.remove();
    }
    
    const style = document.createElement('style');
    style.id = 'positioning-pulse-style';
    style.textContent = `
        .telemetry-container {
            animation: telemetry_pulse 2s infinite;
        }
        @keyframes telemetry_pulse {
            0% { box-shadow: 0 0 15px rgba(46, 204, 113, 0.2); }
            50% { box-shadow: 0 0 20px rgba(46, 204, 113, 0.8); }
            100% { box-shadow: 0 0 15px rgba(46, 204, 113, 0.2); }
        }
    `;
    document.head.appendChild(style);
} 