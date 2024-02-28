# Based on python image which itself is based on debian image
# https://hub.docker.com/_/python
# https://hub.docker.com/_/debian
FROM python:3.9-slim

# Maintainer information
LABEL maintainer="Dribdat <dribdat@datalets.ch>"

# Environment
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Copy pip requirements
COPY requirements.txt .
COPY requirements/* requirements/

# Install compiler (used by some pip packages)
RUN : \
    && apt-get update \
    && apt-get install gcc make libev-dev libuv1-dev libc-ares-dev -y \
    && apt-get clean 

# Install requirements
RUN : \
    && python -m pip install --upgrade pip \
    && EMBED=0 pip install gevent \
    && python -m pip install -r requirements.txt \
    
    # Clean up after build
    && apt-get purge --auto-remove -y


# Copy app files (please see dockerignore)
COPY . /app

# Run commands
RUN set -x \
    && mkdir /docker-entrypoint.d \
    && mv /app/image/docker-entrypoint.d/* /docker-entrypoint.d/ \
    && mv /app/image/docker-entrypoint.sh /docker-entrypoint.sh \
    && chmod +x /docker-entrypoint.sh \
    # Creates a non-root user with an explicit UID and adds permission to access the /app folder
    && adduser --uid 5678 --disabled-password --gecos "" appuser \
    && chown -R appuser /app \
    && chown -R appuser /docker-entrypoint.d \
    && chown appuser /docker-entrypoint.sh 

WORKDIR /app
USER appuser

ENTRYPOINT ["/docker-entrypoint.sh"]
EXPOSE 5000
CMD ["gunicorn","--config=gunicorn.conf.py","patched:init_app()"]



