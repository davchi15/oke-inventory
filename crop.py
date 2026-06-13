from ultralytics import YOLO
import cv2

model = YOLO("yolov8s.pt")

def crop_main_object(image_path, output_path, padding=20):
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"  Could not load {image_path}")
        return None

    results = model(frame, verbose=False)
    boxes = results[0].boxes

    if len(boxes) == 0:
        print(f"  No object found in {image_path} — using full image")
        cv2.imwrite(output_path, frame)
        return output_path

    # take the highest-confidence box, ignore what class it thinks it is
    best = max(boxes, key=lambda b: float(b.conf[0]))
    x1, y1, x2, y2 = map(int, best.xyxy[0])

    # add padding, clamped to image bounds
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1 - padding), max(0, y1 - padding)
    x2, y2 = min(w, x2 + padding), min(h, y2 + padding)

    crop = frame[y1:y2, x1:x2]
    cv2.imwrite(output_path, crop)
    print(f"  Cropped {image_path} → {output_path} ({x2-x1}x{y2-y1})")
    return output_path

def crop_frame(frame, padding=20):
    """Crop the main object from an in-memory frame.
    Returns (cropped_frame, box) or (None, None) if nothing found."""
    results = model(frame, verbose=False)
    boxes = results[0].boxes
    if len(boxes) == 0:
        return None, None

    best = max(boxes, key=lambda b: float(b.conf[0]))
    x1, y1, x2, y2 = map(int, best.xyxy[0])
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1 - padding), max(0, y1 - padding)
    x2, y2 = min(w, x2 + padding), min(h, y2 + padding)
    return frame[y1:y2, x1:x2], (x1, y1, x2, y2)