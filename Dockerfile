FROM python:3.12

WORKDIR /code

ENTRYPOINT ["python", "-m", "tello_renewal"]

RUN apt update --fix-missing
RUN apt install -y firefox-esr

RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz
RUN tar -xzf geckodriver-v0.35.0-linux64.tar.gz -C /usr/local/bin
RUN rm geckodriver-v0.35.0-linux64.tar.gz

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY tello_renewal tello_renewal
COPY config config
