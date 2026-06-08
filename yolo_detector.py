from ultralytics import YOLO
import cv2
import time

MODEL_PATH = "yolov8s.pt"  # nano model — fastest, smallest, best for development

def load_model():
    print("Loading YOLOv8 model...")
    model = YOLO(MODEL_PATH)  # downloads automatically on first run
    print("Model ready.")
    return model

def detect_image(model, image_path="scan.jpg"):
    print(f"\nRunning detection on {image_path}...")
    frame = cv2.imread(image_path)

    if frame is None:
        print(f"  Error: Could not load image at '{image_path}'")
        return

    results = model(frame)

    print(f"\n  Detections:")
    if len(results[0].boxes) == 0:
        print("  No objects detected.")
        return

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        class_name = model.names[class_id]
        confidence = float(box.conf[0])
        print(f"  {class_name} — confidence: {confidence:.0%}")

def detect_live(model):
    from camera import find_camera

    index, backend = find_camera()
    if index == -1:
        print("  No camera found.")
        return

    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        print("  Error: Could not open camera.")
        return

    print("\nLive detection running — press Q to quit, S to save snapshot.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("  Error: Could not read frame.")
            break

        results = model(frame, verbose=False)
        annotated = results[0].plot()  # draws bounding boxes and labels on the frame

        cv2.imshow("Oke Inventory — YOLOv8 Detection", annotated)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Closing detection feed.")
            break
        elif key == ord("s"):
            cv2.imwrite("scan.jpg", frame)
            print("  Snapshot saved — scan.jpg")
            detect_image(model, "scan.jpg")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    model = load_model()
    detect_live(model)