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
    SINGLE_CLAIM_URL = f'/{settings.SITE_ROOT()}report/insuree_family_overview/pdf/?dateFrom=2023-11-01&dateTo=2023-12-31'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))
        
    def test_single_claim_report(self):
        headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        response = self.client.get(self.SINGLE_CLAIM_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)