from insuree.models import Insuree, Family, Gender, InsureePhoto


def create_test_insuree(with_family=True, custom_props=None, family_custom_props={}):
    # insuree has a mandatory reference to family and family has a mandatory reference to insuree
    # So we first insert the family with a dummy id and then update it
    if with_family:
        family = Family.objects.create(
            validity_from="2019-01-01",
            head_insuree_id=1,  # dummy
            audit_user_id=-1,
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
            "head": True,
            "card_issued": True,
            "validity_from": "2019-01-01",
            "audit_user_id": -1,
            **(custom_props if custom_props else {})
        }
    )
    if with_family:
        family.head_insuree_id = insuree.id
        for k, v in family_custom_props.items():
            setattr(family, k, v)
        family.save()

    return insuree


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
            **(custom_props if custom_props else {})
        }
    )

    return photo
