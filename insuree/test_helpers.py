from insuree.models import Insuree, Family, Gender


def create_test_insuree(valid=True, with_family=True, custom_props=None):
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
        family.save()

    return insuree
