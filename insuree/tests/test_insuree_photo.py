import uuid
from unittest import mock
from unittest.mock import PropertyMock

from django.test import TestCase
from core.forms import User
import time
from graphene import Schema
from graphene.test import Client
from insuree.apps import InsureeConfig
from insuree import schema as insuree_schema
from insuree.models import Insuree
from insuree.test_helpers import create_test_insuree
from location.models import UserDistrict
from core.services import create_or_update_interactive_user, create_or_update_core_user

from insuree.services import validate_insuree_number
from unittest.mock import ANY
from django.conf import settings


class InsureePhotoTest(TestCase):

    test_user = None
    _TEST_USER_NAME = None
    test_user_PASSWORD = None
    _TEST_DATA_USER = None

    photo_base64 = None
    test_photo_path, test_photo_uuid = None, None

    class BaseTestContext:
        def __init__(self, user):
            self.user = user
    @classmethod
    def setUpTestData(cls):
        cls._TEST_USER_NAME = "TestUserTest2"
        cls.test_user_PASSWORD = "TestPasswordTest2"
        cls._TEST_DATA_USER = {
            "username": cls._TEST_USER_NAME,
            "last_name": cls._TEST_USER_NAME,
            "password": cls.test_user_PASSWORD,
            "other_names": cls._TEST_USER_NAME,
            "user_types": "INTERACTIVE",
            "language": "en",
            "roles": [4],
        }
        cls.test_photo_path=InsureeConfig.insuree_photos_root_path
        cls.test_photo_uuid = str(uuid.uuid4())
        cls.photo_base64 = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEAAQMAAABmvDolAAAAA1BMVEW10NBjBBbqAAAAH0lEQVRoge3BAQ0AAADCoPdPbQ43oAAAAAAAAAAAvg0hAAABmmDh1QAAAABJRU5ErkJggg=="
        cls.test_user = cls.__create_user_interactive_core()
        cls.insuree = create_test_insuree()
        #Add the disctict on the user
        UserDistrict.objects.create(
            user = cls.test_user.i_user,
            location = cls.insuree.family.location.parent.parent,
            audit_user_id = -1
        )
        cls.test_user.i_user
        cls.row_sec = settings.ROW_SECURITY
        #settings.ROW_SECURITY = False

    #def tearDown(self) -> None:
        #settings.ROW_SECURITY = self.row_sec

    @classmethod
    def setUpClass(cls):
        # Signals are not automatically bound in unit tests
        super(InsureePhotoTest, cls).setUpClass()
        cls.schema = Schema(
            query=insuree_schema.Query,
            mutation=insuree_schema.Mutation
        )
        cls.insuree_client = Client(cls.schema)

        ##insuree_schema.bind_signals()

    def test_add_photo_save_db(self):
        result = self.__call_photo_mutation()
        self.assertEqual(self.insuree.photo.photo, self.photo_base64)

    def test_pull_photo_db(self):
        self.__call_photo_mutation()
        query_result = self.__call_photo_query()
        try:
            gql_photo = query_result['data']['insurees']['edges'][0]['node']['photo']
            self.assertEqual(gql_photo['photo'], self.photo_base64)
        except Exception as e:
            raise e


    def test_add_photo_save_files(self):
        self.__call_photo_mutation()
        self.assertEqual(self.insuree.photo.filename,
                         str(self.test_photo_uuid))


    def test_pull_photo_file_path(self):
        self.__call_photo_mutation()
        query_result = self.__call_photo_query()
        gql_photo = query_result['data']['insurees']['edges'][0]['node']['photo']
        self.assertEqual(gql_photo['photo'], self.photo_base64)
        

    def __call_photo_mutation(self):
        mutation = self.__update_photo_mutation()
        context = self.BaseTestContext(self.test_user)
        result = self.insuree_client.execute(mutation, context=context)
        self.insuree = Insuree.objects.get(pk=self.insuree.pk)
        return result

    def __call_photo_query(self):
        query = self.__get_insuree_query()
        context = self.BaseTestContext(self.test_user)
        return self.insuree_client.execute(query, context=context)

    def __update_photo_mutation(self):
        self.test_photo_uuid = str(uuid.uuid4()).lower()
        return f'''mutation
            {{
                updateInsuree(input: {{
                        clientMutationId: "{str(uuid.uuid4()).lower()}"          
                        clientMutationLabel: "Update insuree - {self.insuree.chf_id}"
                        uuid: "{str(self.insuree.uuid).lower()}" 
                        chfId: "{self.insuree.chf_id}"
                        lastName: "{self.insuree.last_name}"
                        otherNames: "{self.insuree.other_names}"
                        genderId: "M"
                        dob: "1950-07-12"
                        head: true
                        marital: "M"
                        status: "AC"
                        photo:{{
                            uuid: "{self.test_photo_uuid}"
                            officerId: {self.test_user.i_user_id}
                            date: "2022-06-21"
                            photo: "{self.photo_base64}"
                            }}
                        cardIssued:false
                        familyId: {self.insuree.family.id}
                        }})  
                {{
                    clientMutationId
                    internalId
                }}
            }}
        '''
    @classmethod
    def _get_or_create_user_api(cls):
        try:
            return User.objects.filter(username=cls._TEST_USER_NAME).get()
        except User.DoesNotExist:
            return cls.__create_user_interactive_core()
    @classmethod
    def __create_user_interactive_core(cls):
        data = cls._TEST_DATA_USER

        i_user, i_user_created = create_or_update_interactive_user(
            user_id=None, data=data, audit_user_id=999, connected=False
        )
        create_or_update_core_user(
            user_uuid=None, username=cls._TEST_USER_NAME, i_user=i_user)
        
        return User.objects.filter(username=cls._TEST_USER_NAME).get()

    def __get_insuree_query(self):
        return f'''
{{
    insurees(uuid:"{str(self.insuree.uuid).lower()}") {{
        pageInfo {{
            hasNextPage,
            hasPreviousPage,
            startCursor,
            endCursor
        }}
        edges {{
            node {{
                uuid,
                chfId,
                photo {{
                    id,
                    uuid,
                    date,
                    folder,
                    filename,
                    officerId,
                    photo
                }}
            }}
        }}
    }}
}}
'''
