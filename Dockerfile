# Use an official Python runtime as a parent image
FROM python:3.8.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
# RUN pip install --trusted-host mirrors.aliyun.com -r requirements-predication.txt --no-cache-dir    
# RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
# ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]