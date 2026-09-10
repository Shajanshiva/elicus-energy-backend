let token = null;
let map = null;
let vehicleMarker = null;
let routePolyline = null;
let pollingInterval = null;
let currentAssignedVehicleNumber = null;

const API_BASE = "";

// DOM Elements
const loginSection = document.getElementById("login-section");
const dashboardSection = document.getElementById("dashboard-section");
const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const userProfile = document.getElementById("user-profile");
const userDisplayName = document.getElementById("user-display-name");
const logoutBtn = document.getElementById("logout-btn");

const routeNameEl = document.getElementById("route-name");
const routeStartEl = document.getElementById("route-start");
const routeEndEl = document.getElementById("route-end");

const vehicleCodeEl = document.getElementById("vehicle-code");
const vehicleSpeedEl = document.getElementById("vehicle-speed");
const vehicleUpdatedEl = document.getElementById("vehicle-updated");
const vehicleStatusEl = document.getElementById("vehicle-status");

const testUnauthorizedBtn = document.getElementById("test-unauthorized-btn");
const securityResultEl = document.getElementById("security-result");

// Quick Demo User Buttons
document.getElementById("demo-user-a").addEventListener("click", () => {
  document.getElementById("email").value = "usera@test.com";
  document.getElementById("password").value = "password123";
  loginForm.dispatchEvent(new Event("submit"));
});

document.getElementById("demo-user-b").addEventListener("click", () => {
  document.getElementById("email").value = "userb@test.com";
  document.getElementById("password").value = "password123";
  loginForm.dispatchEvent(new Event("submit"));
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.classList.add("hidden");

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Authentication failed.");
    }

    const data = await res.json();
    token = data.access_token;

    loginSection.classList.add("hidden");
    dashboardSection.classList.remove("hidden");
    userProfile.classList.remove("hidden");

    await loadAssignment();
    startPolling();
  } catch (err) {
    loginError.textContent = err.message;
    loginError.classList.remove("hidden");
  }
});

logoutBtn.addEventListener("click", () => {
  token = null;
  if (pollingInterval) clearInterval(pollingInterval);
  dashboardSection.classList.add("hidden");
  userProfile.classList.add("hidden");
  loginSection.classList.remove("hidden");
});

async function loadAssignment() {
  const res = await fetch(`${API_BASE}/me/assignment`, {
    headers: { "Authorization": `Bearer ${token}` }
  });

  if (!res.ok) return;
  const data = await res.json();

  userDisplayName.textContent = `${data.user.full_name} (${data.user.email})`;

  if (data.route) {
    routeNameEl.textContent = data.route.name;
    routeStartEl.textContent = data.route.start_location;
    routeEndEl.textContent = data.route.end_location;
  }

  if (data.vehicle) {
    currentAssignedVehicleNumber = data.vehicle.vehicle_number;
    vehicleCodeEl.textContent = data.vehicle.vehicle_number;
    vehicleStatusEl.textContent = data.vehicle.status.toUpperCase();
  }

  initMap(data.route ? data.route.waypoints : []);
  await pollLatestLocation();
}

function initMap(waypoints) {
  if (!map) {
    map = L.map("map").setView([13.0827, 80.2707], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
  }

  if (routePolyline) {
    map.removeLayer(routePolyline);
  }

  if (waypoints && waypoints.length > 0) {
    const latLngs = waypoints.map(w => [w.latitude, w.longitude]);
    routePolyline = L.polyline(latLngs, { color: "#3730a3", weight: 5, opacity: 0.8 }).addTo(map);
    map.fitBounds(routePolyline.getBounds(), { padding: [40, 40] });

    waypoints.forEach(wp => {
      L.circleMarker([wp.latitude, wp.longitude], {
        radius: 6,
        color: "#ef4444",
        fillColor: "#ffffff",
        fillOpacity: 1
      }).addTo(map).bindPopup(`<b>Stop:</b> ${wp.name}`);
    });
  }
}

async function pollLatestLocation() {
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/me/vehicle/location`, {
      headers: { "Authorization": `Bearer ${token}` }
    });

    if (!res.ok) return;
    const loc = await res.json();

    vehicleSpeedEl.textContent = `${loc.speed.toFixed(1)} km/h`;
    const dt = new Date(loc.timestamp);
    vehicleUpdatedEl.textContent = dt.toLocaleTimeString();

    const latLng = [loc.latitude, loc.longitude];

    if (!vehicleMarker) {
      const busIcon = L.divIcon({
        className: "custom-bus-icon",
        html: `<div style="background:#3730a3; color:white; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center; font-size:20px; box-shadow:0 0 10px rgba(55,48,163,0.5);">🚌</div>`,
        iconSize: [36, 36]
      });
      vehicleMarker = L.marker(latLng, { icon: busIcon }).addTo(map);
    } else {
      vehicleMarker.setLatLng(latLng);
    }
  } catch (_) {}
}

function startPolling() {
  if (pollingInterval) clearInterval(pollingInterval);
  pollingInterval = setInterval(pollLatestLocation, 3000);
}

// Security 403 Forbidden Authorization Test
testUnauthorizedBtn.addEventListener("click", async () => {
  securityResultEl.classList.remove("hidden");
  const targetVehicle = currentAssignedVehicleNumber === "BUS-001" ? "BUS-002" : "BUS-001";
  
  securityResultEl.innerHTML = `<span style="color:#64748b;">Sending GET /vehicles/${targetVehicle}/location with ${currentAssignedVehicleNumber}'s Bearer Token...</span>`;

  try {
    const res = await fetch(`${API_BASE}/vehicles/${targetVehicle}/location`, {
      headers: { "Authorization": `Bearer ${token}` }
    });

    const body = await res.json();

    if (res.status === 403) {
      securityResultEl.className = "security-result alert-danger";
      securityResultEl.innerHTML = `<strong>✅ 403 FORBIDDEN CONFIRMED:</strong><br>${body.detail}`;
    } else {
      securityResultEl.className = "security-result alert-danger";
      securityResultEl.innerHTML = `Unexpected status ${res.status}`;
    }
  } catch (err) {
    securityResultEl.innerHTML = `Error: ${err.message}`;
  }
});
