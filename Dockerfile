FROM apache/airflow:2.10.5
USER airflow
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
USER airflow

# Install dependencies
USER root
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg2 \
    ca-certificates

# Install Google Chrome
RUN wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y /tmp/chrome.deb || apt --fix-broken install -y && \
    rm /tmp/chrome.deb