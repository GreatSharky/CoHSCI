FROM python:3.13.5-bullseye

WORKDIR /app
RUN pip install --upgrade pip
COPY messageq ./messageq
RUN pip install ./messageq
COPY segmentor .
RUN pip install -r requirements.txt
CMD [ "python" , "segment.py"]
