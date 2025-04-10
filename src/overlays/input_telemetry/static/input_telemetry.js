document.addEventListener("DOMContentLoaded", function() {
    var socket = io('/input_telemetry');

    const canvas = document.getElementById("telemetry-graph");
    const ctx = canvas.getContext("2d");

    const steeringWheelImage = document.getElementById("steering-wheel");

    let throttleData = [];
    let brakeData = [];
    let clutchData = [];

    socket.on('connect', function() {
        console.log("Connected to telemetry namespace");
    });

    socket.on('telemetry_update', function(data) {
        updateTelemetryData(data);
    });

    socket.on('disconnect', function() {
        console.log("Disconnected from telemetry namespace");
    });

    function updateTelemetryData(data) {
        // Validate input data
        if (!data || typeof data !== 'object') {
            console.error('Invalid telemetry data received:', data);
            return;
        }
        
        // Process gear with validation
        let gearValue = data.gear;
        if (gearValue === null || gearValue === undefined) gearValue = 0;
        let gearDisplay = gearValue === 0 ? "N" : gearValue === -1 ? "R" : gearValue;
        document.getElementById('gear-display').innerText = gearDisplay;

        // Process speed with validation
        let speedValue = parseFloat(data.speed);
        if (isNaN(speedValue)) speedValue = 0;
        document.getElementById('speed-display').innerText = `${speedValue.toFixed(0)} kph`;

        // Process pedal inputs with validation
        const brakeValue = typeof data.brake === 'number' ? Math.max(0, Math.min(1, data.brake)) : 0;
        const throttleValue = typeof data.throttle === 'number' ? Math.max(0, Math.min(1, data.throttle)) : 0;
        const clutchValue = typeof data.clutch === 'number' ? Math.max(0, Math.min(1, data.clutch)) : 0;

        document.getElementById('brake-fill').style.height = `${brakeValue * 100}%`;
        document.getElementById('throttle-fill').style.height = `${throttleValue * 100}%`;
        document.getElementById('clutch-fill').style.height = `${clutchValue * 100}%`;

        // Process steering angle with validation
        let steeringAngleRadians = typeof data.steering_wheel_angle === 'number' ? data.steering_wheel_angle : 0;
        let steeringAngleDegrees = -steeringAngleRadians * (180 / Math.PI);
        steeringWheelImage.style.transform = `rotate(${steeringAngleDegrees}deg)`;

        // Update graph data with validation
        throttleData.push(throttleValue * 100);
        brakeData.push(brakeValue * 100);
        clutchData.push(clutchValue * 100);

        if (throttleData.length > canvas.width) {
            throttleData.shift();
            brakeData.shift();
            clutchData.shift();
        }
    }

    function drawGraph() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.lineWidth = 3;

        ctx.strokeStyle = "green";
        ctx.beginPath();
        throttleData.forEach((value, index) => {
            ctx.lineTo(index, canvas.height - value);
        });
        ctx.stroke();

        ctx.strokeStyle = "red";
        ctx.beginPath();
        brakeData.forEach((value, index) => {
            ctx.lineTo(index, canvas.height - value);
        });
        ctx.stroke();

        ctx.strokeStyle = "blue";
        ctx.beginPath();
        clutchData.forEach((value, index) => {
            ctx.lineTo(index, canvas.height - value);
        });
        ctx.stroke();
    }

    function animate() {
        drawGraph();
        requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
});
