import numpy as np
import torch
from norfair import Detection


def load_model_to_yolo(weight, classes):
    """
        Description
        ----------
        This code is loading a pre-trained YOLOv7 model,
        which is a type of object detection algorithm,
        from the torch hub using the "WongKinYiu/yolov7" repository and the "custom" version.

        The specific model being loaded is specified by the "args.model" variable.
        The torch.hub library provides a simple interface to load pre-trained models from popular model repositories,
        such as the PyTorch model zoo, and perform common tasks, such as fine-tuning or feature extraction.

        """
    model = torch.hub.load('ultralytics/yolov5', 'custom', './data/yolov5n.pt')
    model.conf_threshold = 0
    model.iou_threshold = 0.15
    model.image_size = 480
    model.classes = classes
    return model


def yolo_detections_to_sort(yolo_detections, track_boxes):
    """
    Detections returned by the detector must be converted to a `Detection` object before being used by Norfair.

        Parameters
        ----------
        points : np.ndarray
            Points detected. Must be a rank 2 array with shape `(n_points, n_dimensions)` where n_dimensions is 2 or 3.
        scores : np.ndarray, optional
            An array of length `n_points` which assigns a score to each of the points defined in `points`.

            This is used to inform the tracker of which points to ignore;
            any point with a score below `detection_threshold` will be ignored.

            This useful for cases in which detections don't always have every point present, as is often the case in pose estimators.
        data : Any, optional
            The place to store any extra data which may be useful when calculating the distance function.
            Anything stored here will be available to use inside the distance function.

            This enables the development of more interesting trackers which can do things like assign an appearance embedding to each
            detection to aid in its tracking.
        label : Hashable, optional
            When working with multiple classes the detection's label can be stored to be used as a matching condition when associating
            tracked objects with new detections. Label's type must be hashable for drawing purposes.
        embedding : Any, optional
            The embedding for the reid_distance.

        """
    norfair_detections = []
    boxes = []

    detections_as_xyxy = yolo_detections.xyxy[0]
    for detection_as_xyxy in detections_as_xyxy:
        detection_as_xyxy = detection_as_xyxy.cpu().numpy()
        bbox = np.array(
            [
                [detection_as_xyxy[0].item(), detection_as_xyxy[1].item()],
                [detection_as_xyxy[2].item(), detection_as_xyxy[3].item()],
            ]
        )
        boxes.append(bbox)

        # Calculate the center coordinate of the bounding box
        center_x = (bbox[0][0] + bbox[1][0]) / 2
        center_y = (bbox[0][1] + bbox[1][1]) / 2

        if track_boxes:
            points = bbox
            scores = np.array([detection_as_xyxy[4], detection_as_xyxy[4]])
        else:
            points = bbox.mean(axis=0, keepdims=True)
            scores = detection_as_xyxy[[4]]

        norfair_detections.append(
            Detection(points=points, scores=scores, label=detection_as_xyxy[-1].item())
        )

    return norfair_detections, boxes
