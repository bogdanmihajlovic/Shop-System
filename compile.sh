#!/bin/bash

file_path=$1
fullpath=echo pwd

rm -r -f ./solidity/output
docker run -v $PWD/solidity:/sources ethereum/solc:0.8.18 -o /sources/output --abi --bin --asm-json /sources/$file_path


