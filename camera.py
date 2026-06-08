import cv2
import time
BACKENDS = [
    ("V4L2", cv2.CAP_V4L2),    # Linux / Raspberry Pi
    ("MSMF", cv2.CAP_MSMF),    # Windows
    ("DSHOW", cv2.CAP_DSHOW),  # Windows fallback
    ("ANY", cv2.CAP_ANY),      # last resort
]

def find_camera(max_index=3):
    print("Searching for available cameras...\n")
    for backend_name, backend in BACKENDS:
        print(f"  Trying backend: {backend_name}")
        for index in range(max_index):
            cap = cv2.VideoCapture(index, backend)
            if cap.isOpened():
                time.sleep(1)
                ret, frame = cap.read()
                if ret:
                    print(f"  Found camera — index {index}, backend {backend_name}, resolution: {frame.shape[1]}x{frame.shape[0]}")
                    cap.release()
                    return index, backend
                cap.release()
        print(f"  No camera found with {backend_name}\n")
    print("No camera found across all backends.")
    return -1, None

def inspect_image(path="scan.jpg"):
    frame = cv2.imread(path)
    if frame is None:
        print(f"  Error: Could not load image at '{path}'")
        return
    height, width, channels = frame.shape
    print(f"\nImage: {path}")
    print(f"  Resolution: {width}x{height}")
    print(f"  Channels: {channels} (BGR format)")
    print(f"  Total pixels: {width * height:,}")

def show_live_feed():
    index, backend = find_camera()
    if index == -1:
        print("\n  No camera available — check the troubleshooting steps below.")
        print("  1. Make sure your webcam is plugged in via USB")
        print("  2. Check Device Manager — is the webcam listed under Imaging Devices?")
        print("  3. Try unplugging and replugging the webcam")
        print("  4. Check if another app (Zoom, Teams) is using the camera")
        return

    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        print(f"  Error: Could not open camera at index {index}.")
        return

    print(f"\nCamera open — press Q to quit, S to save snapshot.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("  Error: Could not read frame.")
            break

        cv2.imshow("Oke Inventory — Camera Feed", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Closing camera.")
            break
        elif key == ord("s"):
            cv2.imwrite("scan.jpg", frame)
            print(f"  Snapshot saved — scan.jpg")
            inspect_image()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    show_live_feed()