FROM python:3.11-slim
WORKDIR /app
COPY entrypoint.sh /entrypoint.sh
COPY src/ /app/src/
RUN pip install --no-cache-dir requests
ENTRYPOINT ["/entrypoint.sh"]
