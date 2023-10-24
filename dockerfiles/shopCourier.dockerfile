FROM python:3

RUN mkdir -p /opt/src/courier
RUN mkdir -p /opt/src/courier/solidity
RUN mkdir - p /opt/src/courier/solidity/output

WORKDIR /opt/src/courier

COPY courier/application.py ./application.py
COPY courier/configuration.py ./configuration.py
COPY courier/models.py ./models.py
COPY courier/requirements.txt ./requirements.txt

COPY courier/solidity/ShopContract.sol ./solidity/ShopContract.sol
COPY courier/solidity/output/MyContract.abi ./solidity/output/MyContract.abi
COPY courier/solidity/output/MyContract.bin ./solidity/output/MyContract.bin

RUN pip install -r requirements.txt

ENV PYTHONPATH="/opt/src/courier"
ENTRYPOINT [ "python", "./application.py"]