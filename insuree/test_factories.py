import factory

from insuree.apps import InsureeConfig
from insuree.models import Insuree, Family, Gender, InsureePhoto

base64_blank_jpg = """
/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL
/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8
QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2Jyg
gkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLD
xMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ
3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eH
l6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+
iiigD//2Q==
"""


class FamilyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Family

    validity_from = "2019-01-01"
    audit_user_id = -1


class InsureeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Insuree

    last_name = "Test Last"
    other_names = "First Second"
    # looked up at call time, not import time: create_test_gender seeds the table lazily
    gender = factory.LazyFunction(lambda: Gender.objects.get(code='M'))
    dob = "1972-08-09"
    card_issued = True
    validity_from = "2019-01-01"
    audit_user_id = -1


class InsureePhotoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InsureePhoto

    folder = factory.LazyFunction(lambda: InsureeConfig.insuree_photos_root_path)
    chf_id = "chfpic"
    date = "2020-01-01"
    validity_from = "2019-01-01"
    audit_user_id = -1
    photo = base64_blank_jpg
