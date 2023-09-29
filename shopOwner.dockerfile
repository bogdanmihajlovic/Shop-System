FROM python:3

RUN mkdir -p /opt/src/owner
WORKDIR /opt/src/owner

COPY owner/application.py ./application.py
COPY owner/configuration.py ./configuration.py
COPY owner/models.py ./models.py
COPY owner/requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

ENV PYTHONPATH="/opt/src/owner"
ENTRYPOINT [ "python", "./application.py"]