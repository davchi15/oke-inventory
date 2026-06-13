import time
import cv2
import numpy as np

# ============================================================
# BACKGROUND-REFERENCE FALLBACK
# Not used in the handheld kiosk flow — reserved for the
# place-down enrollment station (fixed camera, static scene).
# ============================================================
DIFF_THRESHOLD = 30      # per-pixel intensity difference to count as "changed"
MIN_BLOB_AREA = 800      # ignore specks/noise smaller than this (px)


def capture_background(cap, frames=15):
    """Average several frames of the empty scene as the reference."""
    acc = None
    captured = 0
    for _ in range(frames):
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        acc = gray if acc is None else acc + gray
        captured += 1
    if acc is None or captured == 0:
        return None
    return (acc / captured).astype(np.uint8)


def find_object_by_diff(frame, background, zone):
    """Box around whatever differs from the empty-scene reference,
    restricted to the zone. Returns (x1, y1, x2, y2) or None."""
    if background is None:
        return None
    zx1, zy1, zx2, zy2 = zone
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray, background)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)
    _, mask = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
    mask[:zy1, :] = 0
    mask[zy2:, :] = 0
    mask[:, :zx1] = 0
    mask[:, zx2:] = 0
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    biggest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(biggest) < MIN_BLOB_AREA:
        return None
    x, y, w, h = cv2.boundingRect(biggest)
    return (x, y, x + w, y + h)


# ============================================================
# BOX TRACKER — follows a confirmed box without needing YOLO
# to keep detecting the object. Prefers modern neural trackers
# (ViT, Nano), falls back to classical (MIL).
# ============================================================
class BoxTracker:

    def __init__(self):
        self.tracker = None
        self.box = None
        self.ok = False
        self.kind = None

    def _create(self):
        candidates = [
            ("ViT",  lambda: cv2.TrackerVit_create()),
            ("Nano", lambda: cv2.TrackerNano_create()),
            ("MIL",  lambda: cv2.TrackerMIL_create()),
            # CSRT variants, in case a future build restores them:
            ("CSRT-legacy", lambda: cv2.legacy.TrackerCSRT_create()),
            ("CSRT", lambda: cv2.TrackerCSRT_create()),
        ]
        for name, make in candidates:
            try:
                tracker = make()
                self.kind = name
                print(f"  Tracker: {name}")
                return tracker
            except (AttributeError, cv2.error):
                continue
        raise RuntimeError(
            "No usable tracker in this OpenCV build. "
            "Try: pip install opencv-contrib-python"
        )

    def start(self, frame, box):
        x1, y1, x2, y2 = box
        self.tracker = self._create()
        self.tracker.init(frame, (x1, y1, x2 - x1, y2 - y1))  # wants (x, y, w, h)
        self.box = box
        self.ok = True

    def update(self, frame):
        if self.tracker is None:
            self.ok = False
            return None
        ok, rect = self.tracker.update(frame)
        self.ok = ok
        if not ok:
            return None
        x, y, w, h = map(int, rect)
        self.box = (x, y, x + w, y + h)
        return self.box

    def stop(self):
        self.tracker = None
        self.box = None
        self.ok = False
        self.kind = None


# ============================================================
# OBJECT LOCK — three-state item selector for a
# person-in-frame kiosk scene
#
# searching -> candidate persists MIN_CANDIDATE_FRAMES -> pending
# pending   -> confirm() -> locked | reject() -> blacklist + searching
# locked    -> driven by BoxTracker in the enrollment loop
# ============================================================
def iou(box_a, box_b):
    """Intersection over union of two (x1, y1, x2, y2) boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


class ObjectLock:

    MIN_CANDIDATE_FRAMES = 5     # frames a candidate must survive before proposing
    BLACKLIST_IOU = 0.4          # overlap with a rejected box = "same thing"
    BLACKLIST_SECONDS = 6.0      # how long a rejection is remembered

    def __init__(self, frame_w, frame_h,
                 zone_fraction=0.5, iou_threshold=0.3, max_misses=15):
        self.frame_w, self.frame_h = frame_w, frame_h
        zw, zh = frame_w * zone_fraction, frame_h * zone_fraction
        self.zone = (int((frame_w - zw) / 2), int((frame_h - zh) / 2),
                     int((frame_w + zw) / 2), int((frame_h + zh) / 2))
        self.zone_center = ((self.zone[0] + self.zone[2]) / 2,
                            (self.zone[1] + self.zone[3]) / 2)
        self.iou_threshold = iou_threshold
        self.max_misses = max_misses

        self.state = "searching"
        self.box = None
        self.candidate_frames = 0
        self.misses = 0
        self.prev_center = None
        self.center_motion = 0.0
        self.blacklist = []          # list of (box, expiry_time)

    # ---------- internals ----------
    def _center(self, box):
        return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

    def _in_zone(self, box):
        cx, cy = self._center(box)
        zx1, zy1, zx2, zy2 = self.zone
        return zx1 <= cx <= zx2 and zy1 <= cy <= zy2

    def _blacklisted(self, box):
        now = time.time()
        self.blacklist = [(b, t) for b, t in self.blacklist if t > now]
        return any(iou(box, b) > self.BLACKLIST_IOU for b, _ in self.blacklist)

    def _score(self, box):
        """Area weighted by proximity to the zone center."""
        area = (box[2] - box[0]) * (box[3] - box[1])
        cx, cy = self._center(box)
        dist = np.hypot(cx - self.zone_center[0], cy - self.zone_center[1])
        max_dist = np.hypot(self.frame_w, self.frame_h) / 2
        return area * (1.0 - dist / max_dist)

    def _reset(self):
        self.state = "searching"
        self.box = None
        self.candidate_frames = 0
        self.misses = 0
        self.prev_center = None
        self.center_motion = 0.0

    # ---------- per-frame update (searching / pending only) ----------
    def update(self, boxes):
        if self.state == "searching":
            candidates = [b for b in boxes
                          if self._in_zone(b) and not self._blacklisted(b)]
            if not candidates:
                self.box = None
                self.candidate_frames = 0
                return
            best = max(candidates, key=self._score)
            if self.box is not None and iou(self.box, best) >= self.iou_threshold:
                self.candidate_frames += 1     # same thing, still there
            else:
                self.candidate_frames = 1      # new candidate — restart the clock
            self.box = best
            self.prev_center = self._center(best)
            if self.candidate_frames >= self.MIN_CANDIDATE_FRAMES:
                self.state = "pending"

        elif self.state == "pending":
            # keep following via IoU so the amber box tracks until confirmed
            best, best_iou = None, 0.0
            for b in boxes:
                score = iou(self.box, b)
                if score > best_iou:
                    best, best_iou = b, score
            if best is not None and best_iou >= self.iou_threshold:
                self.box = best
                self.prev_center = self._center(best)
                self.misses = 0
            else:
                self.misses += 1
                if self.misses > self.max_misses:
                    self._reset()

    # ---------- user actions ----------
    def confirm(self):
        if self.state == "pending":
            self.state = "locked"
            self.misses = 0

    def reject(self):
        """User says 'not that' — remember it, look for something else."""
        if self.box is not None:
            self.blacklist.append((self.box, time.time() + self.BLACKLIST_SECONDS))
        self._reset()

    def is_locked(self):
        return self.state == "locked"

    def is_pending(self):
        return self.state == "pending"