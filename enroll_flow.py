import cv2
import numpy as np
import time
from ultralytics import YOLO
from camera import find_camera
from object_lock import ObjectLock, BoxTracker
from embeddings import get_embedding_from_array, model as clip_model
from embedding_store import create_embeddings_table, enroll_item
from db import create_table

# ============================================================
# TUNING
# ============================================================
TARGET_VIEWS = 8
DIVERSITY_THRESHOLD = 0.92    # keep a sweep frame only if max sim to kept views < this
SAMPLE_INTERVAL = 0.25        # seconds between embedding attempts during the sweep
STALL_SECONDS = 3.0           # no new view in this long -> show a coaching hint
DETECTION_CONFIDENCE = 0.30   # lowered: small items detect weakly
CROP_PADDING = 20             # px of context around the locked box
PERSON_CLASS = 0              # COCO class id for "person" — always excluded
MAX_BOX_FRACTION = 0.35       # boxes larger than this fraction of frame rejected
YOLO_IMGSZ = 960              # higher inference resolution for small objects

DEBUG = True                  # draw every raw YOLO detection + drop reason

# coaching hints cycle while the sweep is stalled — they name the viewpoints
# people most often miss (ends, top/bottom, tilt) rather than abstract axes
COACHING_HINTS = [
    "Try turning it a different way",
    "Show me the top and bottom",
    "Tilt it toward the camera",
    "Rotate it the other direction",
]

CATEGORIES = ["an electronic component", "a tool", "a kitchen item", "a book"]
CATEGORY_LABELS = {           # zero-shot prompt -> inventory category
    "an electronic component": "Electronics",
    "a tool": "Tools",
    "a kitchen item": "Other",
    "a book": "Other",
}

yolo = YOLO("yolov8s.pt")


# ============================================================
# HELPERS
# ============================================================
def detect_boxes(frame, debug_display=None):
    """YOLO boxes, excluding people and oversized boxes.
    If debug_display is passed, draws ALL raw detections (pre-filter) on it
    with a [DROP:...] tag explaining any that get filtered."""
    h, w = frame.shape[:2]
    frame_area = h * w
    results = yolo(frame, imgsz=YOLO_IMGSZ, verbose=False)
    boxes = []
    for b in results[0].boxes:
        x1, y1, x2, y2 = map(int, b.xyxy[0])
        cls_name = yolo.names[int(b.cls[0])]
        conf = float(b.conf[0])
        area_frac = (x2 - x1) * (y2 - y1) / frame_area

        if debug_display is not None:
            tag = f"{cls_name} {conf:.2f}"
            if int(b.cls[0]) == PERSON_CLASS:
                tag += " [DROP:person]"
            elif conf < DETECTION_CONFIDENCE:
                tag += " [DROP:conf]"
            elif area_frac > MAX_BOX_FRACTION:
                tag += f" [DROP:size {area_frac:.2f}]"
            cv2.rectangle(debug_display, (x1, y1), (x2, y2), (40, 40, 220), 1)
            cv2.putText(debug_display, tag, (x1, max(12, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 40, 220), 1)

        if int(b.cls[0]) == PERSON_CLASS:
            continue
        if conf < DETECTION_CONFIDENCE:
            continue
        if area_frac > MAX_BOX_FRACTION:
            continue
        boxes.append((x1, y1, x2, y2))
    return boxes


def diversity_check(new_vector, kept_vectors):
    """Returns (is_distinct, best_similarity_to_kept).
    A frame is distinct (worth keeping) if it's far enough from everything kept."""
    if not kept_vectors:
        return True, 0.0
    best = max(float(np.dot(new_vector, v)) for v in kept_vectors)
    return best <= DIVERSITY_THRESHOLD, best


def suggest_category(vector):
    """Zero-shot CLIP: compare the item embedding to category text embeddings."""
    best_prompt, best_score = None, -1.0
    for prompt in CATEGORIES:
        text_emb = clip_model.encode(prompt)
        text_emb = text_emb / np.linalg.norm(text_emb)
        score = float(np.dot(vector, text_emb))
        if score > best_score:
            best_prompt, best_score = prompt, score
    return CATEGORY_LABELS[best_prompt]


def padded_crop(frame, box, padding=CROP_PADDING):
    """Crop the locked box from the frame with padding, clamped to bounds."""
    x1, y1, x2, y2 = box
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1 - padding), max(0, y1 - padding)
    x2, y2 = min(w, x2 + padding), min(h, y2 + padding)
    return frame[y1:y2, x1:x2]


