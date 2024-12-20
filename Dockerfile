FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000

# Add wait-for-it script
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Collect static files
RUN python manage.py collectstatic --noinput

# Use wait-for-it to wait for database before starting
CMD ["/wait-for-it.sh", "db:5432", "--timeout=30", "--strict", "--", "python", "manage.py", "runserver", "0.0.0.0:8000"]
