import base64
from collections import defaultdict
from datetime import datetime
import time
from typing import Callable
import uuid

try:
    import cv2
except Exception:
    cv2 = None

try:
    import numpy as np
except Exception:
    np = None


VIDEO_ANALYSIS_STATE = defaultdict(dict)
VIDEO_ANALYSIS_CONTROL = defaultdict(dict)
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v"}


def _utcnow_iso():
    return datetime.utcnow().isoformat()


def is_allowed_video_filename(filename):
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def default_video_state(event_id):
    return {
        "event_id": event_id,
        "status": "idle",
        "source_type": None,
        "source_mode": None,
        "source_label": None,
        "progress": 0,
        "analyzed_frames": 0,
        "latest_people_count": 0,
        "average_people_count": 0,
        "peak_people_count": 0,
        "result_available": False,
        "last_result": None,
        "heatmap_points": [],
        "hotspots": [],
        "preview_frame": None,
        "started_at": None,
        "finished_at": None,
        "reconnect_attempts": 0,
        "updated_at": None,
        "message": "No CCTV/video source is running yet.",
        "error": None,
    }


def get_video_analysis_state(event_id):
    state = VIDEO_ANALYSIS_STATE.get(event_id)
    if not state:
        return default_video_state(event_id)
    merged = default_video_state(event_id)
    merged.update(state)
    return merged


def set_video_analysis_state(event_id, state):
    VIDEO_ANALYSIS_STATE[event_id] = state
    return VIDEO_ANALYSIS_STATE[event_id]


def reset_video_analysis_control(event_id, job_id=None):
    VIDEO_ANALYSIS_CONTROL[event_id] = {
        "stop_requested": False,
        "job_id": job_id or str(uuid.uuid4()),
    }
    return VIDEO_ANALYSIS_CONTROL[event_id]


def request_video_stop(event_id):
    control = VIDEO_ANALYSIS_CONTROL.get(event_id) or {}
    control["stop_requested"] = True
    VIDEO_ANALYSIS_CONTROL[event_id] = control
    return control


def is_stop_requested(event_id, job_id=None):
    control = VIDEO_ANALYSIS_CONTROL.get(event_id) or {}
    if job_id and control.get("job_id") and control.get("job_id") != job_id:
        return True
    return control.get("stop_requested", False)


def _frame_to_data_url(frame):
    if cv2 is None:
        return None
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    if not ok:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buffer.tobytes()).decode("ascii")


def _resize_frame(frame, target_width=960):
    height, width = frame.shape[:2]
    if width <= target_width:
        return frame
    ratio = target_width / float(width)
    target_height = int(height * ratio)
    return cv2.resize(frame, (target_width, target_height))


def _build_heatmap_points(grid):
    if np is None:
        return []
    max_value = float(grid.max()) if grid.size else 0.0
    if max_value <= 0:
        return []
    points = []
    rows, cols = grid.shape
    for row in range(rows):
        for col in range(cols):
            value = float(grid[row, col])
            if value <= 0:
                continue
            points.append(
                {
                    "x": round((col + 0.5) / cols, 4),
                    "y": round((row + 0.5) / rows, 4),
                    "intensity": round(value / max_value, 4),
                    "count": round(value, 2),
                }
            )
    return points


def _extract_hotspots(grid, limit=5):
    if np is None or grid.size == 0 or float(grid.max()) <= 0:
        return []
    rows, cols = grid.shape
    flat_indices = np.argsort(grid, axis=None)[::-1]
    hotspots = []
    for flat_index in flat_indices[:limit]:
        row, col = np.unravel_index(flat_index, grid.shape)
        value = float(grid[row, col])
        if value <= 0:
            continue
        hotspots.append(
            {
                "label": f"Zone {len(hotspots) + 1}",
                "x": round((col + 0.5) / cols, 4),
                "y": round((row + 0.5) / rows, 4),
                "intensity": round(value / float(grid.max()), 4),
                "count": round(value, 2),
            }
        )
    return hotspots


