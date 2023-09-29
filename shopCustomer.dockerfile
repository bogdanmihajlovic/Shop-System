FROM python:3

RUN mkdir -p /opt/src/customer
RUN mkdir -p /opt/src/customer/solidity
RUN mkdir - p /opt/src/customer/solidity/output

WORKDIR /opt/src/customer

COPY customer/application.py ./application.py
COPY customer/configuration.py ./configuration.py
COPY customer/models.py ./models.py
COPY customer/requirements.txt ./requirements.txt

COPY customer/solidity/output/MyContract.abi ./solidity/output/MyContract.abi
COPY customer/solidity/output/MyContract.bin ./solidity/output/MyContract.bin

RUN pip install -r requirements.txt


ENV PYTHONPATH="/opt/src/customer"
ENTRYPOINT [ "python", "./application.py"]
