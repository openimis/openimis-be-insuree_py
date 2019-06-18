from django.db import models
from core import fields
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


class Family(models.Model):
    id = models.AutoField(db_column='FamilyID', primary_key=True)
    legacy_id = models.IntegerField(
        db_column='LegacyID', blank=True, null=True)
    insuree = models.ForeignKey(
        'Insuree', models.DO_NOTHING, db_column='InsureeID')
    location = models.ForeignKey(
        location_models.Location, models.DO_NOTHING, db_column='LocationId', blank=True, null=True)
    poverty = models.BooleanField(db_column='Poverty', blank=True, null=True)
    validity_from = models.DateTimeField(db_column='ValidityFrom')
    validity_to = models.DateTimeField(
        db_column='ValidityTo', blank=True, null=True)

    # type = models.ForeignKey('Tblfamilytypes', models.DO_NOTHING, db_column='FamilyType', blank=True, null=True)
    address = models.CharField(
        db_column='FamilyAddress', max_length=200, blank=True, null=True)
    is_offline = models.BooleanField(
        db_column='isOffline', blank=True, null=True)
    ethnicity = models.CharField(
        db_column='Ethnicity', max_length=1, blank=True, null=True)
    confirmation_no = models.CharField(
        db_column='ConfirmationNo', max_length=12, blank=True, null=True)
    # confirmation_type = models.ForeignKey(Tblconfirmationtypes, models.DO_NOTHING, db_column='ConfirmationType', blank=True, null=True)

    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # rowid = models.TextField(db_column='RowID', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblFamilies'


class Insuree(models.Model):
    id = models.AutoField(db_column='InsureeID', primary_key=True)
    legacy_id = models.IntegerField(
        db_column='LegacyID', blank=True, null=True)

    # familyid = models.ForeignKey(Tblfamilies, models.DO_NOTHING, db_column='FamilyID')
    chf_id = models.CharField(
        db_column='CHFID', max_length=12, blank=True, null=True)
    last_name = models.CharField(db_column='LastName', max_length=100)
    other_names = models.CharField(db_column='OtherNames', max_length=100)

    gender = models.ForeignKey(
        Gender, models.DO_NOTHING, db_column='Gender', blank=True, null=True)
    dob = fields.DateField(db_column='DOB')

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
    # photoid = models.ForeignKey('Tblphotos', models.DO_NOTHING, db_column='PhotoID', blank=True, null=True)
    photo_date = fields.DateField(db_column='PhotoDate', blank=True, null=True)
    card_issued = models.BooleanField(db_column='CardIssued')

    # relationship = models.ForeignKey('Tblrelations', models.DO_NOTHING, db_column='Relationship', blank=True, null=True)
    # profession = models.ForeignKey('Tblprofessions', models.DO_NOTHING, db_column='Profession', blank=True, null=True)
    # education = models.ForeignKey(Tbleducations, models.DO_NOTHING, db_column='Education', blank=True, null=True)

    # typeofid = models.ForeignKey(Tblidentificationtypes, models.DO_NOTHING, db_column='TypeOfId', blank=True, null=True)
    health_facility = models.ForeignKey(location_models.HealthFacility, models.DO_NOTHING,
                                        db_column='HFID', blank=True, null=True)

    validity_from = fields.DateTimeField(db_column='ValidityFrom')
    validity_to = fields.DateTimeField(
        db_column='ValidityTo', blank=True, null=True)

    offline = models.BooleanField(db_column='isOffline', blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # row_id = models.BinaryField(db_column='RowID', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblInsuree'
