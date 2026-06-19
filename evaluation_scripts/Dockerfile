FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends rsync openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /work

EXPOSE 8888

CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--ServerApp.token=", \
     "--ServerApp.password=", \
     "--notebook-dir=/work"]
