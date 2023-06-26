import os
from functools import partial

import numpy as np

from norfair import (
    AbsolutePaths,
    Tracker,
    Video,
)
from norfair.drawing import draw_tracked_objects

from optflow import MotionEstimator, apply_labels, HomographyTransformationGetter
from yolo_helper import load_model_to_yolo, yolo_detections_to_sort


def load_system(source, model='yolov5n', track_boxes=False, mask_detections=False,
                classes=None, id_size=1, save=False, draw_flow=False,
                draw_paths=False, path_history=30, draw_objects=False):
    """
        Loads the system for object tracking and analysis.

        Args:
            source (str): Path to the input video file.
            model (str, optional): YOLO model to use for object detection. Defaults to 'yolov5n'.
            track_boxes (bool, optional): Whether to track the bounding boxes of the detected objects. Defaults to False.
            mask_detections (bool, optional): Whether to mask the detected objects. Defaults to False.
            classes (list, optional): List of classes to detect. Defaults to None.
            id_size (int, optional): Size of the object ID to display. Defaults to 1.
            save (bool, optional): Whether to save the output video. Defaults to False.
            draw_flow (bool, optional): Whether to draw optical flow arrows. Defaults to False.
            draw_paths (bool, optional): Whether to draw paths of tracked objects. Defaults to False.
            path_history (int, optional): Number of frames to keep in the path history. Defaults to 30.
            draw_objects (bool, optional): Whether to draw tracked objects. Defaults to False.

        Returns:
            str: Output path of the processed video file.
        """
    tracked_objects = []
    transformations_getter = HomographyTransformationGetter()

    model = load_model_to_yolo(weight=model, classes=classes)

    if transformations_getter is not None:
        # Optical flow
        motion_estimator = MotionEstimator(
            max_points=900,
            min_distance=14,
            transformations_getter=transformations_getter,
            draw_flow=draw_flow,
        )
    else:
        motion_estimator = None

    if draw_paths:
        path_drawer = AbsolutePaths(max_history=path_history, thickness=2)

    video = Video(input_path=source)
    video.output_path = "./result/"
    show_or_write = (
        video.write
        if save
        else partial(video.show, downsample_ratio=1)
    )

    # SORT tracker
    tracker = Tracker(
        distance_function="euclidean",
        detection_threshold=0.15,
        distance_threshold=300,
        initialization_delay=3,
        hit_counter_max=6,
    )

    for frame in video:
        detections = model(frame)

        # Apply label same as YOLO algo
        # frame = apply_labels(detections, frame)

        # Change the detections to SORT detections
        detections, boxes, center_coordinates = yolo_detections_to_sort(
            detections, track_boxes,
        )

        mask = None
        if mask_detections:
            # create a mask of ones
            mask = np.ones(frame.shape[:2], frame.dtype)
            # set to 0 all detections
            for b in boxes:
                i = b.astype(int)
                mask[i[0, 1]: i[1, 1], i[0, 0]: i[1, 0]] = 0
            if track_boxes:
                for obj in tracked_objects:
                    i = obj.estimate.astype(int)
                    mask[i[0, 1]: i[1, 1], i[0, 0]: i[1, 0]] = 0

        # Validate the OpticalFlow
        if motion_estimator is None:
            coord_transformations = None
        else:
            coord_transformations = motion_estimator.update(frame, mask)

        tracked_objects = tracker.update(
            detections=detections, coord_transformations=coord_transformations
        )

        if draw_objects:
            draw_tracked_objects(
                frame,
                tracked_objects,
                id_size=id_size,
                id_thickness=None
                if id_size is None
                else int(id_size * 2),
            )

        if draw_paths:
            frame = path_drawer.draw(
                frame, tracked_objects, coord_transform=coord_transformations
            )

        show_or_write(frame)
    return video.get_output_file_path()
