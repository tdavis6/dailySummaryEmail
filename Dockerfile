# Use a lightweight Python base image
FROM python:3.14-slim@sha256:486b8092bfb12997e10d4920897213a06563449c951c5506c2a2cfaf591c599f

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
