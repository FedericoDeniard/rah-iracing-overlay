const insertData = ({
  position,
  driver,
  dclass,
  pts,
  best_lap,
  last_lap,
  gap,
}) => {
  return `<tr>
              <td>
                <p id="position">${position}</p>
              </td>
                <td id="driver">${driver}</td>
                <td >
                  <p id="class">
                    <span>${dclass}</span>
                    <span>${dclass}</span>
                  </p>
                </td>
                <td id="pts">
                  <span>${pts[0]}</span>
                  <span class="pts-arrow">${pts[1]}</span>
                  <span class="pts-value">${pts[2]}</span>
                </td>
                <td id="best_lap">${best_lap}</td>
                <td id="last_lap">${last_lap}</td>
                <td id="gap">${gap}</td>
            </tr>`;
};

const mockData = [
  {
    position: 1,
    driver: "Federico Deniard",
    dclass: "4.5 B",
    pts: ["2.5k", "^", "14"],
    best_lap: "1:34:22",
    last_lap: "1:36:22",
    gap: "11.9",
  },
  {
    position: 2,
    driver: "Ricardo Arjona",
    dclass: "4.5 B",
    pts: ["2.5k", "^", "14"],
    best_lap: "1:34:22",
    last_lap: "1:36:22",
    gap: "11.9",
  },
  {
    position: 3,
    driver: "Gustavo Bordon",
    dclass: "4.5 B",
    pts: ["2.5k", "^", "14"],
    best_lap: "1:34:22",
    last_lap: "1:36:22",
    gap: "11.9",
  },
];

document.addEventListener("DOMContentLoaded", () => {
  mockData.forEach((item) => {
    document.querySelector(".classification-table tbody").innerHTML +=
      insertData(item);
  });

  var socket = io('/classification_telemetry', {
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000
  });

  let isConnected = false;
  let reconnectTimer = null;

  socket.on('connect', function() {
    console.log("Connected to classification_telemetry namespace");
    isConnected = true;
    clearTimeout(reconnectTimer);
  });

socket.on('classification_update', function(data) {
    console.log("Received classification update");
    updateClassificationData(data); // TODO
});

// Handle heartbeats to ensure connection is alive
socket.on('heartbeat', function(data) {
    console.log("Heartbeat received");
});

socket.on('disconnect', function() {
    console.log("Disconnected from classification_telemetry namespace");
    isConnected = false;
    
    // Try to reconnect manually if socket.io reconnection fails
    reconnectTimer = setTimeout(function() {
        if (!isConnected) {
            console.log("Manually attempting to reconnect...");
            socket.connect();
        }
    }, 3000);
});

socket.on('error', function(error) {
    console.error("Socket error:", error);
});

socket.on('reconnect_attempt', function() {
    console.log("Attempting to reconnect...");
});

socket.on('reconnect', function(attemptNumber) {
    console.log("Reconnected after", attemptNumber, "attempts");
});

const updateClassificationData = (data) => {
  console.log(data)
    // Validate input data
    if (!data || typeof data !== 'object') {
        console.error('Invalid telemetry data received:', data);
        return;
    }
    
    // Process front last lap time with validation
    let front_last_lap_time = data.front_last_lap_time;
    if (front_last_lap_time === null || front_last_lap_time === undefined) front_last_lap_time = 0;
    let front_last_lap_timeDisplay = front_last_lap_time === 0 ? "N" : front_last_lap_time === -1 ? "R" : front_last_lap_time;
    console.log(front_last_lap_timeDisplay)
    // document.getElementById('front_last_lap_time-display').innerText = front_last_lap_timeDisplay;

    // Process front best lap time with validation
    let front_best_lap_time = data.front_best_lap_time;
    if (front_best_lap_time === null || front_best_lap_time === undefined) front_best_lap_time = 0;
    let front_best_lap_timeDisplay = front_best_lap_time <= 0 ? "N" : front_best_lap_time;
    console.log(front_best_lap_timeDisplay)
    // document.getElementById('front_best_lap_time-display').innerText = front_best_lap_timeDisplay;
}

})