def _result_summary(state):
    return {
        "latest_people_count": state.get("latest_people_count", 0),
        "average_people_count": state.get("average_people_count", 0),
        "peak_people_count": state.get("peak_people_count", 0),
        "analyzed_frames": state.get("analyzed_frames", 0),
        "hotspots_count": len(state.get("hotspots") or []),
        "updated_at": state.get("updated_at"),
    }


def _is_live_mode(source_mode, source_type):
    return source_mode == "live" or source_type in {"cctv", "live_stream"}


def _open_capture(source):
    if cv2 is None:
        return None
    capture = cv2.VideoCapture(source)
    if capture.isOpened():
        return capture
    capture.release()
    return None


def _emit_state(event_id, source_type, source_mode, source_label, emit_update, state_patch):
    state = get_video_analysis_state(event_id)
    state.update(state_patch)
    state["event_id"] = event_id
    state["source_type"] = source_type
    state["source_mode"] = source_mode
    state["source_label"] = source_label
    state["updated_at"] = _utcnow_iso()
    if state.get("analyzed_frames", 0) > 0:
        state["result_available"] = True
        state["last_result"] = _result_summary(state)
    set_video_analysis_state(event_id, state)
    emit_update(state)


def analyze_video_source(event_id, source, source_type, source_mode, source_label, emit_update: Callable[[dict], None], job_id=None):
    if cv2 is None or np is None:
        _emit_state(
            event_id,
            source_type,
            source_mode,
            source_label,
            emit_update,
            {
                "status": "error",
                "error": "OpenCV dependencies are not installed. Install opencv-python-headless and numpy.",
                "message": "Video AI could not start because computer vision dependencies are missing.",
            },
        )
        return

    live_mode = _is_live_mode(source_mode, source_type)
    cap = _open_capture(source)
    if cap is None and not live_mode:
        _emit_state(
            event_id,
            source_type,
            source_mode,
            source_label,
            emit_update,
            {
                "status": "error",
                "error": "Unable to open the provided video source.",
                "message": "The CCTV/video source could not be opened.",
            },
        )
        return

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    grid_rows = 18
    grid_cols = 32
    heat_grid = np.zeros((grid_rows, grid_cols), dtype=np.float32)
    fps = cap.get(cv2.CAP_PROP_FPS) or 10
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    sample_every = max(int(round(fps / 2.0)), 1)

    frame_index = 0
    analyzed_frames = 0
    total_people = 0
    peak_people = 0
    reconnect_attempts = 0

    _emit_state(
        event_id,
        source_type,
        source_mode,
        source_label,
        emit_update,
        {
            "status": "processing",
            "progress": 0,
            "started_at": _utcnow_iso(),
            "finished_at": None,
            "reconnect_attempts": 0,
            "message": "Video AI has started analyzing the CCTV/video source.",
            "error": None,
        },
    )

    try:
        while True:
            if is_stop_requested(event_id, job_id):
                _emit_state(
                    event_id,
                    source_type,
                    source_mode,
                    source_label,
                    emit_update,
                    {
                        "status": "stopped",
                        "progress": 100 if not live_mode else 0,
                        "finished_at": _utcnow_iso(),
                        "message": "Video monitoring stopped. Latest analyzed results remain available.",
                        "error": None,
                    },
                )
                break

            if cap is None or not cap.isOpened():
                if not live_mode:
                    break
                reconnect_attempts += 1
                _emit_state(
                    event_id,
                    source_type,
                    source_mode,
                    source_label,
                    emit_update,
                    {
                        "status": "reconnecting",
                        "reconnect_attempts": reconnect_attempts,
                        "message": "Trying to reconnect to the live CCTV camera feed...",
                        "error": None,
                    },
                )
                time.sleep(2)
                cap = _open_capture(source)
                continue

            ok, frame = cap.read()
            if not ok:
                if not live_mode:
                    break
                if cap:
                    cap.release()
                cap = None
                continue

            frame_index += 1
            if frame_index % sample_every != 0:
                continue

            frame = _resize_frame(frame)
            analyzed_frames += 1
            if live_mode:
                heat_grid *= 0.94
            rects, _weights = hog.detectMultiScale(
                frame,
                winStride=(6, 6),
                padding=(8, 8),
                scale=1.05,
            )

            people_count = len(rects)
            total_people += people_count
            peak_people = max(peak_people, people_count)

            frame_height, frame_width = frame.shape[:2]
            preview_frame = frame.copy()
            for (x, y, w, h) in rects:
                center_x = min(max((x + (w / 2)) / max(frame_width, 1), 0), 0.9999)
                center_y = min(max((y + (h * 0.8)) / max(frame_height, 1), 0), 0.9999)
                grid_x = min(int(center_x * grid_cols), grid_cols - 1)
                grid_y = min(int(center_y * grid_rows), grid_rows - 1)
                heat_grid[grid_y, grid_x] += 1

                cv2.rectangle(preview_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(
                    preview_frame,
                    (int(center_x * frame_width), int(center_y * frame_height)),
                    4,
                    (0, 0, 255),
                    -1,
                )

            should_emit = analyzed_frames == 1 or analyzed_frames % 3 == 0
            if should_emit:
                progress = 0
                if total_frames > 0:
                    progress = round(min((frame_index / total_frames) * 100, 100), 1)
                _emit_state(
                    event_id,
                    source_type,
                    source_mode,
                    source_label,
                    emit_update,
                    {
                        "status": "processing",
                        "progress": 0 if live_mode else progress,
                        "analyzed_frames": analyzed_frames,
                        "latest_people_count": people_count,
                        "average_people_count": round(total_people / max(analyzed_frames, 1), 1),
                        "peak_people_count": peak_people,
                        "reconnect_attempts": reconnect_attempts,
                        "heatmap_points": _build_heatmap_points(heat_grid),
                        "hotspots": _extract_hotspots(heat_grid),
                        "preview_frame": _frame_to_data_url(preview_frame),
                        "message": (
                            "Live CCTV camera is connected and AI is updating detections in real time."
                            if live_mode
                            else "Uploaded video is being analyzed and the heatmap is updating."
                        ),
                        "error": None,
                    },
                )

            if live_mode:
                time.sleep(0.02)

        if is_stop_requested(event_id, job_id):
            return

        final_message = (
            "Uploaded video analysis completed successfully."
            if analyzed_frames
            else "Video opened, but no analyzable frames were sampled."
        )
        _emit_state(
            event_id,
            source_type,
            source_mode,
            source_label,
            emit_update,
            {
                "status": "completed" if not live_mode else "stopped",
                "progress": 100 if not live_mode else 0,
                "analyzed_frames": analyzed_frames,
                "latest_people_count": 0 if not analyzed_frames else get_video_analysis_state(event_id).get("latest_people_count", 0),
                "average_people_count": round(total_people / max(analyzed_frames, 1), 1) if analyzed_frames else 0,
                "peak_people_count": peak_people,
                "heatmap_points": _build_heatmap_points(heat_grid),
                "hotspots": _extract_hotspots(heat_grid),
                "finished_at": _utcnow_iso(),
                "message": (
                    "Live CCTV camera feed ended. Latest analyzed results remain available."
                    if live_mode
                    else final_message
                ),
                "error": None,
            },
        )
    except Exception as exc:
        _emit_state(
            event_id,
            source_type,
            source_mode,
            source_label,
            emit_update,
            {
                "status": "error",
                "finished_at": _utcnow_iso(),
                "error": str(exc),
                "message": "Video AI stopped because the source raised an error during processing.",
            },
        )
    finally:
        if cap:
            cap.release()
