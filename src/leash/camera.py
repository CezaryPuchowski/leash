"""Manager for a Lumen camera."""

from logging import Logger

import cv2


class Camera:
    """Class for a Lumen camera."""

    def __init__(self, logger:Logger, index:int = 1)->None:
        """Initialize of camera."""
        # opening camera from config settings, setting frame size
        self._capture = cv2.VideoCapture(index)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.log = logger

    def list_cameras(self)->list:
        """List available cameras."""
        index = 0
        cameras = []
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.isOpened():
                break
            cameras.append(index)
            cap.release()
            index += 1
        return cameras

    def capture(self):
        """Capture image from camera."""
        ret, image = self._capture.read()
        if ret is True:
            return image
        return False

    def get_fid_position(self):
        """Return precise fiducial position under camera."""
        raise NotImplementedError
        while True:
            image = self.capture()
            if image.any():
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                blur = cv2.blur(gray,(10,10))

                mask = cv2.threshold(blur, 128, 255, cv2.THRESH_BINARY)[1]

                circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1.2, 100)

                cv2.imshow("img", circles)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                self.log.error("couldn't take a pic")

        self._capture.release()
        cv2.destroyAllWindows()

        # circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1.2, 100)

        # if circles is not None:
        #     # convert the (x, y) coordinates and radius of the circles to integers
        #     circles = np.round(circles[0, :]).astype("int")
        #     # loop over the (x, y) coordinates and radius of the circles
        #     for (x, y, r) in circles:
        #         # draw the circle in the output image, then draw a rectangle
        #         # corresponding to the center of the circle
        #         cv2.circle(output, (x, y), r, (0, 255, 0), 4)
        #         cv2.rectangle(output, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
        #     # show the output image

        #     if debug:
        #         cv2.imshow("output", np.hstack([image, output]))
        #         cv2.waitKey(1)

        #     return (x, y, r)

        return False
