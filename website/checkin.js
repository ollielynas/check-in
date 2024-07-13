let map;
const friends = [
    { name: "Alice", lat: 40.730610, lng: -73.935242, checkInTime: "10:00 PM" },
    { name: "Bob", lat: 40.740610, lng: -73.925242, checkInTime: "10:15 PM" },
    { name: "Charlie", lat: 40.750610, lng: -73.915242, checkInTime: "10:20 PM" },
];

function initMap() {
    map = L.map('map').setView([40.730610, -73.935242], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    /*friends.forEach(friend => {
        const marker = L.marker([friend.lat, friend.lng]).addTo(map);
        marker.bindPopup(`<h3>${friend.name}</h3><p>Last check-in: ${friend.checkInTime}</p>`);
    });*/

    populateFriendList();
}

async function populateFriendList() {
    const friendList = document.getElementById('friends');

    const friendData = check_response(await get_all_presses());
    console.log(friendData);

    let focusOn = [0, 0];

    for (key in friendData) {
        console.log(key, friendData[key]);

        const listItem = document.createElement('li');

        const title = document.createElement("strong");
        title.innerText = key;
        listItem.appendChild(title);

        const startTime = new Date(Date.parse(friendData[key]["start"]));
        const formattedStartTime = startTime.toLocaleString();

        const startTimeDisplay = document.createElement("span");
        startTimeDisplay.classList.add("start-time");
        startTimeDisplay.innerText = `Started at ${formattedStartTime}`;
        listItem.appendChild(startTimeDisplay);

        const presses = friendData[key]["presses"];

        if (presses.length == 0) {
            const info = document.createElement("span");
            info.innerText = "Has not checked in yet";
            listItem.appendChild(info);
        } else {
            const lastCheckIn = presses[presses.length - 1];
            const time = new Date(Date.parse(lastCheckIn["timestamp"]));
            const now = new Date();

            const diff = Math.floor((now - time) / 60000);

            const elem = document.createElement("span");
            elem.innerText = `Checked in ${diff} minutes ago`;
            listItem.appendChild(elem);

            let lastLocation = null;
            for (press of presses) {
                if (press["location"]) {
                    lastLocation = press["location"];
                }
            }

            if (lastLocation) {
                const parts = lastLocation.split(", ");
                console.log(parts);

                const lat = Number.parseFloat(parts[0]);
                const long = Number.parseFloat(parts[1]);

                const marker = L.marker([lat, long]).addTo(map);
                console.log(marker);

                focusOn = [lat, long];

                listItem.onclick = () => map.setView([lat, long], 20);
            }
        }

        friendList.appendChild(listItem);
    }

    map.setView(focusOn);

    /*friends.forEach(friend => {
        
        listItem.innerHTML = `<strong>${friend.name}</strong><span>Last check-in:</span><span class="time">${friend.checkInTime}</span>`;
        friendList.appendChild(listItem);
    });*/
}

document.addEventListener('DOMContentLoaded', (event) => {
    initMap();
});
