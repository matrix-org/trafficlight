FROM python:3.11.6-bullseye
WORKDIR /app
COPY . /app
RUN apt update && apt install -y libolm-dev && rm -rf /var/lib/apt/lists/*

RUN python -m pip install .

EXPOSE 5000

ENV QUART_APP=trafficlight
ENTRYPOINT ["hypercorn", "trafficlight:create_app()","--access-logfile", "-", "-b", "0.0.0.0:5000"]
