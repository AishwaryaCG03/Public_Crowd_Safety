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

// Notify emergency contacts from Bottleneck Analysis panel
function initBottleneckNotify(eventId) {
    try {
        const form = document.getElementById('notify-contacts-form');
        if (!form || !eventId) return;
        const btn = document.getElementById('notify-contacts-btn');
        const feedback = document.getElementById('notify-feedback');

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            try {
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Notifying...';
                }
                const payload = {
                    risk_level: document.getElementById('risk_level')?.value || 'High',
                    message: document.getElementById('notify_message')?.value || '',
                    latitude: parseFloat(document.getElementById('latitude')?.value || ''),
                    longitude: parseFloat(document.getElementById('longitude')?.value || '')
                };
                const res = await fetch(`/event/${eventId}/bottleneck/notify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const json = await res.json().catch(() => ({}));
                if (res.ok && json.ok) {
                    if (feedback) {
                        feedback.style.display = 'block';
                        feedback.className = 'alert alert-success';
                        feedback.innerHTML = '<i class="fas fa-check-circle"></i> Contacts notified successfully.';
                    }
                    form.reset();
                } else {
                    throw new Error(json.error || 'Failed to notify contacts.');
                }
            } catch (err) {
                if (feedback) {
                    feedback.style.display = 'block';
                    feedback.className = 'alert alert-danger';
                    feedback.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${err.message}`;
                }
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-bullhorn"></i> Notify Emergency Contacts';
                }
            }
        });
    } catch (e) {
        console.warn('Notify contacts init failed:', e);
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

// Check-In & Capacity Dashboard
function initCheckinDashboard(eventId) {
    try {
        const checkinForm = document.getElementById('checkin-form');
        const checkoutForm = document.getElementById('checkout-form');
        const zoneSelect = document.getElementById('zone_id');
        const capacityTable = document.getElementById('capacity-table');
        const feedback = document.getElementById('checkin-feedback');
        const ctForm = document.getElementById('contact-trace-form');
        const ctZone = document.getElementById('ct_zone_id');
        const ctMinutes = document.getElementById('ct_minutes');
        const ctFeedback = document.getElementById('contact-trace-feedback');
        const ctResults = document.getElementById('contact-trace-results');

        // Join event room for realtime updates
        if (typeof io !== 'undefined' && eventId) {
            const sock = io();
            sock.emit('join_event', { event_id: eventId });
            sock.on('capacity_update', (payload) => {
                if (!capacityTable || !payload) return;
                const row = capacityTable.querySelector(`tr[data-zone-id="${payload.zone_id}"]`);
                if (row) {
                    row.querySelector('.current-capacity').textContent = payload.current_capacity;
                    row.querySelector('.capacity-percentage').textContent = `${payload.capacity_percentage.toFixed(1)}%`;
                }
            });
            sock.on('alert_broadcast', (payload) => {
                if (payload?.type === 'capacity') {
                    const toast = document.getElementById('alert-toast');
                    if (toast) {
                        toast.className = 'alert alert-warning';
                        toast.innerHTML = `<i class="fas fa-people-arrows"></i> ${payload.title}: ${payload.message}`;
                        toast.style.display = 'block';
                        setTimeout(() => { toast.style.display = 'none'; }, 6000);
                    }
                }
            });
        }

        async function postJSON(url, payload) {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const json = await res.json().catch(() => ({}));
            if (!res.ok || !json.ok) throw new Error(json.error || 'Request failed');
            return json;
        }

        if (checkinForm) {
            checkinForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                try {
                    const qr = document.getElementById('qr_code').value.trim();
                    const zid = parseInt(zoneSelect.value, 10);
                    await postJSON(`/event/${eventId}/scan`, { qr_code: qr, zone_id: zid });
                    if (feedback) {
                        feedback.style.display = 'block';
                        feedback.className = 'alert alert-success';
                        feedback.textContent = 'Check-in successful.';
                        setTimeout(() => { feedback.style.display = 'none'; }, 3000);
                    }
                    checkinForm.reset();
                } catch (err) {
                    if (feedback) {
                        feedback.style.display = 'block';
                        feedback.className = 'alert alert-danger';
                        feedback.textContent = err.message;
                    }
                }
            });
        }

        if (checkoutForm) {
            checkoutForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                try {
                    const qr = document.getElementById('qr_code_out').value.trim();
                    await postJSON(`/event/${eventId}/checkout`, { qr_code: qr });
                    if (feedback) {
                        feedback.style.display = 'block';
                        feedback.className = 'alert alert-info';
                        feedback.textContent = 'Checkout successful.';
                        setTimeout(() => { feedback.style.display = 'none'; }, 3000);
                    }
                    checkoutForm.reset();
                } catch (err) {
                    if (feedback) {
                        feedback.style.display = 'block';
                        feedback.className = 'alert alert-danger';
                        feedback.textContent = err.message;
                    }
                }
            });
        }

        if (ctForm) {
            ctForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (!ctZone || !ctMinutes) return;
                try {
                    const zid = parseInt(ctZone.value, 10);
                    const mins = parseInt(ctMinutes.value, 10);
                    const res = await fetch(`/api/event/${eventId}/contact_trace?zone_id=${zid}&minutes=${mins}`);
                    const json = await res.json().catch(() => ({}));
                    if (!res.ok || !json.ok) throw new Error(json.error || 'Trace failed');
                    const tbody = ctResults?.querySelector('tbody');
                    if (tbody) {
                        tbody.innerHTML = '';
                        (json.attendees || []).forEach(a => {
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td>${a.name || ''}</td>
                                <td>${a.email || ''}</td>
                                <td>${a.phone || ''}</td>
                                <td>${a.check_in_time || ''}</td>
                                <td>${a.check_out_time || ''}</td>
                            `;
                            tbody.appendChild(tr);
                        });
                        ctResults.style.display = 'block';
                    }
                    if (ctFeedback) {
                        ctFeedback.style.display = 'block';
                        ctFeedback.className = 'alert alert-info';
                        ctFeedback.textContent = `Found ${json.attendees?.length || 0} attendees in last ${json.minutes} minutes.`;
                        setTimeout(() => { ctFeedback.style.display = 'none'; }, 5000);
                    }
                } catch (err) {
                    if (ctFeedback) {
                        ctFeedback.style.display = 'block';
                        ctFeedback.className = 'alert alert-danger';
                        ctFeedback.textContent = err.message;
                    }
                    if (ctResults) ctResults.style.display = 'none';
                }
            });
        }
    } catch (e) {
        console.warn('Init check-in dashboard failed:', e);
    }
}

// Live Monitoring Dashboard
function initMonitoringDashboard(eventId) {
    const summaryEl = document.getElementById('monitoring-summary');
    const summaryBadgeEl = document.getElementById('monitoring-summary-badge');
    const crowdStateEl = document.getElementById('crowd-state');
    const crowdTrendEl = document.getElementById('crowd-trend');
    const riskLevelEl = document.getElementById('risk-level');
    const riskScoreEl = document.getElementById('risk-score');
    const activeAttendeesEl = document.getElementById('active-attendees');
    const recentCheckinsEl = document.getElementById('recent-checkins');
    const overallOccupancyEl = document.getElementById('overall-occupancy');
    const nearCapacityZonesEl = document.getElementById('near-capacity-zones');
    const lastUpdatedEl = document.getElementById('monitoring-last-updated');
    const modelNameEl = document.getElementById('model-name');
    const modelTypeEl = document.getElementById('model-type');
    const modelFeaturesEl = document.getElementById('model-features');
    const likelyCausesEl = document.getElementById('likely-causes-list');
    const recommendationsEl = document.getElementById('recommendations-list');
    const videoForm = document.getElementById('video-analysis-form');
    const videoModeInput = document.getElementById('source_mode');
    const videoFileInput = document.getElementById('video_file');
    const videoSourceInput = document.getElementById('source_url');
    const videoSubmitBtn = document.getElementById('video-analysis-submit');
    const videoStopBtn = document.getElementById('video-analysis-stop');
    const videoStatusText = document.getElementById('video-analysis-status-text');
    const videoFeedback = document.getElementById('video-analysis-feedback');
    const videoHotspotsEl = document.getElementById('video-hotspots-list');
    const videoPreviewFrame = document.getElementById('video-preview-frame');
    const videoPreviewEmpty = document.getElementById('video-preview-empty');
    const videoResultFrames = document.getElementById('video-result-frames');
    const videoResultCurrent = document.getElementById('video-result-current');
    const videoResultAverage = document.getElementById('video-result-average');
    const videoResultPeak = document.getElementById('video-result-peak');
    const videoResultsSummary = document.getElementById('video-results-summary');
    const heatmapCanvas = document.getElementById('video-heatmap-canvas');
    const heatmapCaption = document.getElementById('video-heatmap-caption');
    const zoneTableBody = document.querySelector('#monitoring-zone-table tbody');
    const trendCanvas = document.getElementById('monitoring-trend-chart');

    if (!eventId || !zoneTableBody || !trendCanvas) return;

    let trendChart;
    const heatmapContext = heatmapCanvas ? heatmapCanvas.getContext('2d') : null;

    const levelClassName = (value) => {
        const normalized = (value || '').toLowerCase();
        if (normalized === 'critical') return 'monitoring-badge critical';
        if (normalized === 'crowded' || normalized === 'high') return 'monitoring-badge crowded';
        if (normalized === 'busy' || normalized === 'moderate') return 'monitoring-badge busy';
        return 'monitoring-badge normal';
    };

    const titleCase = (value) => {
        if (!value) return '--';
        return value.charAt(0).toUpperCase() + value.slice(1);
    };

    const formatRelativeTime = (isoValue) => {
        if (!isoValue) return 'Waiting for first update...';
        const diffSeconds = Math.max(0, Math.round((Date.now() - new Date(isoValue).getTime()) / 1000));
        if (diffSeconds < 10) return 'Updated just now';
        if (diffSeconds < 60) return `Updated ${diffSeconds}s ago`;
        const diffMinutes = Math.round(diffSeconds / 60);
        return `Updated ${diffMinutes}m ago`;
    };

    const renderList = (container, items) => {
        if (!container) return;
        container.innerHTML = '';
        const normalizedItems = (items || []).length ? items : ['No data available yet.'];
        normalizedItems.forEach((item) => {
            const li = document.createElement('li');
            li.textContent = typeof item === 'string' ? item : JSON.stringify(item);
            container.appendChild(li);
        });
    };

    const showVideoFeedback = (message, type) => {
        if (!videoFeedback) return;
        videoFeedback.style.display = 'block';
        videoFeedback.className = `alert alert-${type}`;
        videoFeedback.textContent = message;
    };

    const clearHeatmap = (message) => {
        if (!heatmapContext || !heatmapCanvas) return;
        heatmapContext.clearRect(0, 0, heatmapCanvas.width, heatmapCanvas.height);
        heatmapContext.fillStyle = '#0f172a';
        heatmapContext.fillRect(0, 0, heatmapCanvas.width, heatmapCanvas.height);
        heatmapContext.fillStyle = 'rgba(255,255,255,0.08)';
        for (let x = 0; x < heatmapCanvas.width; x += 40) {
            heatmapContext.fillRect(x, 0, 1, heatmapCanvas.height);
        }
        for (let y = 0; y < heatmapCanvas.height; y += 40) {
            heatmapContext.fillRect(0, y, heatmapCanvas.width, 1);
        }
        heatmapContext.fillStyle = '#cbd5e1';
        heatmapContext.font = '14px sans-serif';
        heatmapContext.fillText(message || 'Waiting for heatmap data...', 20, 28);
    };

    const renderHeatmap = (points) => {
        if (!heatmapContext || !heatmapCanvas) return;
        clearHeatmap('Analyzing live crowd distribution...');
        const width = heatmapCanvas.width;
        const height = heatmapCanvas.height;

        (points || []).forEach((point) => {
            const x = point.x * width;
            const y = point.y * height;
            const radius = 30 + (point.intensity * 45);
            const gradient = heatmapContext.createRadialGradient(x, y, 0, x, y, radius);
            gradient.addColorStop(0, `rgba(255, 59, 48, ${Math.min(0.8, 0.25 + point.intensity)})`);
            gradient.addColorStop(0.45, `rgba(255, 159, 10, ${Math.min(0.45, 0.1 + point.intensity / 2)})`);
            gradient.addColorStop(1, 'rgba(255, 205, 86, 0)');
            heatmapContext.fillStyle = gradient;
            heatmapContext.beginPath();
            heatmapContext.arc(x, y, radius, 0, Math.PI * 2);
            heatmapContext.fill();
        });

        heatmapContext.strokeStyle = 'rgba(255,255,255,0.18)';
        heatmapContext.strokeRect(0.5, 0.5, width - 1, height - 1);
    };

    const renderVideoHotspots = (hotspots) => {
        if (!videoHotspotsEl) return;
        videoHotspotsEl.innerHTML = '';
        const items = hotspots && hotspots.length
            ? hotspots.map((spot, index) => `Hotspot ${index + 1}: intensity ${(spot.intensity * 100).toFixed(0)}% at (${spot.x.toFixed(2)}, ${spot.y.toFixed(2)})`)
            : ['No hotspots detected yet.'];
        items.forEach((item) => {
            const li = document.createElement('li');
            li.textContent = item;
            videoHotspotsEl.appendChild(li);
        });
    };

    const renderVideoAnalysis = (videoAnalysis) => {
        const analysis = videoAnalysis || {};
        const status = analysis.status || 'idle';
        const progress = typeof analysis.progress === 'number' ? analysis.progress.toFixed(1) : '0.0';
        const isLive = analysis.source_mode === 'live';
        const hasResults = !!analysis.result_available;

        if (videoStatusText) {
            const sourceLabel = analysis.source_label ? ` Source: ${analysis.source_label}` : '';
            const progressText = isLive
                ? (status === 'processing' ? ' live' : '')
                : (status === 'processing' || status === 'queued' || status === 'completed' ? ` (${progress}%)` : '');
            videoStatusText.textContent = `${titleCase(status)}${progressText}.${sourceLabel}`;
        }

        if (heatmapCaption) {
            heatmapCaption.textContent = analysis.message || 'Heatmap will appear once CCTV/video analysis starts.';
        }

        if (videoStopBtn) {
            videoStopBtn.disabled = !(status === 'processing' || status === 'reconnecting' || status === 'queued');
        }

        if (analysis.preview_frame && videoPreviewFrame) {
            videoPreviewFrame.src = analysis.preview_frame;
            videoPreviewFrame.style.display = 'block';
            if (videoPreviewEmpty) videoPreviewEmpty.style.display = 'none';
        } else if (videoPreviewFrame) {
            videoPreviewFrame.style.display = 'none';
            if (videoPreviewEmpty) videoPreviewEmpty.style.display = 'block';
        }

        if (analysis.heatmap_points && analysis.heatmap_points.length) {
            renderHeatmap(analysis.heatmap_points);
        } else {
            clearHeatmap(analysis.message || 'Waiting for heatmap data...');
        }

        renderVideoHotspots(analysis.hotspots || []);

        if (videoResultFrames) videoResultFrames.textContent = analysis.analyzed_frames ?? 0;
        if (videoResultCurrent) videoResultCurrent.textContent = analysis.latest_people_count ?? 0;
        if (videoResultAverage) videoResultAverage.textContent = analysis.average_people_count ?? 0;
        if (videoResultPeak) videoResultPeak.textContent = analysis.peak_people_count ?? 0;
        if (videoResultsSummary) {
            if (hasResults) {
                const modeText = isLive ? 'live CCTV feed' : 'uploaded video';
                videoResultsSummary.textContent = `Latest ${modeText} results are available. Hotspots: ${(analysis.hotspots || []).length}. Last update: ${formatRelativeTime(analysis.updated_at || analysis.finished_at)}.`;
            } else {
                videoResultsSummary.textContent = 'Analyzed results will stay visible here after processing completes.';
            }
        }

        if (analysis.error) {
            showVideoFeedback(analysis.error, 'danger');
        }
    };

    const renderZones = (zones) => {
        if (!zoneTableBody) return;
        if (!zones || !zones.length) {
            zoneTableBody.innerHTML = '<tr><td colspan="5" class="text-muted">No zones configured yet.</td></tr>';
            return;
        }

        zoneTableBody.innerHTML = zones.map((zone) => `
            <tr>
                <td>
                    <div class="fw-semibold">${zone.name}</div>
                    <div class="small text-muted">${zone.description || 'No zone description available.'}</div>
                </td>
                <td><span class="${levelClassName(zone.status)}">${zone.status_label}</span></td>
                <td>${zone.current_capacity}</td>
                <td>${zone.max_capacity}</td>
                <td>${zone.capacity_percentage.toFixed(1)}%</td>
            </tr>
        `).join('');
    };

    const renderTrendChart = (history) => {
        const labels = (history || []).map((point) => {
            const date = new Date(point.timestamp);
            return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
        });
        const occupancyData = (history || []).map((point) => point.overall_capacity_percentage);
        const riskData = (history || []).map((point) => point.risk_score);

        if (!trendChart) {
            trendChart = new Chart(trendCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        {
                            label: 'Occupancy %',
                            data: occupancyData,
                            borderColor: 'rgba(13, 110, 253, 1)',
                            backgroundColor: 'rgba(13, 110, 253, 0.12)',
                            tension: 0.3,
                            fill: true
                        },
                        {
                            label: 'Risk Score',
                            data: riskData,
                            borderColor: 'rgba(220, 53, 69, 1)',
                            backgroundColor: 'rgba(220, 53, 69, 0.08)',
                            tension: 0.3,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
            return;
        }

        trendChart.data.labels = labels;
        trendChart.data.datasets[0].data = occupancyData;
        trendChart.data.datasets[1].data = riskData;
        trendChart.update();
    };

    const renderMonitoringPayload = (payload) => {
        if (!payload) return;

        if (summaryEl) summaryEl.textContent = payload.summary || 'No monitoring summary available.';
        if (summaryBadgeEl) {
            summaryBadgeEl.className = levelClassName(payload.crowd_state);
            summaryBadgeEl.textContent = payload.crowd_state || 'Unknown';
        }
        if (crowdStateEl) crowdStateEl.textContent = payload.crowd_state || '--';
        if (crowdTrendEl) {
            const delta = typeof payload.occupancy_delta === 'number' ? payload.occupancy_delta.toFixed(1) : '0.0';
            crowdTrendEl.textContent = `Trend: ${titleCase(payload.trend)} (${delta >= 0 ? '+' : ''}${delta}%)`;
        }
        if (riskLevelEl) {
            riskLevelEl.textContent = payload.risk_level || '--';
            riskLevelEl.className = `monitoring-stat-value ${levelClassName(payload.risk_level).replace('monitoring-badge ', '')}`;
        }
        if (riskScoreEl) riskScoreEl.textContent = payload.risk_score ?? 0;
        if (activeAttendeesEl) activeAttendeesEl.textContent = payload.active_attendees ?? 0;
        if (recentCheckinsEl) recentCheckinsEl.textContent = payload.recent_checkins ?? 0;
        if (overallOccupancyEl) overallOccupancyEl.textContent = `${(payload.overall_capacity_percentage ?? 0).toFixed(1)}%`;
        if (nearCapacityZonesEl) nearCapacityZonesEl.textContent = payload.near_capacity_zones ?? 0;
        if (lastUpdatedEl) lastUpdatedEl.textContent = formatRelativeTime(payload.timestamp);

        if (modelNameEl) modelNameEl.textContent = payload.model?.name || 'Hybrid Crowd Risk Inference';
        if (modelTypeEl) modelTypeEl.textContent = payload.model?.type || 'Tabular real-time event risk scoring';
        if (modelFeaturesEl) {
            modelFeaturesEl.textContent = (payload.model?.features || []).join(' | ');
        }

        renderList(likelyCausesEl, payload.likely_causes || []);
        renderList(recommendationsEl, payload.recommendations || []);
        renderZones(payload.zones || []);
        renderTrendChart(payload.history || []);
        renderVideoAnalysis(payload.video_analysis || {});
    };

    const fetchMonitoring = async () => {
        const res = await fetch(`/api/event/${eventId}/monitoring`);
        if (!res.ok) throw new Error('Unable to fetch monitoring data.');
        return res.json();
    };

    fetchMonitoring()
        .then(renderMonitoringPayload)
        .catch((error) => {
            if (summaryEl) summaryEl.textContent = error.message;
        });

    clearHeatmap('Waiting for heatmap data...');

    if (videoForm) {
        videoForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const hasFile = !!(videoFileInput && videoFileInput.files && videoFileInput.files.length);
            const sourceUrl = videoSourceInput ? videoSourceInput.value.trim() : '';
            const sourceMode = videoModeInput ? videoModeInput.value : 'live';
            if (sourceMode === 'upload' && !hasFile) {
                showVideoFeedback('Select a video file first for uploaded-video analysis.', 'warning');
                return;
            }
            if (sourceMode === 'live' && !sourceUrl) {
                showVideoFeedback('Enter a live CCTV camera URL first.', 'warning');
                return;
            }

            try {
                if (videoSubmitBtn) {
                    videoSubmitBtn.disabled = true;
                    videoSubmitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
                }
                const formData = new FormData();
                if (hasFile) formData.append('video_file', videoFileInput.files[0]);
                if (sourceUrl) formData.append('source_url', sourceUrl);
                formData.append('source_mode', sourceMode);

                const response = await fetch(`/event/${eventId}/monitoring/video`, {
                    method: 'POST',
                    body: formData
                });
                const payload = await response.json().catch(() => ({}));
                if (!response.ok || !payload.ok) {
                    throw new Error(payload.error || 'Unable to start video analysis.');
                }
                showVideoFeedback(payload.message || 'Video AI analysis started.', 'success');
            } catch (error) {
                showVideoFeedback(error.message, 'danger');
            } finally {
                if (videoSubmitBtn) {
                    videoSubmitBtn.disabled = false;
                    videoSubmitBtn.innerHTML = '<i class="fas fa-video"></i> Start Video AI';
                }
            }
        });
    }

    if (videoStopBtn) {
        videoStopBtn.addEventListener('click', async () => {
            try {
                videoStopBtn.disabled = true;
                const response = await fetch(`/event/${eventId}/monitoring/video/stop`, {
                    method: 'POST'
                });
                const payload = await response.json().catch(() => ({}));
                if (!response.ok || !payload.ok) {
                    throw new Error(payload.error || 'Unable to stop live video analysis.');
                }
                showVideoFeedback(payload.message || 'Stop request sent.', 'info');
            } catch (error) {
                showVideoFeedback(error.message, 'danger');
            }
        });
    }

    if (typeof io !== 'undefined') {
        const socket = io();
        socket.emit('join_event', { event_id: eventId });
        socket.on('monitoring_update', renderMonitoringPayload);
        socket.on('video_analysis_update', renderVideoAnalysis);
    }

    setInterval(async () => {
        try {
            const payload = await fetchMonitoring();
            renderMonitoringPayload(payload);
        } catch (error) {
            console.warn('Monitoring refresh failed:', error);
        }
    }, 15000);
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

        if (document.getElementById('monitoring-zone-table')) {
            initMonitoringDashboard(eventId);
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

        // Notify emergency contacts panel
        if (document.getElementById('notify-contacts-form')) {
            initBottleneckNotify(eventId);
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
