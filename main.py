import os
import shutil

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

from schemas import DetectResponseModel

from traffic_analysis import load_system

app = FastAPI()

# Configure CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/upload")
async def create_upload_file(file: UploadFile = File(...)):
    if not file.read():
        return {"message": "No upload file sent"}

    dist_path = os.path.join(os.getcwd(), 'upload_files')
    if not os.path.exists(dist_path):
        os.makedirs(dist_path)

    # Move file to upload_files directory
    file_path = os.path.join(dist_path, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": f"{file.filename} is Uploaded Successfully"}


def get_file_names(folder_path):
    file_names = []
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            file_names.append(filename)
    return file_names


@app.get("/api/v1/video/get-all-file-name")
async def get_all_stored_file():
    demo = []
    result = []
    demo_files = get_file_names("demo")
    detected_files = get_file_names("result")

    for file_name in demo_files:
        file_name = f"upload_files/{file_name}"
        demo.append(file_name)

    for file_name in detected_files:
        file_name = f"result/{file_name}"
        result.append(file_name)

    return {
        "demo files": demo,
        "detected videos": result
    }


@app.post("/api/v1/detect/file-name")
async def load_traffic_analysis_system(metadata: DetectResponseModel):
    # detected_video_path = load_system(source=file_path, draw_paths=metadatadraw_paths,
    #                                   classes=metadataclasses, track_boxes=metadatatrack_boxes,
    #                                   save=metadatasave)
    detected_video_path= load_system(source="./demo/traffic.mp4", draw_paths=metadata.draw_paths, classes=[2, 3],
                id_size=metadata.id_size, path_history=metadata.path_history, draw_objects=metadata.draw_objects,
                track_boxes=metadata.track_boxes, save=metadata.save)

    return FileResponse(detected_video_path, media_type="video/mp4", filename="traffic_out.mp4")