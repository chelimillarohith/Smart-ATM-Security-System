import cv2
import numpy as np

def verify_fingerprint(stored_fp_bytes, uploaded_fp_bytes, min_matches=10):
    stored_np = np.frombuffer(stored_fp_bytes, np.uint8)
    img1 = cv2.imdecode(stored_np, cv2.IMREAD_GRAYSCALE)

    up_np = np.frombuffer(uploaded_fp_bytes, np.uint8)
    img2 = cv2.imdecode(up_np, cv2.IMREAD_GRAYSCALE)

    orb = cv2.ORB_create(nfeatures=1000)
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    if des1 is None or des2 is None:
        return False

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    good = [m for m in matches if m.distance < 60]

    return len(good) >= min_matches
