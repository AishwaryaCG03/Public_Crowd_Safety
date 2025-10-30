// Main JavaScript file for CrowdSafe application

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// AI Chatbot functionality
function initChatbot(eventId) {
    const chatForm = document.getElementById('chatbot-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const zoneInput = document.getElementById('zone-input');
    
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = chatInput.value.trim();
            const zone = zoneInput.value.trim();
            
            if (query === '') return;
            
            // Add user message to chat
            addMessage('user', query);
            chatInput.value = '';
            
            // Create a bot message container for streaming
            const botDiv = document.createElement('div');
            botDiv.classList.add('chat-message', 'bot-message');
            botDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Connecting...';
            chatMessages.appendChild(botDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Open SSE connection for real-time streaming
            const url = `/api/chatbot/stream?event_id=${encodeURIComponent(eventId)}&query=${encodeURIComponent(query)}&zone=${encodeURIComponent(zone)}`;
            const es = new EventSource(url);

            es.onmessage = (e) => {
                try {
                    const payload = JSON.parse(e.data);
                    const delta = payload.delta || '';
                    if (delta) {
                        // Replace initial loading text on first chunk
                        if (botDiv.innerHTML.includes('Connecting')) botDiv.innerHTML = '';
                        botDiv.innerHTML += delta;
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                } catch (err) {
                    // Fallback for plain text chunks
                    if (botDiv.innerHTML.includes('Connecting')) botDiv.innerHTML = '';
                    botDiv.innerHTML += e.data;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            };

            es.addEventListener('done', () => {
                es.close();
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });

            es.addEventListener('error', (e) => {
                es.close();
                botDiv.innerHTML = 'Sorry, there was an error processing your request. Please try again.';
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        });
    }
    
    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        messageDiv.innerHTML = message;
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Bottleneck Analysis Dashboard
function initBottleneckDashboard(eventId) {
    const densityChart = document.getElementById('density-chart');
    
    if (densityChart) {
        // Sample data - in a real application, this would come from the server
        const ctx = densityChart.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['12:00', '12:15', '12:30', '12:45', '13:00', '13:15', '13:30', '13:45', '14:00'],
                datasets: [{
                    label: 'Main Entrance',
                    data: [1.2, 1.5, 2.1, 3.2, 4.5, 5.1, 4.8, 3.9, 3.2],
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.4
                }, {
                    label: 'Food Court',
                    data: [0.8, 1.2, 1.8, 2.5, 3.1, 3.8, 4.2, 4.5, 4.1],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.4
                }, {
                    label: 'Stage Area',
                    data: [0.5, 0.8, 1.2, 2.8, 4.2, 5.8, 6.5, 6.2, 5.8],
                    borderColor: 'rgba(255, 206, 86, 1)',
                    backgroundColor: 'rgba(255, 206, 86, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Crowd Density Over Time (people/m²)'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Density (people/m²)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    }
}

// Evacuation Routes Map
function initEvacuationMap(eventId, latitude, longitude, restrictedAreas = [], incidents = []) {
    const mapContainer = document.getElementById('evacuation-map');
    
    if (mapContainer) {
        const map = L.map('evacuation-map').setView([latitude, longitude], 18);
        
        // Define multiple tile layers
        const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        });
        
        const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        });
        
        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
        });
        
        // Add default layer
        osmLayer.addTo(map);
        
        // Layer control
        const baseMaps = {
            "OpenStreetMap": osmLayer,
            "Street Map": streetLayer,
            "Satellite": satelliteLayer
        };
        
        L.control.layers(baseMaps).addTo(map);
        
        // Ensure map properly fits container
        setTimeout(() => map.invalidateSize(), 100);
        window.addEventListener('resize', () => map.invalidateSize());
        
        // Add venue marker
        const venueMarker = L.marker([latitude, longitude]).addTo(map);
        venueMarker.bindPopup("<b>Event Venue</b>").openPopup();

        // Real-time crowd density heatmap layer
        const heatLayer = L.heatLayer([], {
            radius: 25,
            blur: 20,
            maxZoom: 18,
            gradient: {
                0.0: 'green',
                0.5: 'yellow',
                0.8: 'orange',
                1.0: 'red'
            }
        }).addTo(map);

        // Legend control for density
        const legend = L.control({ position: 'bottomright' });
        legend.onAdd = function() {
            const div = L.DomUtil.create('div', 'heat-legend');
            div.innerHTML = `
                <div class="card shadow-sm p-2" style="min-width:180px;">
                    <div class="fw-bold mb-1">Density</div>
                    <div style="height:8px;background:linear-gradient(to right, green, yellow, orange, red)"></div>
                    <div class="text-muted small">Low → Critical</div>
                    <div id="density-stats" class="small mt-1">Waiting for data…</div>
                </div>`;
            return div;
        };
        legend.addTo(map);

        // Helper to show predictive overflow alerts
        const showMapAlert = (message, level) => {
            const cls = level === 'Critical' ? 'danger' : (level === 'High' ? 'warning' : 'info');
            const banner = document.createElement('div');
            banner.className = `alert alert-${cls}`;
            banner.role = 'alert';
            banner.textContent = message;
            banner.style.marginTop = '0.5rem';
            mapContainer.insertAdjacentElement('afterend', banner);
            setTimeout(() => banner.remove(), 6000);
        };
        
        // Sample exit points - in a real application, these would come from the database
        const exits = [
            { name: "Main Exit", lat: latitude + 0.0005, lng: longitude + 0.0005 },
            { name: "Emergency Exit 1", lat: latitude - 0.0003, lng: longitude + 0.0007 },
            { name: "Emergency Exit 2", lat: latitude + 0.0008, lng: longitude - 0.0003 }
        ];
        
        // Add exit markers
        exits.forEach(exit => {
            const exitMarker = L.marker([exit.lat, exit.lng], {
                icon: L.divIcon({
                    className: 'exit-marker',
                    html: '<i class="fas fa-door-open text-success fa-2x"></i>',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            }).addTo(map);
            
            exitMarker.bindPopup("<b>" + exit.name + "</b>");
        });

        // Socket.IO: subscribe to real-time density updates
        try {
            if (typeof io !== 'undefined') {
                const socket = io();
                socket.emit('join_event', { event_id: eventId });
                socket.on('density_update', (payload) => {
                    const { points = [], stats = {}, alert } = payload || {};
                    // Update heat layer with [lat, lng, intensity]
                    const latlngs = points.map(p => [p.lat, p.lng, p.intensity]);
                    heatLayer.setLatLngs(latlngs);
                    // Update stats in legend
                    const statsEl = document.getElementById('density-stats');
                    if (statsEl && stats && typeof stats.critical !== 'undefined') {
                        statsEl.textContent = `Critical hotspots: ${stats.critical}/${stats.total || latlngs.length}`;
                    }
                    // Show predictive overflow alert
                    if (alert && alert.message) {
                        showMapAlert(alert.message, alert.level || 'High');
                    }
                });
            }
        } catch (e) {
            console.warn('Socket.IO not available:', e);
        }
        
        // Helper: point-in-polygon (ray casting)
        const isPointInPolygon = (point, polygonCoords) => {
            let x = point.lng, y = point.lat;
            let inside = false;
            for (let i = 0, j = polygonCoords.length - 1; i < polygonCoords.length; j = i++) {
                const xi = polygonCoords[i][1], yi = polygonCoords[i][0];
                const xj = polygonCoords[j][1], yj = polygonCoords[j][0];
                const intersect = ((yi > y) !== (yj > y)) &&
                    (x < (xj - xi) * (y - yi) / (yj - yi + 0.0000001) + xi);
                if (intersect) inside = !inside;
            }
            return inside;
        };

        // Prepare restricted polygons
        const restrictedPolygons = (restrictedAreas || []).map(area => {
            try {
                const coords = JSON.parse(area.coordinates);
                return { name: area.name, coords };
            } catch (e) {
                console.error('Invalid restricted area coordinates', e);
                return null;
            }
        }).filter(Boolean);

        // Severity weights for safety scoring
        const severityWeight = { Low: 10, Medium: 20, High: 50, Critical: 100 };

        // Attempt to use user's live location
        let userMarker;
        let routingControl;
        const routeToExit = (userLatLng) => {
            // Compute safety-aware score for each exit
            let best = exits[0];
            let bestScore = Infinity;
            exits.forEach(exit => {
                const baseDist = Math.hypot(exit.lat - userLatLng.lat, exit.lng - userLatLng.lng);
                // Penalize exits inside restricted polygons
                let restrictedPenalty = 0;
                for (const poly of restrictedPolygons) {
                    if (isPointInPolygon({ lat: exit.lat, lng: exit.lng }, poly.coords)) {
                        restrictedPenalty += 1000; // large penalty to avoid
                    }
                }
                // Penalize exits near high-severity incidents
                let incidentPenalty = 0;
                (incidents || []).forEach(inc => {
                    const d = Math.hypot(inc.latitude - exit.lat, inc.longitude - exit.lng);
                    const weight = severityWeight[inc.severity] || 0;
                    // inverse distance weighting (avoid divide-by-zero)
                    incidentPenalty += weight / Math.max(d, 0.0001);
                });
                const score = baseDist + restrictedPenalty + incidentPenalty;
                if (score < bestScore) {
                    bestScore = score;
                    best = exit;
                }
            });

            // Draw route using Leaflet Routing Machine (OSRM)
            if (routingControl) {
                routingControl.remove();
            }
            routingControl = L.Routing.control({
                waypoints: [
                    L.latLng(userLatLng.lat, userLatLng.lng),
                    L.latLng(best.lat, best.lng)
                ],
                lineOptions: {
                    styles: [{ color: 'green', weight: 6, opacity: 0.8 }]
                },
                fitSelectedRoutes: true,
                show: false,
                addWaypoints: false,
                routeWhileDragging: false
            }).addTo(map);
        };

        const onGeolocateSuccess = (pos) => {
            const { latitude: userLat, longitude: userLng } = pos.coords;
            const userLatLng = { lat: userLat, lng: userLng };
            if (!userMarker) {
                userMarker = L.marker([userLat, userLng], {
                    icon: L.divIcon({
                        className: 'user-marker',
                        html: '<i class="fas fa-person-walking text-primary fa-2x"></i>',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    })
                }).addTo(map);
            } else {
                userMarker.setLatLng([userLat, userLng]);
            }
            userMarker.bindPopup('<b>Your Location</b>').openPopup();
            routeToExit(userLatLng);
        };

        const onGeolocateError = (err) => {
            console.warn('Geolocation unavailable:', err.message);
            // Fallback: route from venue
            routeToExit({ lat: latitude, lng: longitude });
        };

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(onGeolocateSuccess, onGeolocateError, {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            });
        } else {
            onGeolocateError({ message: 'Geolocation not supported' });
        }
    }
}

// Geofencing Restricted Areas
function initRestrictedAreas(eventId, latitude, longitude, restrictedAreas) {
    const mapContainer = document.getElementById('restricted-areas-map');
    
    if (mapContainer) {
        const map = L.map('restricted-areas-map').setView([latitude, longitude], 18);
        
        // Define multiple tile layers
        const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        });
        
        const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        });
        
        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
        });
        
        // Add default layer
        osmLayer.addTo(map);
        
        // Layer control
        const baseMaps = {
            "OpenStreetMap": osmLayer,
            "Street Map": streetLayer,
            "Satellite": satelliteLayer
        };
        
        L.control.layers(baseMaps).addTo(map);
        
        // Add venue marker
        const venueMarker = L.marker([latitude, longitude]).addTo(map);
        venueMarker.bindPopup("<b>Event Venue</b>").openPopup();
        
        // Add restricted areas
        if (restrictedAreas && restrictedAreas.length > 0) {
            restrictedAreas.forEach(area => {
                try {
                    const coordinates = JSON.parse(area.coordinates);
                    const polygon = L.polygon(coordinates, {
                        color: 'red',
                        fillColor: '#f03',
                        fillOpacity: 0.3
                    }).addTo(map);
                    
                    polygon.bindPopup("<b>" + area.name + "</b><br>" + area.description);
                } catch (e) {
                    console.error('Error parsing coordinates:', e);
                }
            });
        }
    }
}

