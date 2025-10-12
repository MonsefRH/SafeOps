FROM python:3.12-slim

WORKDIR /app

# + git pour GitPython
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev git \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
