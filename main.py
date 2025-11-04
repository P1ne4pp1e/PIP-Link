import numpy as np
import cv2

cv2.namedWindow('PIP-Link')
cv2.resizeWindow('PIP-Link', 720, 540)

frame = np.zeros((720, 540, 3), np.uint8)

if __name__ == '__main__':
    while True:
        cv2.imshow('PIP-Link', frame)

        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()