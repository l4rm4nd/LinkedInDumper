FROM python:3.12.4-alpine
LABEL Maintainer="LRVT"

COPY requirements.txt linkedindumper.py /app/.
RUN pip3 install -r /app/requirements.txt

WORKDIR /app
ENTRYPOINT [ "python", "linkedindumper.py"]

CMD [ "python", "linkedindumper.py", "--help"]