def draw_progress_ring(display, kept, target):
    """A filling arc in the top-right: progress = distinct views collected."""
    h, w = display.shape[:2]
    center = (w - 55, 55)
    radius = 34
    cv2.circle(display, center, radius, (90, 90, 90), 5)          # background ring
    if kept > 0:
        end_angle = -90 + int(360 * min(kept, target) / target)  # fill from top, CW
        cv2.ellipse(display, center, (radius, radius), 0, -90, end_angle,
                    (80, 179, 47), 5)
    text = f"{kept}/{target}"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.putText(display, text, (center[0] - tw // 2, center[1] + th // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


# ============================================================
# MAIN ENROLLMENT LOOP
# ============================================================
def run_enrollment():
    create_table()
    create_embeddings_table()

    index, backend = find_camera()
    if index == -1:
        return
    cap = cv2.VideoCapture(index, backend)

    ret, first = cap.read()
    if not ret:
        print("  Error: could not read from camera.")
        cap.release()
        return
    lock = ObjectLock(first.shape[1], first.shape[0])
    tracker = BoxTracker()

    kept_vectors = []             # distinct embeddings collected during the sweep
    last_sample = 0.0             # throttle for embedding attempts
    last_kept_time = 0.0          # when we last kept a distinct view (stall clock)
    flash_until = 0.0             # brief green "new view" flash timer
    status = "Show me the item in the center"

    print("\nEnrollment started — present the item, confirm it, then slowly")
    print("rotate it to show every side until the ring fills.")
    print("Y = confirm the highlighted item   N = not that   Q = cancel")
    if DEBUG:
        print("DEBUG on — red boxes are raw YOLO detections, tagged with drop reasons.\n")

    while len(kept_vectors) < TARGET_VIEWS:
        ret, frame = cap.read()
        if not ret:
            print("  Error: could not read frame.")
            break

        display = frame.copy()

        if lock.is_locked():
            # --- TRACKER drives the box; YOLO is off during the sweep ---
            tracked = tracker.update(frame)
            if tracked is None:
                status = "Lost the item — show it again"
                tracker.stop()
                lock._reset()
            else:
                lock.box = tracked

                # ---- sweep capture: throttled embed + diversity check ----
                now = time.time()
                if now - last_sample >= SAMPLE_INTERVAL:
                    last_sample = now
                    crop = padded_crop(frame, lock.box)
                    if crop.size > 0:
                        vector = get_embedding_from_array(crop)
                        distinct, similarity = diversity_check(vector, kept_vectors)
                        if distinct:
                            kept_vectors.append(vector)
                            flash_until = now + 0.4
                            last_kept_time = now
                            print(f"  Kept view {len(kept_vectors)}/{TARGET_VIEWS}"
                                  f" (max sim to kept: {similarity:.3f})")

                # ---- status: flash > first-view > stall-coaching > default ----
                if time.time() < flash_until:
                    status = f"New angle! ({len(kept_vectors)}/{TARGET_VIEWS})"
                elif len(kept_vectors) == 0:
                    status = "Slowly turn the item to show every side"
                else:
                    stalled = time.time() - last_kept_time > STALL_SECONDS
                    if stalled:
                        hint_index = int(
                            (time.time() - last_kept_time) / STALL_SECONDS
                        ) % len(COACHING_HINTS)
                        status = COACHING_HINTS[hint_index]
                    else:
                        status = "Keep turning — show me a new side"
        else:
            # --- searching / pending: YOLO detection feeds the lock ---
            boxes = detect_boxes(frame, debug_display=display if DEBUG else None)
            lock.update(boxes)
            if lock.state == "searching":
                status = "Show me the item in the center"
            elif lock.is_pending():
                status = "Is this the item?  Y = yes   N = no"

        # ---- overlay ----
        zx1, zy1, zx2, zy2 = lock.zone
        cv2.rectangle(display, (zx1, zy1), (zx2, zy2), (90, 90, 90), 1)
        if lock.box is not None and lock.state != "searching":
            if lock.is_pending():
                color = (0, 191, 255)                       # amber: awaiting confirm
            elif time.time() < flash_until:
                color = (80, 230, 120)                       # bright flash on new view
            else:
                color = (80, 179, 47)                        # green: locked + sweeping
            x1, y1, x2, y2 = lock.box
            cv2.rectangle(display, (x1, y1), (x2, y2), color, 3)
        cv2.putText(display, status, (10, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 179, 47), 2)

        if lock.is_locked():
            draw_progress_ring(display, len(kept_vectors), TARGET_VIEWS)

        cv2.imshow("Oke Works — Enrollment", display)

        # ---- keys: Y confirm, N reject, Q cancel ----
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("Enrollment cancelled.")
            tracker.stop()
            cap.release()
            cv2.destroyAllWindows()
            return
        elif key == ord("y") and lock.is_pending():
            lock.confirm()
            tracker.start(frame, lock.box)   # hand confirmed box to the tracker
            now = time.time()
            last_sample = now                # small grace before first sample
            last_kept_time = now             # start the stall clock
            status = "Locked on — slowly turn the item"
        elif key == ord("n") and lock.state in ("pending", "locked"):
            lock.reject()
            tracker.stop()
            kept_vectors = []                # rejecting the object resets the sweep
            status = "Okay — show me the item again"

    cap.release()
    cv2.destroyAllWindows()
    tracker.stop()

    if len(kept_vectors) < TARGET_VIEWS:
        print("Enrollment did not complete.")
        return

    # ---- naming (terminal version — kiosk NAMING screen lands Day 14) ----
    print(f"\nAll {TARGET_VIEWS} views captured!")
    suggested = suggest_category(kept_vectors[0])
    name = input("  Item name: ").strip()
    category = input(f"  Category [{suggested}]: ").strip().title() or suggested

    enroll_item(name, category, kept_vectors)
    print(f"\nDone — '{name}' ({category}) is now in the catalog.")


if __name__ == "__main__":
    run_enrollment()