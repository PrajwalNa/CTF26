FROM python:3.11-slim

WORKDIR /app

COPY customISA.py .
COPY server.py .
COPY journey.rune .

EXPOSE 666

CMD ["python", "-u", "server.py"]
# docker build -t unknown-runes .
# docker run -p 666:666 --rm --name runes unknown-runes