FROM python:3.11-slim
WORKDIR /app
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt
COPY shared_infra/ shared_infra/
COPY axengine/ axengine/
CMD ["uvicorn", "axengine.main:app", "--host", "0.0.0.0", "--port", "8001"]
