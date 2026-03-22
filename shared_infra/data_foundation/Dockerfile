FROM python:3.11-slim
WORKDIR /app
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt
COPY shared_infra/ shared_infra/
CMD ["uvicorn", "shared_infra.data_foundation.main:app", "--host", "0.0.0.0", "--port", "8005"]
