FROM python:3.9-buster

RUN apt-get update -y
RUN apt-get install -y build-essential
RUN apt update && apt install -y libsm6 libxext6
RUN apt-get -y install tesseract-ocr

# COPY . /app
COPY openccv_test.py /app
WORKDIR /app
RUN pip install pillow
RUN pip install pytesseract
RUN pip install opencv-contrib-python
# RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["openccv_test.py"]