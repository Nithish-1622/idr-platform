# Frontend Integration Guide: Sri Eshwar College Demonstration Scenario

This document outlines the details of the newly added **Sri Eshwar College — GPS & Internet Outage** demonstration scenario and how the frontend application should interact with it.

## 1. Overview
A new simulation preset has been added to the backend engine to demonstrate a real-world edge case: navigating a vehicle along a real road, experiencing a complete GPS and Internet outage midway, and recovering gracefully using the onboard Deep IDR Machine Learning model.

- **Scenario ID:** `sri_eshwar_outage`
- **Name:** Sri Eshwar College — GPS & Internet Outage
- **Duration:** 360 seconds
- **Starting Location:** Sri Eshwar College (10.8286° N, 77.0605° E)

## 2. API Integration (Zero Code Changes Required)
**No changes are required in the frontend application code to support this scenario.** 

Because the backend API was designed to be fully dynamic, the new scenario automatically registers itself in the preset registry.

### Fetching the Scenario
When the frontend fetches the list of available presets to populate the UI dropdown, the new scenario will appear automatically in the response payload.

**Endpoint:** `GET /api/v1/simulations/presets/`

**Expected Snippet in Response:**
```json
{
  "preset_id": "sri_eshwar_outage",
  "name": "Sri Eshwar College — GPS & Internet Outage",
  "description": "Vehicle traveling from Sri Eshwar College on a real road. GPS + Internet connection lost mid-route for 56 seconds (from t=144s to t=200s). During outage, ML dead reckoning takes over.",
  "duration_seconds": 360.0,
  "movement_mode": "WAYPOINT_ROUTE",
  "seed": 1024
}
```

### Triggering the Simulation
To execute the simulation, the frontend simply sends a standard `POST` request just as it would for any other preset scenario.

**Endpoint:** `POST /api/v1/simulations/`

**Request Body:**
```json
{
  "preset_id": "sri_eshwar_outage",
  "seed": 1024,
  "duration_seconds": 360.0
}
```

## 3. Expected UI Behavior & Visualizations
When running this simulation on the frontend map interface, expect the following timeline of events:

1. **Start ($t=0s$ to $t=144s$):** 
   - The vehicle spawns at Sri Eshwar College.
   - The UI should display the vehicle moving smoothly along the road towards Kinathukadavu.
   - Both GPS and Internet status indicators (if present) should show as 🟢 **ONLINE/AVAILABLE**.

2. **The Outage ($t=144s$ to $t=200s$):**
   - At exactly 144 seconds, the simulation will trigger a `GNSSOutage`.
   - The UI should indicate that the GPS and Internet connection are 🔴 **OFFLINE**.
   - **Crucial Demo Feature:** The vehicle *will not stop moving*. The frontend map will continue to receive position updates because the Deep IDR ML model seamlessly takes over using purely IMU data.

3. **Recovery ($t=200s$ to $t=360s$):**
   - At 200 seconds, the outage concludes. 
   - GPS and Internet status return to 🟢 **ONLINE**.
   - The frontend should visualize the correction as the estimated dead-reckoning trajectory merges back with the restored true GPS trajectory until the vehicle reaches its destination.
