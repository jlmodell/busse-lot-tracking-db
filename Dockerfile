FROM tiangolo/uvicorn-gunicorn-fastapi:latest

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 8089

COPY . .

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8089", "main:app"]