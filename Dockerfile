FROM python:3.12-bullseye
RUN pip install discord
COPY src/ app/
CMD ["python", "-u", "app/main.py"]
