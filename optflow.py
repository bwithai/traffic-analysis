from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np

try:
    import cv2
except ImportError:
    from norfair.utils import DummyOpenCVImport

    cv2 = DummyOpenCVImport()


#
# Abstract interfaces
#
class CoordinatesTransformation(ABC):
    """
    Abstract class representing a coordinate transformation.

    Detections' and tracked objects' coordinates can be interpreted in 2 reference:

    - _Relative_: their position on the current frame, (0, 0) is top left
    - _Absolute_: their position on an fixed space, (0, 0)
        is the top left of the first frame of the video.

    Therefore, coordinate transformation in this context is a class that can transform
    coordinates in one reference to another.
    """

    @abstractmethod
    def abs_to_rel(self, points: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def rel_to_abs(self, points: np.ndarray) -> np.ndarray:
        pass


class TransformationGetter(ABC):
    """
    Abstract class representing a method for finding CoordinatesTransformation between 2 sets of points
    """

    @abstractmethod
    def __call__(
            self, curr_pts: np.ndarray, prev_pts: np.ndarray
    ) -> Tuple[bool, CoordinatesTransformation]:
        pass


#
# Homography
#
class HomographyTransformation(CoordinatesTransformation):
    """
    Coordinate transformation beweent points using an homography

    Parameters
    ----------
    homography_matrix : np.ndarray
        The matrix representing the homography
    """

    def __init__(self, homography_matrix: np.ndarray):
        self.homography_matrix = homography_matrix
        self.inverse_homography_matrix = np.linalg.inv(homography_matrix)

    def abs_to_rel(self, points: np.ndarray):
        ones = np.ones((len(points), 1))
        points_with_ones = np.hstack((points, ones))
        points_transformed = points_with_ones @ self.homography_matrix.T
        points_transformed = points_transformed / points_transformed[:, -1].reshape(
            -1, 1
        )
        return points_transformed[:, :2]

    def rel_to_abs(self, points: np.ndarray):
        ones = np.ones((len(points), 1))
        points_with_ones = np.hstack((points, ones))
        points_transformed = points_with_ones @ self.inverse_homography_matrix.T
        points_transformed = points_transformed / points_transformed[:, -1].reshape(
            -1, 1
        )
        return points_transformed[:, :2]


class HomographyTransformationGetter(TransformationGetter):
    """
    Calculates HomographyTransformation between points.

    The camera movement is represented as an homography that matches the optical flow between the previous reference frame
    and the current.

    Comparing consecutive frames can make differences too small to correctly estimate the homography, often resulting in the identity.
    For this reason the reference frame is kept fixed as we progress through the video.
    Eventually, if the transformation is no longer able to match enough points, the reference frame is updated.

    Parameters
    ----------
    method : Optional[int], optional
        One of openCV's method for finding homographies.
        Valid options are: `[0, cv.RANSAC, cv.LMEDS, cv.RHO]`, by default `cv.RANSAC`
    ransac_reproj_threshold : int, optional
        Maximum allowed reprojection error to treat a point pair as an inlier. More info in links below.
    max_iters : int, optional
        The maximum number of RANSAC iterations.  More info in links below.
    confidence : float, optional
        Confidence level, must be between 0 and 1. More info in links below.
    proportion_points_used_threshold : float, optional
        Proportion of points that must be matched, otherwise the reference frame must be updated.

    See Also
    --------
    [opencv.findHomography](https://docs.opencv.org/3.4/d9/d0c/group__calib3d.html#ga4abc2ece9fab9398f2e560d53c8c9780)
    """

    def __init__(
            self,
            method: Optional[int] = None,
            ransac_reproj_threshold: int = 3,
            max_iters: int = 2000,
            confidence: float = 0.995,
            proportion_points_used_threshold: float = 0.9,
    ) -> None:
        self.data = None
        if method is None:
            method = cv2.RANSAC
        self.method = method
        self.ransac_reproj_threshold = ransac_reproj_threshold
        self.max_iters = max_iters
        self.confidence = confidence
        self.proportion_points_used_threshold = proportion_points_used_threshold

    def __call__(
            self, curr_pts: np.ndarray, prev_pts: np.ndarray
    ) -> Tuple[bool, HomographyTransformation]:
        homography_matrix, points_used = cv2.findHomography(
            prev_pts,
            curr_pts,
            method=self.method,
            ransacReprojThreshold=self.ransac_reproj_threshold,
            maxIters=self.max_iters,
            confidence=self.confidence,
        )

        proportion_points_used = np.sum(points_used) / len(points_used)

        update_prvs = proportion_points_used < self.proportion_points_used_threshold

        try:
            homography_matrix = homography_matrix @ self.data
        except (TypeError, ValueError):
            pass

        if update_prvs:
            self.data = homography_matrix

        return update_prvs, HomographyTransformation(homography_matrix)


#
# Motion estimation
#
def _get_sparse_flow(
        gray_next,
        gray_prvs,
        prev_pts=None,
        max_points=300,
        min_distance=15,
        block_size=3,
        mask=None,
        quality_level=0.01,
):
    if prev_pts is None:
        # get points
        prev_pts = cv2.goodFeaturesToTrack(
            gray_prvs,
            maxCorners=max_points,
            qualityLevel=quality_level,
            minDistance=min_distance,
            blockSize=block_size,
            mask=mask,
        )

    # compute optical flow
    curr_pts, status, err = cv2.calcOpticalFlowPyrLK(
        gray_prvs, gray_next, prev_pts, None
    )
    # filter valid points
    idx = np.where(status == 1)[0]
    prev_pts = prev_pts[idx].reshape((-1, 2))
    curr_pts = curr_pts[idx].reshape((-1, 2))
    return curr_pts, prev_pts


class MotionEstimator:
    """
    Estimator of the motion of the camera.

    Uses optical flow to estimate the motion of the camera from frame to frame.
    The optical flow is calculated on a sample of strong points (corners).

    Parameters
    ----------
    max_points : int, optional
        Maximum amount of points sampled.
        More points make the estimation process slower but more precise
    min_distance : int, optional
        Minimum distance between the sample points.
    block_size : int, optional
        Size of an average block when finding the corners. More info in links below.
    transformations_getter : TransformationGetter, optional
        An instance of TransformationGetter. By default [`HomographyTransformationGetter`][norfair.camera_motion.HomographyTransformationGetter]
    draw_flow : bool, optional
        Draws the optical flow on the frame for debugging.
    flow_color : Optional[Tuple[int, int, int]], optional
        Color of the drawing, by default blue.
    quality_level : float, optional
        Parameter characterizing the minimal accepted quality of image corners.
    """

    def __init__(
            self,
            max_points: int = 200,
            min_distance: int = 15,
            block_size: int = 3,
            transformations_getter: TransformationGetter = None,
            draw_flow: bool = False,
            flow_color: Optional[Tuple[int, int, int]] = None,
            quality_level: float = 0.01,
    ):

        self.max_points = max_points
        self.min_distance = min_distance
        self.block_size = block_size

        self.draw_flow = draw_flow
        if self.draw_flow and flow_color is None:
            flow_color = [255, 0, 0]
        self.flow_color = flow_color

        self.gray_prvs = None
        self.prev_pts = None
        if transformations_getter is None:
            transformations_getter = HomographyTransformationGetter()

        self.transformations_getter = transformations_getter
        self.prev_mask = None
        self.gray_next = None
        self.quality_level = quality_level

    def update(
            self, frame: np.ndarray, mask: np.ndarray = None
    ) -> CoordinatesTransformation:
        """
        Estimate camera motion for each frame

        Parameters
        ----------
        frame : np.ndarray
            The frame.
        mask : np.ndarray, optional
            An optional mask to avoid areas of the frame when sampling the corner.
            Must be an array of shape `(frame.shape[0], frame.shape[1])`, dtype same as frame,
            and values in {0, 1}.

            In general, the estimation will work best when it samples many points from the background;
            with that intention, this parameters is usefull for masking out the detections/tracked objects,
            forcing the MotionEstimator ignore the moving objects.
            Can be used to mask static areas of the image, such as score overlays in sport transmisions or
            timestamps in security cameras.

        Returns
        -------
        CoordinatesTransformation
            The CoordinatesTransformation that can transform coordinates on this frame to absolute coordinates
            or vice versa.
        """
        self.gray_next = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.gray_prvs is None:
            self.gray_prvs = self.gray_next
            self.prev_mask = mask

        curr_pts, self.prev_pts = _get_sparse_flow(
            self.gray_next,
            self.gray_prvs,
            self.prev_pts,
            self.max_points,
            self.min_distance,
            self.block_size,
            self.prev_mask,
            quality_level=self.quality_level,
        )
        if self.draw_flow:
            for (curr, prev) in zip(curr_pts, self.prev_pts):
                c = tuple(curr.astype(int).ravel())
                p = tuple(prev.astype(int).ravel())
                # cv2.line(frame, c, p, self.flow_color, 2)
                # cv2.circle(frame, c, 3, self.flow_color, -1)
                cv2.arrowedLine(frame, c, p,
                                self.flow_color, 2, tipLength=0.5)

        update_prvs, coord_transformations = self.transformations_getter(
            curr_pts,
            self.prev_pts,
        )

        if update_prvs:
            self.gray_prvs = self.gray_next
            self.prev_pts = None
            self.prev_mask = mask

        return coord_transformations


def apply_labels(detections, frame):
    # Get the bounding box coordinates
    boxes = detections.xyxy[0][:, :4]

    # Get the class labels
    labels = detections.names[0][detections.xyxy[0][:, -1].long()]

    # Get the confidence scores
    scores = detections.xyxy[0][:, 4]

    # Process the detections
    for box, label, score in zip(boxes, labels, scores):
        # Check if the detection is a vehicle (class_id 2 corresponds to car in COCO dataset)
        if label == 'car' and score > 0.5:
            x_min = int(box[0])
            y_min = int(box[1])
            x_max = int(box[2])
            y_max = int(box[3])

            # Draw the bounding box on the frame
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    return frame

    # # Display the frame
    # cv2.imshow('Frame', frame)
    #
    # # Press 'q' to quit the loop
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break