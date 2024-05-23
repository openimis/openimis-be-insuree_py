from core.test_helpers import create_test_interactive_user
from rest_framework import status
from rest_framework.test import APITestCase
from dataclasses import dataclass
from graphql_jwt.shortcuts import get_token
from core.models import User
from django.conf import settings


@dataclass
class DummyContext:
    """ Just because we need a context to generate. """
    user: User


class ReportAPITests( APITestCase):

    admin_user = None
    admin_token = None
    EFO_URL = f'/{settings.SITE_ROOT()}report/enrolled_families/pdf/?locationId=34&dateFrom=2019-04-01&dateTo=2019-04-30'
    IFO_URL = f'/{settings.SITE_ROOT()}report/insuree_family_overview/pdf/?dateFrom=2023-11-01&dateTo=2023-12-31'
    IMP_URL = f'/{settings.SITE_ROOT()}report/insuree_missing_photo/pdf/'
    IME_URL = f'/{settings.SITE_ROOT()}report/insurees_pending_enrollment/pdf/?dateFrom=2019-04-01&dateTo=2019-04-30&officerId=1&locationId=20'
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))
        
    def test_single_enrolled_families_report(self):
        headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        response = self.client.get(self.EFO_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_single_insuree_family_overview_report(self):
        headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        response = self.client.get(self.IFO_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_single_insuree_missing_photo_report(self):
        headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        response = self.client.get(self.IMP_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_single_insurees_pending_enrollment_report(self):
        headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        response = self.client.get(self.IME_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
