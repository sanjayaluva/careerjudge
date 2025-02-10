FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Add wait-for-it script for database readiness
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Use wait-for-it to wait for database before starting
CMD ["/wait-for-it.sh", "db:5432", "--timeout=30", "--strict", "--", "python", "manage.py", "runserver", "0.0.0.0:8000"]
