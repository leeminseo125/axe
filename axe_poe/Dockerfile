FROM python:3.11-slim
WORKDIR /app
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt
COPY shared_infra/ shared_infra/
COPY axe_poe/ axe_poe/
CMD ["uvicorn", "axe_poe.main:app", "--host", "0.0.0.0", "--port", "8002"]
