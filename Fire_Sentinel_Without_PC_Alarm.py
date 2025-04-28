import cv2
import serial
import time
import datetime
import pywhatkit
from ultralytics import YOLO

# ========== SERIAL SETUP ==========
arduino = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)

# ========== YOLO MODEL ==========
model = YOLO("best.pt").to("cpu")

# ========== CAMERA ==========
ip_camera_url = "http://192.0.0.4:8080/video"
cap = cv2.VideoCapture(ip_camera_url)

# ========== FIRE DETECTION PARAMS ==========
KNOWN_WIDTH = 30
FOCAL_LENGTH = 800

def calculate_distance(known_width, focal_length, perceived_width):
    return (known_width * focal_length) / perceived_width

# ========== STATE ==========
fire_detected = False
fire_start_time = None
alarm_triggered = False
image_sent = False
last_frame_time = time.time()

# ========== MAIN LOOP ==========
while True:
    # Limit frame rate (approx. 10 FPS)
    if time.time() - last_frame_time < 0.1:
        continue
    last_frame_time = time.time()

    ret, frame = cap.read()
    if not ret or frame is None:
        print("⚠️ Frame not captured")
        continue

    if not fire_detected:
        arduino.write(b"ROTATE\n")
        print("[SERVO 360] Rotating continuously")

    results = model.predict(frame, imgsz=320, verbose=False)
    fire_found = False

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width = x2 - x1
            distance = calculate_distance(KNOWN_WIDTH, FOCAL_LENGTH, width)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"Fire: {int(distance)} cm", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            fire_found = True

    # ========== FIRE RESPONSE ==========
    if fire_found:
        if not fire_detected:
            fire_start_time = time.time()
            fire_detected = True
        elif time.time() - fire_start_time > 3 and not alarm_triggered:
            print("🔥 Fire confirmed. Triggering actions...")
            arduino.write(b"STOP\n")
            time.sleep(0.5)
            arduino.write(b"FIRE\n")
            alarm_triggered = True

            if not image_sent:
                image_path = "fire.jpg"
                cv2.imwrite(image_path, frame)

                now = datetime.datetime.now() + datetime.timedelta(minutes=1)
                try:
                    pywhatkit.sendwhats_image(
                        "+918433659338",  # CHANGE THIS NUMBER
                        image_path,
                        "🔥 Fire Detected!",
                        tab_close=True
                    )
                    print("📲 WhatsApp sent")
                    image_sent = True
                except Exception as e:
                    print(f"❌ WhatsApp Error: {e}")
    else:
        if fire_detected:
            print("✅ Fire gone. Resetting...")
            arduino.write(b"RESUME\n")
        fire_detected = False
        fire_start_time = None
        alarm_triggered = False
        image_sent = False

    # ========== DISPLAY ==========
    cv2.imshow("🔥 Fire Detection", cv2.resize(frame, (320, 240)))
    if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:
        print("👋 Exiting...")
        arduino.write(b'STOP\n')
        break

# ========== CLEANUP ==========
arduino.write(b'STOP\n')
cap.release()
arduino.close()
cv2.destroyAllWindows()
