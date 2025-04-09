FROM python:3.11-slim

WORKDIR /gtp-server
COPY . .

# install opencv dependencies
RUN apt-get update && apt-get install -y libglib2.0-0 libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

ENV SERVER_ENV=production

EXPOSE 4455

ENV PORT=4455

CMD ["python", "run.py"]