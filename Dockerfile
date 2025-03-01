FROM python:3.12

WORKDIR /fastapiapp

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /fastapiapp


CMD ["python3", "main.py"]