from insuree.models import Insuree, Family, Gender, InsureePhoto


def create_test_insuree(with_family=True, is_head=False, custom_props=None, family_custom_props=None):
    # insuree has a mandatory reference to family and family has a mandatory reference to insuree
    # So we first insert the family with a dummy id and then update it
    if with_family:
        family = Family.objects.create(
            validity_from="2019-01-01",
            head_insuree_id=1,  # dummy
            audit_user_id=-1,
            **(family_custom_props if family_custom_props else {})
        )
    else:
        family = None

    insuree = Insuree.objects.create(
        **{
            "last_name": "Test Last",
            "other_names": "First Second",
            "chf_id": "chf_dflt",
            "family": family,
            "gender": Gender.objects.get(code='M'),
            "dob": "1970-01-01",
            "head": is_head,
            "card_issued": True,
            "validity_from": "2019-01-01",
            "audit_user_id": -1,
            **(custom_props if custom_props else {})
        }
    )
    if with_family:
        family.head_insuree_id = insuree.id
        if family_custom_props:
            for k, v in family_custom_props.items():
                setattr(family, k, v)
        family.save()

    return insuree


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


def create_test_photo(insuree_id, officer_id, custom_props=None):
    photo = InsureePhoto.objects.create(
        **{
            "insuree_id": insuree_id,
            "folder": "images/insurees/",
            "officer_id": officer_id,
            "chf_id": "chfpic",
            "date": "2020-01-01",
            "validity_from": "2019-01-01",
            "audit_user_id": -1,
            "photo": base64_blank_jpg,
            **(custom_props if custom_props else {})
        }
    )

    return photo
