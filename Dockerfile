FROM python:3.7
MAINTAINER Wenhui Zhou

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

ENV PYTHONPATH "${PYTHONPATH}:/app/al"

CMD ["gunicorn", "device_server:device_server", "-c", "./gunicorn.conf.py"]