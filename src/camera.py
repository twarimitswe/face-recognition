import cv2

def main():
        cap=cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Camera not opened try using different index 0/1/2")
        print("Camera test. press 'q' to quit")
        while True:
            ok, frame=cap.read()
            if not ok:
                print("Failed to read Frame.")
                break
            cv2.imshow("Camera Test",frame)
            if(cv2.waitKey(1) & 0xFF)== ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()

if __name__=="__main__":
    main()
        