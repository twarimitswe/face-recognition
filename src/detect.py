import cv2
import os

def main():
    cascade_path = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")

    face=cv2.CascadeClassifier(cascade_path)
    if face.empty():
        raise RuntimeError(f"Failed to load cascade: {cascade_path}")
    cap=cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera not opened. Try camera index 0/1/2")
    print("Haar face detect (minimal). Press 'q' to quit.")

    smoothed = None  # (x, y, w, h) as floats
    missed_frames = 0
    MAX_MISSED = 10   # keep showing last box for this many frames without a detection
    SMOOTHING = 0.4    # higher = snappier, lower = smoother

    while True:
        ok,frame=cap.read()
        if not ok:
            break
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

        #minimal but practical defaults
        faces=face.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60,60)
        )

        if len(faces) > 0:
            # track the largest face only, to avoid boxes jumping between candidates
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
            x, y, w, h = (int(v) for v in smoothed)
            cv2.rectangle(frame, (x,y), (x+w, y+h),(0,255,0),2)

        cv2.imshow("Face Detection",frame)
        if (cv2.waitKey(1) & 0xFF)== ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
if __name__=="__main__":
    main()