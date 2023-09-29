FROM python:3

RUN mkdir -p /opt/src/owner
WORKDIR /opt/src/owner

COPY owner/migrate.py ./migrate.py
COPY owner/configuration.py ./configuration.py
COPY owner/models.py ./models.py
COPY owner/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT [ "python", "./migrate.py"]

