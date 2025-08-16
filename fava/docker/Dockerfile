# Use a lightweight official Python image as the base.
# 'python:3.11-slim' is a good choice as it's smaller than the full image.
FROM python:3.12-slim


# Set the working directory inside the container.
# All subsequent commands will be run from this directory.
WORKDIR /app

# Copy the requirements file into the container.
# This is a common practice to take advantage of Docker's layer caching.
# If requirements.txt doesn't change, Docker won't re-run the `pip install` command.
COPY docker/requirements.txt .
# Install Fava and other dependencies from the requirements file.
# The '--no-cache-dir' flag saves space by not caching package downloads.
RUN pip install --no-cache-dir -r requirements.txt



# Expose the port Fava runs on (default is 5000).
EXPOSE 5000


CMD ["fava", "--host", "0.0.0.0", "--port", "5000", "/data/budget.beancount"]
