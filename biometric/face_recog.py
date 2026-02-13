import cv2
import numpy as np
import face_recognition
import pickle

def register_face(image_bytes):
    np_bytes = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
    enc = face_recognition.face_encodings(img)
    if len(enc) == 0:
        raise ValueError("No face detected.")
    return pickle.dumps(enc[0])

def verify_face(stored_enc, live_img_bytes):
    np_bytes = np.frombuffer(live_img_bytes, np.uint8)
    frame = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
    enc = face_recognition.face_encodings(frame)
    if len(enc) == 0:
        return False
    known = pickle.loads(stored_enc)
    return face_recognition.compare_faces([known], enc[0])[0]

def liveness_detection(live_img_bytes):
    np_bytes = np.frombuffer(live_img_bytes, np.uint8)
    frame = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    eyes = eye_cascade.detectMultiScale(gray, 1.3, 5)
    return len(eyes) >= 1
