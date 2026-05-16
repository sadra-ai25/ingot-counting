# Ingot Counting System

![Python](https://img.shields.io/badge/Python-3.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green) ![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-red) ![Docker](https://img.shields.io/badge/Docker-Compose-blue) ![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-orange)

Real-time steel ingot counting system using computer vision. Detects and counts ingots passing a virtual counting line on a conveyor belt via RTSP camera streams, with automatic logging to SQL Server.

## Features

- **Multi-camera support** — simultaneously process multiple RTSP streams
- **Video file support** — count ingots from recorded video files
- **Virtual counting line** — configurable X-position line triggers count when ingot centroid crosses it
- **Object tracking** — YOLOv8 tracker prevents double-counting the same ingot
- **Dimension estimation** — captures approximate height/width of each counted ingot
- **SQL Server logging** — every count event is persisted to the database
- **RabbitMQ queue** — decoupled producer/consumer architecture for reliability
- **REST API** — start/stop cameras and upload videos via HTTP endpoints

## Tech Stack

| Component | Technology |
|---|---|
| AI Model | YOLOv8 (Ultralytics) with object tracking |
| API Server | FastAPI + Uvicorn |
| Message Queue | RabbitMQ |
| Database | Microsoft SQL Server (pyodbc) |
| Containerization | Docker Compose |
| Camera Capture | OpenCV (cv2) |

## Architecture

```
RTSP Camera(s)
      │
      ▼
 Camera Producer (Thread)
      │  pushes frames
      ▼
  RabbitMQ Queue
      │  consumes frames
      ▼
 Frame Consumer (Thread)
      │
      ▼
 IngotCounter (YOLOv8 Track)
   - Detects ingots
   - Assigns tracking IDs
   - Checks centroid vs. counting line
      │  count event
      ▼
 SQL Server Database  ←→  FastAPI REST API
```

## Prerequisites

- Docker & Docker Compose
- YOLOv8 model weights (`best.pt`) placed in `src/ai/weights/`
- RTSP-capable IP cameras or video files
- Microsoft SQL Server (reachable from the container)
- ODBC Driver 17 for SQL Server

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/sadra-ai25/ingot-counting.git
cd ingot-counting

# 2. Configure environment
cp .env.example .env   # then edit .env with your values

# 3. Place your model weights
mkdir -p src/ai/weights
cp /path/to/best.pt src/ai/weights/

# 4. Start services
docker compose up -d --build
```

## Configuration

Edit `.env` before starting:

| Key | Description | Example |
|---|---|---|
| `DB_SERVER` | SQL Server hostname/IP | `192.168.1.100\sqlserver` |
| `DB_NAME` | Database name | `IngotDB` |
| `USERNAME` | SQL Server login | `sa` |
| `PASSWORD` | SQL Server password | `your_password_here` |
| `CAMERA1_RTSP_URL` | RTSP URL of camera 1 | `rtsp://username:password@192.168.1.101:554/` |
| `CAMERA1_COUNTING_LINE_X` | X-pixel position of virtual line | `1130` |
| `CAMERA2_RTSP_URL` | RTSP URL of camera 2 | `rtsp://username:password@192.168.1.102:554/` |
| `CAMERA2_COUNTING_LINE_X` | X-pixel position of virtual line | `2710` |
| `RABBITMQ_HOST` | RabbitMQ hostname | `rabbitmq` |
| `RABBITMQ_PORT` | RabbitMQ port | `5672` |
| `RABBITMQ_USER` | RabbitMQ username | `guest` |
| `RABBITMQ_PASS` | RabbitMQ password | `guest` |

## Usage

The service starts automatically with Docker Compose. Use the REST API to control cameras:

```bash
# Check service health
curl http://localhost:5003/

# Start all cameras (reads from .env)
curl -X POST http://localhost:5003/start_cameras

# Stop all cameras
curl -X POST http://localhost:5003/stop_cameras

# Upload a video file for processing
curl -X POST http://localhost:5003/upload_video \
  -F "file=@/path/to/video.mp4" \
  -F "counting_line_x=1130"
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/start_cameras` | Start all configured camera streams |
| `POST` | `/stop_cameras` | Stop all running camera streams |
| `POST` | `/upload_video` | Upload a video file for ingot counting |
| `POST` | `/start_custom_cameras` | Start cameras with custom config payload |

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
