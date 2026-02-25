from fastapi import FastAPI, UploadFile, File, Form
from threading import Thread, Event
import tempfile
import time
import os
from typing import List
from pydantic import BaseModel
from src.capture.video_producer import video_producer
from src.capture.camera_producer import camera_producer
from src.processing.frame_consumer import frame_consumer
from src.config.config import settings
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()
active_processors = {}

class CameraConfig(BaseModel):
    camera_id: str
    rtsp_url: str
    counting_line_x: int

class StartCamerasRequest(BaseModel):
    cameras: List[CameraConfig]

load_dotenv()

CAMERA1_RTSP_URL = os.getenv("CAMERA1_RTSP_URL")
CAMERA1_COUNTING_LINE_X = int(os.getenv("CAMERA1_COUNTING_LINE_X", 0))
CAMERA2_RTSP_URL = os.getenv("CAMERA2_RTSP_URL")
CAMERA2_COUNTING_LINE_X = int(os.getenv("CAMERA2_COUNTING_LINE_X", 0))

def start_camera_processing(camera_id, rtsp_url, counting_line_x):
    stop_event = Event()
    producer_thread = Thread(
        target=camera_producer,
        args=(rtsp_url, camera_id, stop_event)
    )
    consumer_thread = Thread(
        target=frame_consumer,
        args=(camera_id, counting_line_x, f"camera_{camera_id}", stop_event)
    )
    producer_thread.start()
    consumer_thread.start()

    active_processors[camera_id] = {
        "type": "camera",
        "producer_thread": producer_thread,
        "consumer_thread": consumer_thread,
        "stop_event": stop_event,
        "rtsp_url": rtsp_url,
        "counting_line_x": counting_line_x
    }
    logger.info(f"Camera {camera_id} - Producer thread started: {producer_thread.is_alive()}")
    logger.info(f"Camera {camera_id} - Consumer thread started: {consumer_thread.is_alive()}")

    Thread(target=monitor_threads, args=(camera_id, producer_thread, consumer_thread, stop_event)).start()

def monitor_threads(camera_id, producer_thread, consumer_thread, stop_event):
    while not stop_event.is_set():
        if not producer_thread.is_alive():
            logger.warning(f"Producer thread for {camera_id} has stopped. Restarting...")
            producer_thread = Thread(
                target=camera_producer,
                args=(active_processors[camera_id]["rtsp_url"], camera_id, stop_event)
            )
            producer_thread.start()
            active_processors[camera_id]["producer_thread"] = producer_thread
        if not consumer_thread.is_alive():
            logger.warning(f"Consumer thread for {camera_id} has stopped. Restarting...")
            consumer_thread = Thread(
                target=frame_consumer,
                args=(camera_id, active_processors[camera_id]["counting_line_x"], f"camera_{camera_id}", stop_event)
            )
            consumer_thread.start()
            active_processors[camera_id]["consumer_thread"] = consumer_thread
        time.sleep(10)  


###========
# Autorun service by two cameras and counting lines
###========
@app.on_event("startup")
async def startup_event():
    # start processing for cam1
    if CAMERA1_RTSP_URL and CAMERA1_COUNTING_LINE_X:
        start_camera_processing("camera1", CAMERA1_RTSP_URL, CAMERA1_COUNTING_LINE_X)
    # start processing for cam2
    if CAMERA2_RTSP_URL and CAMERA2_COUNTING_LINE_X:
        start_camera_processing("camera2", CAMERA2_RTSP_URL, CAMERA2_COUNTING_LINE_X)

@app.post("/start/cameras")
async def start_cameras(request: StartCamerasRequest):
    for cam in request.cameras:
        start_camera_processing(cam.camera_id, cam.rtsp_url, cam.counting_line_x)
    return {
        "status": "started",
        "camera_ids": [cam.camera_id for cam in request.cameras]
    }


@app.get("/status")
async def get_status():
    return {"active": list(active_processors.keys())}

@app.post("/stop/{processor_id}")
async def stop_processor(processor_id: str):
    if processor_id not in active_processors:
        return {"error": "Processor not found"}

    proc = active_processors[processor_id]
    proc["stop_event"].set()

    proc["producer_thread"].join(timeout=5)
    proc["consumer_thread"].join(timeout=5)

    if proc["type"] == "video" and "temp_file" in proc:
        try:
            os.unlink(proc["temp_file"])
        except Exception as e:
            logger.error(f"error in deleting temp file: {e}")

    del active_processors[processor_id]
    return {"status": "stopped", "processor_id": processor_id}