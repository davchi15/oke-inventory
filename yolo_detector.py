from ultralytics import YOLO
import cv2
import time
from camera import find_camera
from db import check_in, check_out, get_all_items
from item_map import ITEM_MAP
from enums import Action

MODEL_PATH = "yolov8s.pt"
CONFIDENCE_THRESHOLD = 0.75  # only act on detections above this confidence

def load_model():
    print("Loading YOLOv8 model...")
    model = YOLO(MODEL_PATH)
    print("Model ready.")
    return model

def get_inventory_names():
    items = get_all_items()
    return {item.name.lower() for item in items}

def detect_and_act(model):
    index, backend = find_camera()
    if index == -1:
        print("  No camera found.")
        return

    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        print("  Error: Could not open camera.")
        return

    print("\nDetection active — press Q to quit.")
    print("When an item is detected, press I to check in or O to check out.\n")

    last_detection = None  # tracks the most recently detected inventory item

    while True:
        ret, frame = cap.read()
        if not ret:
            print("  Error: Could not read frame.")
            break

        results = model(frame, verbose=False)
        annotated = results[0].plot()

        detected_item = None

        for box in results[0].boxes:
            confidence = float(box.conf[0])
            if confidence < CONFIDENCE_THRESHOLD:
                continue

            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            # check if this YOLO class maps to an inventory item
            if class_name in ITEM_MAP:
                inventory_name = ITEM_MAP[class_name]
                detected_item = inventory_name

                # overlay item name and confidence on the frame
                label = f"Inventory: {inventory_name} ({confidence:.0%})"
                cv2.putText(annotated, label, (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 100), 2)
                cv2.putText(annotated, "Press I = Check In  |  O = Check Out",
                            (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                break  # act on the highest confidence detection only

        if detected_item:
            last_detection = detected_item
        
        cv2.imshow("Oke Inventory — Detection", annotated)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Closing detection feed.")
            break

        elif key == ord("i"):
            if last_detection:
                print(f"\n  Checking in: {last_detection}")
                check_in(last_detection)
                last_detection = None
            else:
                print("  No inventory item detected yet — hold an item up to the camera.")

        elif key == ord("o"):
            if last_detection:
                print(f"\n  Checking out: {last_detection}")
                check_out(last_detection)
                last_detection = None
            else:
                print("  No inventory item detected yet — hold an item up to the camera.")

if __name__ == "__main__":
    model = load_model()
    detect_and_act(model)