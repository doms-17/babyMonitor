# MyBabyMonitor

IoT Project: for comprehensive details about this project, please refer to the relazione_final_iot.pdf file.

## Getting Started

### Prerequisites

- Python 3.8+
- Docker

### Building
- Build the images of each system component using the command:
```bash
docker build -t catalog .
```
```bash
docker build -t bot .
```
```bash
docker build -t seizure .
```
```bash
docker build -t apnea .
```
```bash
docker build -t raspberry .
```
```bash
docker build -t monitoring .
```

- Run the docker-compose.yml file:
```bash
docker-compose up
```
