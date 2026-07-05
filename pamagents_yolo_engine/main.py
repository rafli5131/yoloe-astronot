import cv2
import numpy as np
import json
import os
import time
from datetime import datetime, timezone

from core.stream_reader import VideoStreamer
from core.inference_engine import YoloDetector
from core.data_models import ApdDetectionResult, ApdViolation

def has_high_vis_color(frame, person_box):
    px1, py1, px2, py2 = person_box
    
    # ensure bounds are within frame
    h, w = frame.shape[:2]
    px1 = max(0, px1)
    py1 = max(0, py1)
    px2 = min(w, px2)
    py2 = min(h, py2)
    
    if px2 <= px1 or py2 <= py1:
        return False
        
    person_crop = frame[py1:py2, px1:px2]
    
    # Convert to HSV to easily detect neon orange/yellow/green
    hsv = cv2.cvtColor(person_crop, cv2.COLOR_BGR2HSV)
    
    # Neon Yellow/Green bounds
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([45, 255, 255])
    
    # Bright Orange bounds
    lower_orange = np.array([5, 150, 150])
    upper_orange = np.array([20, 255, 255])
    
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
    
    mask = cv2.bitwise_or(mask_yellow, mask_orange)
    
    # Calculate ratio of high-vis pixels
    high_vis_ratio = cv2.countNonZero(mask) / (person_crop.shape[0] * person_crop.shape[1] + 1e-6)
    
    # If > 5% of person area is neon, they have a vest
    return high_vis_ratio > 0.05

def check_overlap(person_box, item_box):
    px1, py1, px2, py2 = person_box
    ix1, iy1, ix2, iy2 = item_box
    
    x_left = max(px1, ix1)
    y_top = max(py1, iy1)
    x_right = min(px2, ix2)
    y_bottom = min(py2, iy2)
    
    if x_right < x_left or y_bottom < y_top:
        return False
        
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    item_area = (ix2 - ix1) * (iy2 - iy1)
    
    # Calculate item center
    ix_center = ix1 + (ix2 - ix1) / 2
    iy_center = iy1 + (iy2 - iy1) / 2
    
    # Check if item center is inside person box
    center_inside = (px1 <= ix_center <= px2) and (py1 <= iy_center <= py2)
    
    # Be very lenient: either 10% overlap or center point is inside the person box
    return center_inside or (intersection_area / (item_area + 1e-6) > 0.1)

def load_config(config_path="config.json"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return json.load(f)

def main():
    print("Starting YOLO-E GPU Inference Engine...")
    
    # 1. Read config.json
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    cameras_config = config.get("cameras", [
        {
            "camera_id": config.get("camera_id", "CAM-PIT-A-01"),
            "video_source": config.get("video_source", 0)
        }
    ])
    
    conf_threshold = config.get("confidence_threshold", 0.5)
    target_fps = config.get("target_fps", 5)
    model_path = config.get("model_path", "weights/yolov8n.pt")
    required_items = config.get("required_items", {
        "helmet": ["helmet", "hat", "hard hat"],
        "vest": ["vest"],
        "shoe": ["shoe", "boot"]
    })

    # Ensure weights directory exists
    os.makedirs("weights", exist_ok=True)
    
    # 2. Initialize Models
    print(f"Loading YOLO Model from {model_path}...")
    try:
        detector = YoloDetector(model_path=model_path)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print(f"Initializing {len(cameras_config)} camera stream(s)...")
    streamers = []
    for cam in cameras_config:
        print(f"Connecting to {cam['camera_id']} ({cam['video_source']}) at {target_fps} FPS...")
        streamers.append({
            "id": cam["camera_id"],
            "streamer": VideoStreamer(source=cam["video_source"], target_fps=target_fps)
        })

    print("Inference loop started. Press Ctrl+C to stop.\n")

    # 3. Main Loop
    try:
        while True:
            for cam_data in streamers:
                camera_id = cam_data["id"]
                streamer = cam_data["streamer"]
                
                # Pull frame with integrated frame skipping
                frame = streamer.get_next_frame()
                if frame is None:
                    continue

                # Run detection
                raw_detections = detector.detect(frame, confidence_threshold=conf_threshold)

                # Separate detections into persons and APD items
                persons = []
                apd_items = []
                
                for d in raw_detections:
                    label = d["label"].lower()
                    if "person" in label or "worker" in label:
                        persons.append(d)
                    else:
                        for apd_type, keywords in required_items.items():
                            if any(k in label for k in keywords):
                                apd_items.append({"type": apd_type, "bbox": d["bbox_xyxy"]})
                                break

                violations = []
                
                for p in persons:
                    person_box = p["bbox_xyxy"]
                    found_apd = {apd_type: False for apd_type in required_items.keys()}
                    
                    for item in apd_items:
                        if check_overlap(person_box, item["bbox"]):
                            if item["type"] in found_apd:
                                found_apd[item["type"]] = True
                    
                    missing = [apd_type for apd_type, found in found_apd.items() if not found]
                    
                    # Fallback for vest/high-vis clothing if the model failed to detect it
                    if "vest" in missing and has_high_vis_color(frame, person_box):
                        missing.remove("vest")
                    
                    x1, y1, x2, y2 = person_box
                    
                    if missing:
                        violations.append(ApdViolation(
                            person_bbox=person_box,
                            missing_apd=missing
                        ))
                        # Draw red bounding box for violation
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        text = "Missing: " + ", ".join(missing)
                        cv2.putText(frame, text, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    else:
                        # Draw green bounding box for APD complete
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, "APD OK", (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Only output JSON if there are APD violations
                if len(violations) > 0:
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    result = ApdDetectionResult(
                        camera_id=camera_id,
                        timestamp=timestamp,
                        violations=violations
                    )

                    # Dump JSON as per contract
                    print(result.model_dump_json(indent=2))
                    
                    # HTTP POST webhook integration can be placed here

                # Live view display per camera
                window_name = f"APD Live View: {camera_id}"
                # Resize if needed to fit multiple windows on screen
                display_frame = cv2.resize(frame, (640, 360))
                cv2.imshow(window_name, display_frame)
                
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quit signal received (pressed 'q').")
                break

    except KeyboardInterrupt:
        print("\nShutdown signal received. Exiting...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        for cam_data in streamers:
            cam_data["streamer"].release()
        cv2.destroyAllWindows()
        print("Stream resources released.")

if __name__ == "__main__":
    main()
