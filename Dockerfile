# Use the official Python image from the Docker Hub
FROM ubuntu:22.04

SHELL ["/bin/bash", "-c"]

RUN apt-get update -q -y && DEBIAN_FRONTEND="noninteractive" apt-get install --yes python3-pip python3-opencv tesseract-ocr git-all curl unzip



# Set the working directory
WORKDIR /app

# Copy the rest of the application code into the container
COPY . .


RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:${PATH}"
WORKDIR /app/node_executor
RUN bun install
RUN bun build src/cli.ts --compile --outfile node_executor 

WORKDIR /app/


COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt


# Specify the command to run the Python script
CMD ["python3", "kusho-jenkins.py"]
