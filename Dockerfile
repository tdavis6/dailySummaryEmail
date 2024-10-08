FROM python:3.12.6-slim

# Install cron
RUN apt-get update && apt-get install -y cron
RUN apt-get purge -y python-software-properties software-properties-common && apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir --root-user-action -r requirements.txt

# Add the cron job
RUN echo "* * * * * root /usr/local/bin/python /app/main.py" > /etc/cron.d/dailySummaryEmail

# Give execution rights on the cron job file
RUN chmod 0644 /etc/cron.d/dailySummaryEmail

# Set the permissions of /app files to allow them to be ran by the cronjob
RUN chmod a+x /app/*

# Apply cron job
RUN crontab /etc/cron.d/dailySummaryEmail

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
