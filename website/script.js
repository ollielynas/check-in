let map, userMarker;
let watchId = null;

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: -34.397, lng: 150.644 },
        zoom: 15
    });
    userMarker = new google.maps.Marker({
        map: map,
        title: 'Your Location'
    });
}

function startLocationSharing() {
    if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition(
            position => {
                const { latitude, longitude } = position.coords;
                const userLocation = new google.maps.LatLng(latitude, longitude);
                userMarker.setPosition(userLocation);
                map.setCenter(userLocation);
                sendLocationToServer(latitude, longitude);
            },
            error => console.error('Error getting location', error),
            { enableHighAccuracy: true }
        );
    } else {
        alert('Geolocation is not supported by this browser.');
    }
}

function stopLocationSharing() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
}

function sendLocationToServer(latitude, longitude) {
    fetch('/update_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ latitude, longitude })
    }).catch(error => console.error('Error sending location to server', error));
}

document.getElementById('start-sharing').addEventListener('click', startLocationSharing);
document.getElementById('stop-sharing').addEventListener('click', stopLocationSharing);
