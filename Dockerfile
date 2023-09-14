FROM apache/airflow:2.7.1
# Install Additional Python Dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt