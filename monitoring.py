from collections import defaultdict, deque
from datetime import datetime


MONITORING_HISTORY = defaultdict(lambda: deque(maxlen=24))


def _iso_timestamp(value):
    return value.isoformat() if value else None


def get_zone_status(capacity_percentage):
    if capacity_percentage >= 100:
        return "critical", "Critical"
    if capacity_percentage >= 85:
        return "crowded", "Crowded"
    if capacity_percentage >= 60:
        return "busy", "Busy"
    return "normal", "Normal"


def build_monitoring_payload(event, zones, active_attendees, recent_checkins, video_analysis=None):
    now = datetime.utcnow()
    total_max_capacity = sum((zone.max_capacity or 0) for zone in zones)
    total_current_capacity = sum((zone.current_capacity or 0) for zone in zones)
    overall_capacity_percentage = (
        (total_current_capacity / total_max_capacity) * 100 if total_max_capacity else 0
    )

    zone_summaries = []
    crowded_zones = 0
    critical_zones = 0
    near_capacity_zones = 0
    max_zone_load = 0

    for zone in zones:
        current_capacity = zone.current_capacity or 0
        max_capacity = zone.max_capacity or 0
        capacity_percentage = zone.capacity_percentage
        status_key, status_label = get_zone_status(capacity_percentage)

        if status_key == "crowded":
            crowded_zones += 1
        if status_key == "critical":
            critical_zones += 1
        if capacity_percentage >= 80:
            near_capacity_zones += 1

        max_zone_load = max(max_zone_load, current_capacity)
        zone_summaries.append(
            {
                "id": zone.id,
                "name": zone.name,
                "current_capacity": current_capacity,
                "max_capacity": max_capacity,
                "capacity_percentage": round(capacity_percentage, 1),
                "status": status_key,
                "status_label": status_label,
                "description": zone.description or "",
            }
        )

    previous_snapshot = MONITORING_HISTORY[event.id][-1] if MONITORING_HISTORY[event.id] else None
    previous_occupancy = previous_snapshot["overall_capacity_percentage"] if previous_snapshot else 0
    occupancy_delta = round(overall_capacity_percentage - previous_occupancy, 1)

    if occupancy_delta >= 5:
        trend = "rising"
    elif occupancy_delta <= -5:
        trend = "falling"
    else:
        trend = "stable"

    concentration_index = (
        max_zone_load / total_current_capacity if total_current_capacity else 0
    )
    recent_flow_score = min(recent_checkins / 25, 1)
    zone_pressure_score = min(near_capacity_zones / max(len(zones), 1), 1)
    concentration_score = min(concentration_index, 1)
    occupancy_score = min(overall_capacity_percentage / 100, 1)
    video_analysis = video_analysis or {}
    video_people = (
        video_analysis.get("latest_people_count")
        or video_analysis.get("average_people_count")
        or 0
    )
    video_hotspots = len(video_analysis.get("hotspots") or [])
    video_density_score = min(video_people / 25, 1)
    video_hotspot_score = min(video_hotspots / 5, 1)

    hours_to_event = None
    if event.date_time:
        hours_to_event = (event.date_time - now).total_seconds() / 3600

    timing_pressure = 0
    if hours_to_event is not None:
        if -4 <= hours_to_event <= 2:
            timing_pressure = 1
        elif 2 < hours_to_event <= 8:
            timing_pressure = 0.6
        elif -12 <= hours_to_event < -4:
            timing_pressure = 0.4

    risk_score = round(
        min(
            100,
            (occupancy_score * 45)
            + (zone_pressure_score * 25)
            + (concentration_score * 15)
            + (recent_flow_score * 10)
            + (video_density_score * 12)
            + (video_hotspot_score * 8)
            + (timing_pressure * 5),
        )
    )

    if critical_zones > 0 or overall_capacity_percentage >= 100 or risk_score >= 85:
        risk_level = "Critical"
        crowd_state = "Critical"
    elif crowded_zones > 0 or overall_capacity_percentage >= 85 or risk_score >= 65:
        risk_level = "High"
        crowd_state = "Crowded"
    elif overall_capacity_percentage >= 60 or risk_score >= 40:
        risk_level = "Moderate"
        crowd_state = "Busy"
    else:
        risk_level = "Low"
        crowd_state = "Normal"

    likely_causes = []
    recommendations = []

    if not zones:
        likely_causes.append("No monitoring zones are configured for this event yet.")
        recommendations.append("Create zones first so CrowdSafe can classify crowd pressure accurately.")

    if near_capacity_zones:
        likely_causes.append("One or more zones are close to their configured capacity.")
        recommendations.append("Redirect attendees toward lower-density zones and slow new entries into hot zones.")

    if critical_zones:
        likely_causes.append("At least one zone is over safe capacity and requires immediate action.")
        recommendations.append("Trigger on-ground intervention and open overflow or alternate movement routes now.")

    if concentration_index >= 0.55 and total_current_capacity:
        likely_causes.append("Crowd distribution is uneven, with too many attendees concentrated in one area.")
        recommendations.append("Use signage, staff, or barriers to spread people across available space.")

    if recent_checkins >= 8:
        likely_causes.append("Recent check-ins show a rapid inflow, which may create sudden surges.")
        recommendations.append("Temporarily meter admissions and stage arrivals in smaller batches.")

    if video_analysis.get("status") in {"processing", "completed"} and video_hotspots >= 2:
        likely_causes.append("CCTV analysis detected repeated crowd hotspots in the camera field of view.")
        recommendations.append("Deploy stewards or barriers at the highlighted hotspots and monitor camera updates closely.")

    if video_analysis.get("status") in {"processing", "completed"} and video_people >= 12:
        likely_causes.append("Video AI is detecting sustained person density in the monitored feed.")
        recommendations.append("Reduce inflow toward the monitored corridor and open alternate circulation paths.")

    if video_analysis.get("status") == "error" and video_analysis.get("error"):
        likely_causes.append("CCTV analysis is unavailable because the current video source could not be processed.")
        recommendations.append("Retry with a supported video file or verify the live stream URL is reachable.")

    if hours_to_event is not None and -2 <= hours_to_event <= 2:
        likely_causes.append("The event schedule window suggests a natural crowd surge around the venue.")
        recommendations.append("Keep response staff near entrances, choke points, and stage-adjacent zones.")

    if not likely_causes:
        likely_causes.append("Crowd flow and zone utilization are currently within expected operating limits.")
        recommendations.append("Continue monitoring and keep staff positioned for quick response.")

    summary = (
        f"{crowd_state} conditions with {total_current_capacity} active attendees across "
        f"{len(zones)} zones at {overall_capacity_percentage:.1f}% total occupancy."
    )

    snapshot = {
        "timestamp": _iso_timestamp(now),
        "overall_capacity_percentage": round(overall_capacity_percentage, 1),
        "risk_score": risk_score,
        "active_attendees": active_attendees,
        "crowded_zones": crowded_zones,
        "critical_zones": critical_zones,
    }
    MONITORING_HISTORY[event.id].append(snapshot)

    history = list(MONITORING_HISTORY[event.id])

    return {
        "event_id": event.id,
        "event_name": event.name,
        "timestamp": snapshot["timestamp"],
        "summary": summary,
        "crowd_state": crowd_state,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "overall_capacity_percentage": round(overall_capacity_percentage, 1),
        "active_attendees": active_attendees,
        "recent_checkins": recent_checkins,
        "near_capacity_zones": near_capacity_zones,
        "crowded_zones": crowded_zones,
        "critical_zones": critical_zones,
        "trend": trend,
        "occupancy_delta": occupancy_delta,
        "likely_causes": likely_causes[:4],
        "recommendations": recommendations[:4],
        "zones": zone_summaries,
        "history": history,
        "model": {
            "name": "Hybrid Crowd Risk Inference",
            "type": "Tabular real-time event risk scoring",
            "features": [
                "zone occupancy",
                "crowd concentration",
                "recent inflow",
                "event timing pressure",
                "cctv person detections",
                "heatmap hotspots",
            ],
        },
        "video_analysis": video_analysis,
    }
