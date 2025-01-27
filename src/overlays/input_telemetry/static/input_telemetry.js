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
        let gearDisplay = data.gear === 0 ? "N" : data.gear === -1 ? "R" : data.gear;
        document.getElementById('gear-display').innerText = gearDisplay;

        document.getElementById('speed-display').innerText = `${data.speed.toFixed(0)} kph`;

        document.getElementById('brake-fill').style.height = `${data.brake * 100}%`;
        document.getElementById('throttle-fill').style.height = `${data.throttle * 100}%`;
        document.getElementById('clutch-fill').style.height = `${data.clutch * 100}%`;

        let steeringAngleRadians = data.steering_wheel_angle;
        let steeringAngleDegrees = -steeringAngleRadians * (180 / Math.PI);
        steeringWheelImage.style.transform = `rotate(${steeringAngleDegrees}deg)`;

        throttleData.push(data.throttle * 100);
        brakeData.push(data.brake * 100);
        clutchData.push(data.clutch * 100);

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
