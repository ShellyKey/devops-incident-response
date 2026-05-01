FROM python:3.11-slim

WORKDIR /app

# Install kubectl inside the container
RUN apt-get update && apt-get install -y curl && \
    curl -LO "https://dl.k8s.io/release/v1.29.0/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl && \
    apt-get clean

RUN pip install --no-cache-dir flask requests

COPY scripts/remediation_server.py .

EXPOSE 5000

CMD ["python", "remediation_server.py"]