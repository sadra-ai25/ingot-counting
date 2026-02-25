# in the src folder app/api.py, db/database.py, processing/frame_consumer.py changed for autorun of cameras without requesting
- sudo docker compose up -d

# if you need to request after that the docker is up, use 'api-old.py' instead of the 'api.py' then send request based on the below commands:
curl -X POST "http://localhost:5003/start/video" -F "file=@path/to/your/video.mp4" -F "counting_line_x=525"
curl -X POST "http://localhost:5003/start/video" -F "file=@path/to/your/video.mp4" -F "counting_line_x=525"
curl -X POST "http://localhost:5003/start/cameras" \
     -H "Content-Type: application/json" \
     -d '{
    "cameras": [
        {"camera_id": "camera_1", "rtsp_url": "rtsp://admin:$adraPASS@192.168.50.150:554/", "counting_line_x": 1130},
        {"camera_id": "camera_2", "rtsp_url": "rtsp://admin:$adraPASS@192.168.50.150:554/", "counting_line_x": 2710}
    ]
}'
####################################################################################
# 'restart-service.sh' restarts service every 30 minutes (30 minutes is changable)
for enabling you should run:
      - sudo chmod +x restart-service.sh
      - sudo ./restart-service.sh

for disabling you should run:
      - sudo systemctl disable --now ingot-service.timer
      - sudo rm /etc/systemd/system/ingot-service.timer
      - sudo rm /etc/systemd/system/ingot-service.service
      - sudo systemctl daemon-reload
      - sudo systemctl reset-failed
####################################################################################

if .env file not exist please done follow commands:
# cd project root
touch .env
sudo nano .env
# write bellow lines:
""" use for sadra database and uncomment that
DB_SERVER=192.168.50.113\sql2019
DB_NAME=dbailog
USERNAME=sa
PASSWORD=S@draAfzar

""" use for abhar database and uncomment that
# DB_SERVER=192.168.1.11\sqlsadra
# DB_NAME=DBSadraafzar001
# USERNAME=AI
# PASSWORD=S@dra123

# # camera 1 config
CAMERA1_RTSP_URL=rtsp://admin:$$adraPASS@192.168.50.150:554/
CAMERA1_COUNTING_LINE_X=525

# # camera 2 config
CAMERA2_RTSP_URL=rtsp://A:Aa.123456@185.129.236.75:554/cam/realmonitor?channel=1&subtype=0
CAMERA2_COUNTING_LINE_X=525

# # video 1 config
VIDEO1_PATH=./cam1_2.mp4
VIDEO1_COUNTING_LINE_X=525

# RabbitMQ config
RABBITMQ_HOST = rabbitmq
RABBITMQ_PORT = 5672
RABBITMQ_USER = guest
RABBITMQ_PASS = guest
# QUEUE_NAME = camera_frames