// Missing Person Detection
function initMissingPersonForm() {
    const imageUpload = document.getElementById('image');
    const imagePreview = document.getElementById('image-preview');
    
    if (imageUpload && imagePreview) {
        imageUpload.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });
    }
}

// Initialize all modules based on page content
document.addEventListener('DOMContentLoaded', function() {
    // Get event ID and coordinates from data attributes if available
    const eventElement = document.getElementById('event-data');
    if (eventElement) {
        const eventId = eventElement.dataset.eventId;
        const latitude = parseFloat(eventElement.dataset.latitude);
        const longitude = parseFloat(eventElement.dataset.longitude);
        
        // Initialize modules as needed
        if (document.getElementById('chat-messages')) {
            initChatbot(eventId);
        }
        
        if (document.getElementById('density-chart')) {
            initBottleneckDashboard(eventId);
        }
        
        if (document.getElementById('evacuation-map')) {
            initEvacuationMap(eventId, latitude, longitude);
        }
        
        if (document.getElementById('restricted-areas-map')) {
            // Parse restricted areas from data attribute
            let restrictedAreas = [];
            try {
                restrictedAreas = JSON.parse(eventElement.dataset.restrictedAreas || '[]');
            } catch (e) {
                console.error('Error parsing restricted areas:', e);
            }
            
            initRestrictedAreas(eventId, latitude, longitude, restrictedAreas);
        }

        // In-app alert notifications
        initAlertNotifications(eventId);
    }
    
    // Initialize missing person form if present
    initMissingPersonForm();
});

// In-app notifications: listen for alert_broadcast and show Bootstrap alert
function initAlertNotifications(eventId) {
    if (typeof io === 'undefined' || !eventId) return;
    try {
        const socket = io();
        socket.emit('join_event', { event_id: eventId });
        socket.on('alert_broadcast', (payload) => {
            const container = document.querySelector('main.container .col-md-12');
            if (!container) return;
            const level = (payload.severity || 'Info');
            const cls = level === 'Critical' ? 'danger' : (level === 'High' ? 'warning' : 'info');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${cls} alert-dismissible fade show`;
            alertDiv.role = 'alert';
            const title = payload.title || 'Alert';
            const message = payload.message || '';
            alertDiv.innerHTML = `<strong>${title}</strong><br>${message}` +
                '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
            container.prepend(alertDiv);
            setTimeout(() => {
                try { alertDiv.remove(); } catch (e) {}
            }, 120000);
        });
    } catch (e) {
        console.warn('Alert notifications unavailable:', e);
    }
}