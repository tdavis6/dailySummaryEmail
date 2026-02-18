# Use a lightweight Python base image
FROM python:3.14-slim

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the port Flask or Waitress will use
EXPOSE 8080

# Command to start the app
CMD ["python", "src/main.py"]
