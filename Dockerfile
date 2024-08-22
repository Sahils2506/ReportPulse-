# app/Dockerfile

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# RUN git clone https://github.com/streamlit/streamlit-example.git .
COPY . .

RUN pip3 install -r requirements.txt

#RUN mkdir /app/.streamlit/

#COPY .streamlit/secrets.toml /app/.streamlit/secrets.toml

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
EXPOSE 6379

CMD redis-server --daemonize yes && streamlit run report_pulse.py --server.port 8501 --server.address 0.0.0.0