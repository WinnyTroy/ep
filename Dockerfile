# Image from dockerhub
FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1 
# Expose the port 8000 in which our application runs
EXPOSE 8000
# Make /app as a working directory in the container
WORKDIR /usr/src/
# Copy requirements from host, to docker container in /app 
COPY ./dev-requirements.txt .
# Copy everything from ./src directory to /app in the container
COPY ./ .
# Install the dependencies
RUN pip install -r dev-requirements.txt
# Run the application in the port 8000
CMD ["uvicorn", "credit_notes.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
