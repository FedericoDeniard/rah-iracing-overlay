document.addEventListener("DOMContentLoaded", function() {
    var socket = io('/lap_pace');

    const canvas = document.getElementById("lap-pace-graph");
    const ctx = canvas.getContext("2d");

    let lapTimes = [];
    let optimalLapTime = null;

    socket.on('connect', function() {
        console.log("Connected to lap pace namespace");
    });

    socket.on('lap_time_update', function(data) {
        updateLapTimes(data);
    });

    socket.on('disconnect', function() {
        console.log("Disconnected from lap pace namespace");
    });

    function updateLapTimes(data) {
        lapTimes.push(data.lap_time);
        if (lapTimes.length > 10) {
            lapTimes.shift();
        }
        optimalLapTime = Math.min(...lapTimes);
        drawGraph();
    }

    function drawGraph() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw optimal lap line
        if (optimalLapTime) {
            ctx.strokeStyle = "green";
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            const optimalY = canvas.height - (optimalLapTime / Math.max(...lapTimes)) * canvas.height;
            ctx.beginPath();
            ctx.moveTo(0, optimalY);
            ctx.lineTo(canvas.width, optimalY);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // Draw lap times
        ctx.lineWidth = 2;
        ctx.strokeStyle = "red";
        ctx.beginPath();
        lapTimes.forEach((time, index) => {
            const x = (index / (lapTimes.length - 1)) * canvas.width;
            const y = canvas.height - (time / Math.max(...lapTimes)) * canvas.height;
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();

        ctx.fillStyle = "white";
        lapTimes.forEach((time, index) => {
            const x = (index / (lapTimes.length - 1)) * canvas.width;
            const y = canvas.height - (time / Math.max(...lapTimes)) * canvas.height;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }
});
