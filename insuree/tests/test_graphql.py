import base64
import json
from dataclasses import dataclass
from django.utils.translation import gettext as _
from core.models import User, filter_validity
from core.test_helpers import create_test_interactive_user
from django.conf import settings
from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token
from location.models import Location
from location.test_helpers import create_test_location, assign_user_districts
from rest_framework import status
from insuree.test_helpers import create_test_insuree
from location.test_helpers import create_test_location, create_test_health_facility, create_test_village
from insuree.models import Family


# from openIMIS import schema


@dataclass
class DummyContext:
    """ Just because we need a context to generate. """
    user: User


class InsureeGQLTestCase(GraphQLTestCase):
    GRAPHQL_URL = f'/{settings.SITE_ROOT()}graphql'
    # This is required by some version of graphene but is never used. It should be set to the schema but the import
    # is shown as an error in the IDE, so leaving it as True.
    GRAPHQL_SCHEMA = True
    admin_user = None
    ca_user = None
    ca_token = None
    test_village = None
    test_insuree = None
    test_photo = None
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_village = create_test_village()
        cls.test_insuree = create_test_insuree(with_family=True, is_head=True, custom_props={'current_village':cls.test_village}, family_custom_props={'location':cls.test_village})
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))
        cls.ca_user = create_test_interactive_user(username="testLocationNoRight", roles=[9])
        cls.ca_token = get_token(cls.ca_user, DummyContext(user=cls.ca_user))
        cls.admin_dist_user = create_test_interactive_user(username="testLocationDist")
        assign_user_districts(cls.admin_dist_user, ["R1D1", "R2D1", "R2D2", "R2D1", cls.test_village.parent.parent.code])
        cls.admin_dist_token = get_token(cls.admin_dist_user, DummyContext(user=cls.admin_dist_user))
        cls.photo_base64 = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEAAQMAAABmvDolAAAAA1BMVEW10NBjBBbqAAAAH0lEQVRoge3BAQ0AAADCoPdPbQ43oAAAAAAAAAAAvg0hAAABmmDh1QAAAABJRU5ErkJggg=="

    def test_query_insuree_number_validity(self):
        response = self.query(
            '''
            {
                insureeNumberValidity(insureeNumber:"123456782")
                {
                  isValid
                  errorCode
                  errorMessage
                }
            }
            ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"},
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        




    def test_insuree_query(self):
        
        response = self.query(
            '''
            query {
                
      insurees
      {
        totalCount
        
    pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor}
    edges
    {
      node
      {
        id,uuid,validityFrom,validityTo,chfId,otherNames,lastName,phone,gender{code},dob,marital,status,family{uuid,location{id, uuid, code, name, type, parent{id,uuid,code,name,type,parent{id,uuid,code,name,type,parent{id,uuid,code,name,type}}}}},currentVillage{id, uuid, code, name, type, parent{id,uuid,code,name,type,parent{id,uuid,code,name,type,parent{id,uuid,code,name,type}}}}
      }
    }
      }
    
            }
            ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_dist_user}"},

        )

        content = json.loads(response.content)

        # This validates the status code and if you get errors
        self.assertEqual(content['errors'][0]['message'],_('unauthorized'))



    def test_family_query(self):
        
        response = self.query(
            '''
            query {

      families(first: 10,orderBy: ["-validityFrom"])
      {
        totalCount
        
    pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor}
    edges
    {
      node
      {
        id,uuid,poverty,confirmationNo,validityFrom,validityTo,headInsuree{id,uuid,chfId,lastName,otherNames,email,phone, dob},location{id, uuid, code, name, type, parent{id,uuid,code,name,type,parent{id,uuid,code,name,type,parent{id,uuid,code,name,type}}}}
      }
    }
      }
    }

            ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_dist_user}"},

        )

        content = json.loads(response.content)

        # This validates the status code and if you get errors
        self.assertEqual(content['errors'][0]['message'],_('unauthorized'))



    def test_query_with_variables(self):
        response = self.query(
            '''
    
            query insurees( $first:  Int! ) 
    {
      insurees(first: $first,orderBy: ["chfId"])
      {
        totalCount
        
    pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor}
    edges
    {
      node
      {
        id,uuid,validityFrom,validityTo,chfId,otherNames,lastName,phone,gender{code},dob,marital,status,family{uuid,location{id, uuid, code, name, type, parent{id,uuid,code,name,type,parent{id,uuid,code,name,type,parent{id,uuid,code,name,type}}}}},currentVillage{id, uuid, code, name, type, parent{id,uuid,code,name,type,parent{id,uuid,code,name,type,parent{id,uuid,code,name,type}}}}
      }
    }
      }
    }
            ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"},
            variables={ 'first':10}
        )

        content = json.loads(response.content)

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)

    def test_query_ignore_location(self):
        
      response = self.query(
            '''
    query insurees( $chfid:  String!, $ignoreLocation : Boolean! )    
    {
      insurees(chfId:$chfid, ignoreLocation:$ignoreLocation)
      {
        pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor}
        edges
        {
          node
          {
            id,uuid,chfId,lastName,otherNames,dob,age,validityFrom,validityTo,gender{code},status,family{id, uuid, address location{name, parent{name, parent{name}}}},photo{folder,filename,photo},gender{code, gender, altLanguage},healthFacility{id, uuid, code, name, level, servicesPricelist{id, uuid}, itemsPricelist{id, uuid}, contractStartDate, contractEndDate, location{id,uuid,code,name,type, parent{id,uuid,code,name,type}}}
          }
        }
      }
    }
            ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_dist_token}"},
            variables={ 'chfid':self.test_insuree.chf_id, 'ignoreLocation':True}
        )

      content = json.loads(response.content)

    # This validates the status code and if you get errors
      self.assertResponseNoErrors(response)

    def test_create_insuree(self):
      response = self.query(f'''
    mutation {{
      createInsuree(
        input: {{
          clientMutationId: "ffa465c5-6807-4de0-847e-202b7f42122b"
          clientMutationLabel: "Create insuree - 12343456234"
          
          chfId: "12343456234"
    lastName: "test"
    otherNames: "create insuree"
    genderId: "M"
    dob: "1951-12-05"
    head: false
    marital: "N"
    currentVillageId: {self.test_village.id}
    photo:{{
    officerId: 1
    date: "2023-12-15"
    photo: "{self.photo_base64}"
  }}
    cardIssued:false
    status: "AC"
        }}
      ) {{
        clientMutationId
        internalId
      }}
    }}
    ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_dist_token}"},
        )

      content = json.loads(response.content)

    # This validates the status code and if you get errors
      self.assertResponseNoErrors(response)
      
      
      
    def test_create_family(self):
      response = self.query(f'''
    mutation {{
      createFamily(
        input: {{
          clientMutationId: "50f8f2c9-7685-4cd5-a7d8-b1fa78d46470"
          clientMutationLabel: "Create Family - test create family (445566778899)"
          headInsuree: {{
    chfId: "4455667788"
    lastName: "test"
    otherNames: "create family"
    genderId: "M"
    uuid: "50f8f2c9-7685-4cd5-a778-b1fa78d46470"
    dob: "1999-12-15"
    head: true
    photo:{{
    officerId: 1
    date: "2023-12-15"
    photo: "{self.photo_base64}"

  }}
    cardIssued:false
    status: "AC"
  }}
    locationId: {self.test_village.id}
    poverty: false
    uuid: "50f8f2c9-7685-4cd5-a7d8-b1fa78d46475"
    jsonExt: "{{}}"
        }}
      ) {{
        clientMutationId
        internalId
      }}
    }}
      ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_dist_token}"},
        )

      content = json.loads(response.content)

    # This validates the status code and if you get errors
      self.assertResponseNoErrors(response)
      
      # update
      response = self.query(f'''
    mutation {{
      updateFamily(
        input: {{
          clientMutationId: "50f8f2c9-7685-4cd5-a778-b1fa78d46470"
          clientMutationLabel: "Update Family - test create family (445566778899)"
          headInsuree: {{
    chfId: "4455667788"
    uuid: "50f8f2c9-7685-4cd5-a778-b1fa78d46470"
    lastName: "test"
    otherNames: "create family"
    genderId: "M"
    dob: "1999-12-15"
    head: true
    photo:{{
    officerId: 1
    date: "2023-12-15"
    photo: "{self.photo_base64}"

  }}
    cardIssued:false
    status: "AC"
  }}
    locationId: {self.test_village.id}
    poverty: true
    uuid: "50f8f2c9-7685-4cd5-a7d8-b1fa78d46475"
    jsonExt: "{{}}"
        }}
      ) {{
        clientMutationId
        internalId
      }}
    }}
      ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_dist_token}"},
        )

      content = json.loads(response.content)

    # This validates the status code and if you get errors
      self.assertResponseNoErrors(response)
            
      family = Family.objects.filter(*filter_validity(),uuid= "50f8f2c9-7685-4cd5-a7d8-b1fa78d46475").first()
      self.assertEqual(family.poverty, True)

      