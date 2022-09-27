FROM python:3-buster
RUN apt update && apt install --yes graphviz libgraphviz-dev && rm -r /var/cache/apt
WORKDIR /app
COPY . /app
RUN python -m pip install .

EXPOSE 5000

ENV QUART_APP=trafficlight
ENTRYPOINT ["hypercorn", "trafficlight:create_app()","--access-logfile", "-", "-b", "0.0.0.0:5000"]
