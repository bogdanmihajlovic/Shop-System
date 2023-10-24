# Shop-System

This repository contains Dockerfiles and configuration files to set up the Shop-System using Docker Compose.

## Docker Build

To build the necessary Docker images, navigate to the `dockerfiles` directory and run the following commands:

```bash
cd dockerfiles
docker build -f authenticationDBMigration.dockerfile --tag authenticationdbmigration .
docker build -f authentication.dockerfile --tag authentication .
docker build -f shopDBMigration.dockerfile --tag shopdbmigration .
docker build -f shopOwner.dockerfile --tag owner .
docker build -f shopCustomer.dockerfile --tag customer .
docker build -f shopCourier.dockerfile --tag courier .
cd ..
```

## Spark Application

To build the Spark application, navigate to the spark directory and run the following command:
```bash

cd spark
docker build -f application.dockerfile --tag sparkapp .
cd ..
```

## Docker Compose

To deploy the Shop-System, use the Docker Compose configuration files. Run the following commands:

For Authentication:

```bash
docker-compose -f authDeployment.yaml up
```

For the Shop System:

```bash
docker-compose -f shopDeployment.yaml up
```
