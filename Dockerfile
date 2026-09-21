FROM python:3.13-slim

WORKDIR /fastapiapp

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /fastapiapp

EXPOSE 8081

CMD ["python3", "main.py"]