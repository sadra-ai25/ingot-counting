from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
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

@app.post("/start/cameras")
async def start_cameras(request: StartCamerasRequest):
    for cam in request.cameras:
        stop_event = Event()
        producer_thread = Thread(
            target=camera_producer,
            args=(cam.rtsp_url, cam.camera_id, stop_event)
        )
        consumer_thread = Thread(
            target=frame_consumer,
            args=(cam.camera_id, cam.counting_line_x, f"camera_{cam.camera_id}", stop_event)
        )
        producer_thread.start()
        consumer_thread.start()

        active_processors[cam.camera_id] = {
            "type": "camera",
            "producer_thread": producer_thread,
            "consumer_thread": consumer_thread,
            "stop_event": stop_event,
            "rtsp_url": cam.rtsp_url,
            "counting_line_x": cam.counting_line_x
        }
        print(f"Camera {cam.camera_id} - Producer thread started: {producer_thread.is_alive()}")
        print(f"Camera {cam.camera_id} - Consumer thread started: {consumer_thread.is_alive()}")

        Thread(target=monitor_threads, args=(cam.camera_id, producer_thread, consumer_thread, stop_event)).start()

    return {
        "status": "started",
        "camera_ids": [cam.camera_id for cam in request.cameras]
    }

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


@app.post("/start/video")
async def start_video(
    file: UploadFile = File(...),
    counting_line_x: int = Form(...)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name
    
    processor_id = f"video_{int(time.time())}"
    stop_event = Event()
    producer_thread = Thread(
        target=video_producer,
        args=(temp_path, processor_id, stop_event)
    )
    consumer_thread = Thread(
        target=frame_consumer,
        args=(processor_id, counting_line_x, f"video_{processor_id}", stop_event)
    )
    producer_thread.start()
    consumer_thread.start()

    active_processors[processor_id] = {
        "type": "video",
        "producer_thread": producer_thread,
        "consumer_thread": consumer_thread,
        "stop_event": stop_event,
        "temp_file": temp_path
    }
    print(f"Video {processor_id} - Producer thread started: {producer_thread.is_alive()}")
    print(f"Video {processor_id} - Consumer thread started: {consumer_thread.is_alive()}")

    return {"status": "video processing started", "processor_id": processor_id}

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
            print(f"error in deleting temp file: {e}")

    del active_processors[processor_id]
    return {"status": "stopped", "processor_id": processor_id}