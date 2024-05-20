# Use the official Python image from the Docker Hub
FROM python:3.12.1-alpine3.19

# Set the working directory
WORKDIR /app

COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Specify the command to run the Python script
CMD ["python", "kusho-jenkins.py"]
