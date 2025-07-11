const insertData = ({position, driver, dclass, pts, best_lap, last_lap, gap}) => {
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
                <td id="pts">${pts}</td>
                <td id="best_lap">${best_lap}</td>
                <td id="last_lap">${last_lap}</td>
                <td id="gap">${gap}</td>
            </tr>`
}

const mockData = [
    {
        position: 1,
        driver: "Federico Deniard",
        dclass: "4.5 B",
        pts: "2.5k ^14",
        best_lap: "1:34:22",
        last_lap: "1:36:22",
        gap: "11.9"
    },
    {
        position: 2,
        driver: "Ricardo Arjona",
        dclass: "4.5 B",
        pts: "2.5k ^14",
        best_lap: "1:34:22",
        last_lap: "1:36:22",
        gap: "11.9"
    },
    {
        position: 3,
        driver: "Gustavo Bordon",
        dclass: "4.5 B",
        pts: "2.5k ^14",
        best_lap: "1:34:22",
        last_lap: "1:36:22",
        gap: "11.9"
    }
]

document.addEventListener("DOMContentLoaded", () => {
    mockData.forEach((item) => {
        document.querySelector(".classification-table tbody").innerHTML += insertData(item)
    });
});