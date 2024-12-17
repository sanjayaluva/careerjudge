from datetime import datetime
from django.urls.converters import IntConverter

class DateConverter:
    regex = '\d{4}-\d{1,2}-\d{1,2}'
    format = '%Y-%m-%d'

    def to_python(self, value):
        return datetime.strptime(value, self.format).date()

    def to_url(self, value):
        return value.strftime(self.format)

class EmptyOrIntConverter(IntConverter):
    regex = '[-a-zA-Z0-9_]*'
