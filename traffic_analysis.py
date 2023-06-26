import os
from functools import partial

from norfair import (
    AbsolutePaths,
    Tracker,
    Video,
)
from norfair.drawing import draw_tracked_objects

from optflow import MotionEstimator, apply_labels
from yolo_helper import load_model_to_yolo, yolo_detections_to_sort


def load_system(source, model='yolov5n', track_boxes=False,
           classes=None, id_size=1, save=False, draw_flow=False,
           draw_paths=False, path_history=30, draw_objects=False):
    global left_line_counter
    global right_line_counter

    model = load_model_to_yolo(weight=model, classes=classes)

    motion_estimator = MotionEstimator(
        max_points=900,
        min_distance=14,
        transformations_getter=None,
        draw_flow=draw_flow,
    )

    if draw_paths:
        path_drawer = AbsolutePaths(max_history=path_history, thickness=2)

    video = Video(input_path=source)
    video.output_path = "./result/"
    show_or_write = (
        video.write
        if save
        else partial(video.show, downsample_ratio=1)
    )

    # sort
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

        # Validate the OpticalFlow
        if motion_estimator is None:
            coord_transformations = None
        else:
            coord_transformations = motion_estimator.update(frame)

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

    # if h264:
    #     input_file = video.get_output_file_path()
    #     path = input_file.split(".")
    #     output_file = f".{path[1]}_h264.{path[2]}"
    #
    #     command = "ffmpeg -i {} -c:v h264 -crf 18 -strict -2 {}".format(input_file, output_file)
    #
    #     subprocess.call(command, shell=True)
    #     os.remove(input_file)
    #     return output_file
    # return video.get_output_file_path()

# result = load_system(source="./demo/traffic.mp4", draw_paths=True, classes=[2, 3],
#                 id_size=1, path_history=70, draw_objects=True,
#                 track_boxes=True, save=False)
# print("Video stored at ", result)
