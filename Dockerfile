FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask requests

COPY scripts/remediation_server.py .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["python", "remediation_server.py"]