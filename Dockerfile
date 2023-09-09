FROM apache/airflow:2.7.1
# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge --auto-remove -y curl \
    && rm -rf /src/*.deb
# Install Additional Python Dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt