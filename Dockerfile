FROM python:3.9-slim

# نصب پیشنیازها
RUN apt-get update && apt-get install -y \
curl \
gnupg \
ffmpeg \
libavcodec-dev \
libgl1-mesa-glx \
libavformat-dev \
libavutil-dev \
libglib2.0-0 \
unixodbc \
unixodbc-dev

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
&& curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
&& echo "[ODBC Driver 17 for SQL Server]\nDescription=Microsoft ODBC Driver 17 for SQL Server\nDriver=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.5.1.so.1\nUsageCount=1" >> /etc/odbcinst.ini


# تنظیم دایرکتوری کاری
WORKDIR /app

# نصب وابستگی‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن کل پروژه
COPY ./src /app/src

ENV PYTHONPATH="${PYTHONPATH}:/app"
# اجرای برنامه با uvicorn
CMD ["uvicorn", "src.app.api:app", "--host", "0.0.0.0", "--port", "5003"]
