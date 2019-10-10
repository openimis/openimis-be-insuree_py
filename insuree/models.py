from django.db import models
import core
import uuid
from location import models as location_models


class Gender(models.Model):
    code = models.CharField(db_column='Code', primary_key=True, max_length=1)
    gender = models.CharField(
        db_column='Gender', max_length=50, blank=True, null=True)
    alt_language = models.CharField(
        db_column='AltLanguage', max_length=50, blank=True, null=True)
    sort_order = models.IntegerField(
        db_column='SortOrder', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblGender'


class Photo(models.Model):
    id = models.AutoField(db_column='PhotoID', primary_key=True)
    uuid = models.CharField(db_column='PhotoUUID',
                            max_length=36, default=uuid.uuid4, unique=True)
    insuree_id = models.IntegerField(
        db_column='InsureeID', blank=True, null=True)
    chf_id = models.CharField(
        db_column='CHFID', max_length=12, blank=True, null=True)
    folder = models.CharField(db_column='PhotoFolder', max_length=255)
    filename = models.CharField(
        db_column='PhotoFileName', max_length=250, blank=True, null=True)
    officer_id = models.IntegerField(db_column='OfficerID')
    date = core.fields.DateField(db_column='PhotoDate')
    validity_from = core.fields.DateTimeField(db_column='ValidityFrom')
    validity_to = core.fields.DateTimeField(
        db_column='ValidityTo', blank=True, null=True)
    audit_user_id = models.IntegerField(
        db_column='AuditUserID', blank=True, null=True)
    # rowid = models.TextField(db_column='RowID', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblPhotos'


class FamilyType(models.Model):
    code = models.CharField(
        db_column='FamilyTypeCode', primary_key=True, max_length=2)
    type = models.CharField(db_column='FamilyType', max_length=50)
    sort_order = models.IntegerField(
        db_column='SortOrder', blank=True, null=True)
    alt_language = models.CharField(
        db_column='AltLanguage', max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblFamilyTypes'


class Family(models.Model):
    id = models.AutoField(db_column='FamilyID', primary_key=True)
    uuid = models.CharField(db_column='FamilyUUID',
                            max_length=36, default=uuid.uuid4, unique=True)
    legacy_id = models.IntegerField(
        db_column='LegacyID', blank=True, null=True)
    head_insuree = models.OneToOneField(
        'Insuree', models.DO_NOTHING, db_column='InsureeID', related_name='head_of')
    # locationid = models.ForeignKey('Tbllocations', models.DO_NOTHING, db_column='LocationId', blank=True, null=True)
    poverty = models.BooleanField(db_column='Poverty', blank=True, null=True)
    family_type = models.ForeignKey(
        FamilyType, models.DO_NOTHING, db_column='FamilyType', blank=True, null=True)
    address = models.CharField(
        db_column='FamilyAddress', max_length=200, blank=True, null=True)
    is_offline = models.BooleanField(
        db_column='isOffline', blank=True, null=True)
    ethnicity = models.CharField(
        db_column='Ethnicity', max_length=1, blank=True, null=True)
    confirmation_no = models.CharField(
        db_column='ConfirmationNo', max_length=12, blank=True, null=True)
    # confirmation_type = models.ForeignKey(
    #     Tblconfirmationtypes, models.DO_NOTHING, db_column='ConfirmationType', blank=True, null=True)
    validity_from = core.fields.DateTimeField(db_column='ValidityFrom')
    validity_to = core.fields.DateTimeField(
        db_column='ValidityTo', blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # rowid = models.TextField(db_column='RowID', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblFamilies'


class Insuree(models.Model):
    id = models.AutoField(db_column='InsureeID', primary_key=True)
    uuid = models.CharField(db_column='InsureeUUID',
                            max_length=36, default=uuid.uuid4, unique=True)
    legacy_id = models.IntegerField(
        db_column='LegacyID', blank=True, null=True)

    family = models.ForeignKey(
        Family, models.DO_NOTHING, db_column='FamilyID', related_name="members")
    chf_id = models.CharField(
        db_column='CHFID', max_length=12, blank=True, null=True)
    last_name = models.CharField(db_column='LastName', max_length=100)
    other_names = models.CharField(db_column='OtherNames', max_length=100)

    gender = models.ForeignKey(
        Gender, models.DO_NOTHING, db_column='Gender', blank=True, null=True)
    dob = core.fields.DateField(db_column='DOB')

    def age(self, reference_date=None):
        if self.dob:
            today = core.datetime.date.today() if reference_date is None else reference_date
            before_birthday = (today.month, today.day) < (
                self.dob.month, self.dob.day)
            return today.year - self.dob.year - before_birthday
        else:
            return None

    def is_adult(self, reference_date=None):
        if self.dob:
            return self.age() >= core.age_of_majority
        else:
            return None

    head = models.BooleanField(db_column='IsHead')
    marital = models.CharField(
        db_column='Marital', max_length=1, blank=True, null=True)

    passport = models.CharField(max_length=25, blank=True, null=True)
    phone = models.CharField(
        db_column='Phone', max_length=50, blank=True, null=True)
    email = models.CharField(
        db_column='Email', max_length=100, blank=True, null=True)
    current_address = models.CharField(
        db_column='CurrentAddress', max_length=200, blank=True, null=True)
    geolocation = models.CharField(
        db_column='GeoLocation', max_length=250, blank=True, null=True)
    current_village = models.IntegerField(
        db_column='CurrentVillage', blank=True, null=True)
    photo = models.ForeignKey(Photo, models.DO_NOTHING,
                              db_column='PhotoID', blank=True, null=True)
    photo_date = core.fields.DateField(
        db_column='PhotoDate', blank=True, null=True)
    card_issued = models.BooleanField(db_column='CardIssued')

    # relationship = models.ForeignKey('Tblrelations', models.DO_NOTHING, db_column='Relationship', blank=True, null=True)
    # profession = models.ForeignKey('Tblprofessions', models.DO_NOTHING, db_column='Profession', blank=True, null=True)
    # education = models.ForeignKey(Tbleducations, models.DO_NOTHING, db_column='Education', blank=True, null=True)

    # typeofid = models.ForeignKey(Tblidentificationtypes, models.DO_NOTHING, db_column='TypeOfId', blank=True, null=True)
    health_facility = models.ForeignKey(location_models.HealthFacility, models.DO_NOTHING,
                                        db_column='HFID', blank=True, null=True)

    validity_from = core.fields.DateTimeField(db_column='ValidityFrom')
    validity_to = core.fields.DateTimeField(
        db_column='ValidityTo', blank=True, null=True)

    offline = models.BooleanField(db_column='isOffline', blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # row_id = models.BinaryField(db_column='RowID', blank=True, null=True)

    def __str__(self):
        return self.chf_id + " " + self.last_name + " " + self.other_names

    class Meta:
        managed = False
        db_table = 'tblInsuree'


class InsureePolicy(models.Model):
    id = models.AutoField(db_column='InsureePolicyID', primary_key=True)
    legacy_id = models.IntegerField(
        db_column='LegacyID', blank=True, null=True)

    insuree = models.ForeignKey(
        Insuree, models.DO_NOTHING, db_column='InsureeId', related_name="insuree_policies")
    policy = models.ForeignKey("policy.Policy", models.DO_NOTHING, db_column='PolicyId',
                               related_name="insuree_policies")

    enrollment_date = core.fields.DateField(
        db_column='EnrollmentDate', blank=True, null=True)
    start_date = core.fields.DateField(
        db_column='StartDate', blank=True, null=True)
    effective_date = core.fields.DateField(
        db_column='EffectiveDate', blank=True, null=True)
    expiry_date = core.fields.DateField(
        db_column='ExpiryDate', blank=True, null=True)

    validity_from = core.fields.DateTimeField(db_column='ValidityFrom')
    validity_to = core.fields.DateTimeField(
        db_column='ValidityTo', blank=True, null=True)

    offline = models.BooleanField(db_column='isOffline', blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # row_id = models.BinaryField(db_column='RowID', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblInsureePolicy'
