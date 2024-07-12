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

    friends.forEach(friend => {
        const marker = L.marker([friend.lat, friend.lng]).addTo(map);
        marker.bindPopup(`<h3>${friend.name}</h3><p>Last check-in: ${friend.checkInTime}</p>`);
    });

    populateFriendList();
}

function populateFriendList() {
    const friendList = document.getElementById('friends');
    friends.forEach(friend => {
        const listItem = document.createElement('li');
        listItem.innerHTML = `<strong>${friend.name}</strong><span>Last check-in:</span><span class="time">${friend.checkInTime}</span>`;
        friendList.appendChild(listItem);
    });
}

document.addEventListener('DOMContentLoaded', (event) => {
    initMap();
});
