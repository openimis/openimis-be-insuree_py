from insuree.apps import InsureeConfig
from insuree.models import Insuree, Family, Gender, InsureePhoto
from insuree.services import validate_insuree_number
from location.models import Location
import random

def create_test_insuree(with_family=True, is_head=False, custom_props=None, family_custom_props=None):
    # insuree has a mandatory reference to family and family has a mandatory reference to insuree
    # So we first insert the family with a dummy id and then update it
    #loof if it exists
    family = None
    location = None
    village = None
    ref = random.randrange(10000000, 99999999)
    while validate_insuree_number(ref) != []:
        ref = random.randrange(10000000, 99999999)
    if custom_props is not None and 'chf_id' in custom_props:
        ref=custom_props.pop('chf_id')
    insuree = Insuree.objects.filter(chf_id=ref, validity_to__isnull=True).first()
    if insuree is None:
        #managing location
        family_location = None
        if (family_custom_props and ("location" in family_custom_props or "location_id" in family_custom_props ) ):
            family_location = family_custom_props['location'] if 'location' in  family_custom_props else Location.objects.get(pk=family_custom_props['location_id'])
        
        qs_location = Location.objects.filter(type="V", validity_to__isnull=True)

        if custom_props and "current_village" in custom_props:
            village = custom_props.pop('current_village')
        elif custom_props and "current_village_id" in custom_props:
            village= qs_location.filter(current_village_id =custom_props.pop('current_village_id')).first()
        elif custom_props and "family" in custom_props:
            village = custom_props["family"].location
        elif  family_location:
            village =family_location
        else:    
            village=qs_location.first()
    
        family = get_from_custom_props(custom_props, 'family',  None)
        

        
        insuree = Insuree.objects.create(
                last_name = get_from_custom_props(custom_props, 'last_name',"last" ),
                other_names= get_from_custom_props(custom_props, 'other_names', "First Second"),
                family= family,
                gender= get_from_custom_props(custom_props, 'gender', Gender.objects.get(code='M')),
                dob=  get_from_custom_props(custom_props, 'dob', '1972-08-09'),
                chf_id= ref,
                head= is_head,
                card_issued= get_from_custom_props(custom_props, 'card_issued', True),
                validity_from= get_from_custom_props(custom_props, 'validity_from',"2019-01-01"),
                audit_user_id= get_from_custom_props(custom_props, 'audit_user_id',-1),
                current_village= village,
                **(custom_props if custom_props else {})
        )
    if with_family and family is None and insuree.family is None:
        if not family_custom_props:
            family_custom_props={}
        if 'head_insuree' not in family_custom_props and 'head_insuree_id' not in family_custom_props:
            family_custom_props['head_insuree']=insuree
        family_custom_props['location']=village
        family= create_test_family(custom_props=family_custom_props)
        insuree.family = family
        insuree.save()

    return insuree

def create_test_family(custom_props={}):
    family = None
    if custom_props and "id" in custom_props:
        family = Family.objects.filter(id=custom_props['id']).first()
    if family is None and  custom_props and "uuid" in custom_props:    
        family = Family.objects.filter(uuid=custom_props['uuid']).first()      
    if family is None:
        qs_location = Location.objects.filter(type="V")
        if custom_props and "location" in custom_props:
            location= custom_props.pop('location')
        elif custom_props and "location_id" in custom_props:
            location= qs_location.filter(location_id =custom_props.pop('location_id')).first()
        else:
            location=qs_location.filter(validity_to__isnull=True).first() 
            ## manage head
        head_insuree = custom_props.pop('head_insuree', Insuree.objects.filter(validity_to__isnull=True).first())    
            

        family = Family.objects.create(
            validity_from=get_from_custom_props(custom_props, 'validity_from',"2019-01-01"),
            audit_user_id=get_from_custom_props(custom_props, 'audit_user_id',-1),
            head_insuree= head_insuree,
            location=location,
            **(custom_props if custom_props else {})
        )
    return family



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
def get_from_custom_props( custom_props, elm, default):
    return custom_props.pop(elm) if custom_props and elm in custom_props else default

def create_test_photo(insuree_id, officer_id, custom_props=None):
    photo = InsureePhoto.objects.create(
        **{
            "insuree_id": insuree_id,
            "folder": InsureeConfig.insuree_photos_root_path,
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
