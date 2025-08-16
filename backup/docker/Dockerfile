FROM python:3.12-slim

# Install rclone
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip && \
    unzip rclone-current-linux-amd64.zip && \
    cd rclone-*-linux-amd64 && \
    cp rclone /usr/bin/ && \
    chmod 755 /usr/bin/rclone && \
    cd .. && rm -rf rclone-*-linux-amd64*

WORKDIR /app

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#COPY backup_runner.py .

CMD ["python", "backup_runner.py"]
