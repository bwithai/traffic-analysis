from pydantic import BaseModel


class DetectResponseModel(BaseModel):
    draw_paths: bool = True
    classes = [2, 3]  # coco data set 2:car, 3:bike
    id_size: int = 1
    path_history: int = 70
    draw_objects: bool = True
    track_boxes: bool = True
    save: bool = True  # Ture to save file