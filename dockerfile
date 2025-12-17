FROM repository.medfutura.com.br/python-chrome-image:latest
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
