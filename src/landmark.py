# src/landmark.py
"""
Minimal pipeline:
camera -> Haar face box -> MediaPipe FaceLandmarker (Tasks API, full-frame) -> extract 5 keypoints -> draw

Run:
 python -m src.landmark

Keys:
 q : quit
"""

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python import BaseOptions
import os
import time


# 5-point indices (same canonical face mesh topology as legacy FaceMesh)
IDX_LEFT_EYE = 33
IDX_RIGHT_EYE = 263
IDX_NOSE_TIP = 1
IDX_MOUTH_LEFT = 61
IDX_MOUTH_RIGHT = 291


def main():
    # Haar
    cascade_path = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")
    face = cv2.CascadeClassifier(cascade_path)
    if face.empty():
        raise RuntimeError(f"Failed to load cascade: {cascade_path}")

    # FaceLandmarker (Tasks API)
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "face_landmarker.task")
    if not os.path.exists(model_path):
        raise RuntimeError(f"Missing model file: {model_path}")

    options = mp_vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=mp_vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = mp_vision.FaceLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera not opened. Try camera index 0/1/2.")

    print("Haar + FaceLandmarker 5pt (minimal). Press 'q' to quit.")
    start_time = time.monotonic()

    smoothed = None  # (x, y, w, h) as floats
    missed_frames = 0
    MAX_MISSED = 10   # keep showing last box for this many frames without a detection
    SMOOTHING = 0.4    # higher = snappier, lower = smoother

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        H, W = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

        if len(faces) > 0:
            # track the largest face only, to avoid the box jumping between candidates
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            missed_frames = 0
            if smoothed is None:
                smoothed = (float(x), float(y), float(w), float(h))
            else:
                smoothed = tuple(
                    prev + SMOOTHING * (cur - prev)
                    for prev, cur in zip(smoothed, (x, y, w, h))
                )
        else:
            missed_frames += 1
            if missed_frames > MAX_MISSED:
                smoothed = None

        if smoothed is not None:
            bx, by, bw, bh = (int(v) for v in smoothed)
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)

        # FaceLandmarker on full frame (simple)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.monotonic() - start_time) * 1000)
        res = landmarker.detect_for_video(mp_image, timestamp_ms)

        if res.face_landmarks:
            lm = res.face_landmarks[0]
            idxs = [IDX_LEFT_EYE, IDX_RIGHT_EYE, IDX_NOSE_TIP, IDX_MOUTH_LEFT, IDX_MOUTH_RIGHT]

            pts = []
            for i in idxs:
                p = lm[i]
                pts.append([p.x * W, p.y * H])
            kps = np.array(pts, dtype=np.float32)  # (5,2)

            # enforce left/right ordering
            if kps[0, 0] > kps[1, 0]:
                kps[[0, 1]] = kps[[1, 0]]
            if kps[3, 0] > kps[4, 0]:
                kps[[3, 4]] = kps[[4, 3]]

            # draw 5 points
            for (px, py) in kps.astype(int):
                cv2.circle(frame, (int(px), int(py)), 4, (0, 255, 0), -1)

            cv2.putText(frame, "5pt", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow("5pt Landmarks", frame)
        if (cv2.waitKey(1) & 0xFF) == ord("q"):
            break

    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

