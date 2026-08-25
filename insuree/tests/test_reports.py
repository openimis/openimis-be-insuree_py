from core.test_helpers import create_test_interactive_user, create_test_role, create_admin_role
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
from django.db import connection
from core.models.openimis_graphql_test_case import BaseTestContext


class ReportAPITests(APITestCase):

    admin_user = None
    admin_token = None
    EFO_URL = f'/{settings.SITE_ROOT()}report/enrolled_families/pdf/?locationId=34&dateFrom=2019-04-01&dateTo=2019-04-30'
    IFO_URL = f'/{settings.SITE_ROOT()}report/insuree_family_overview/pdf/?dateFrom=2023-11-01&dateTo=2023-12-31'
    IMP_URL = f'/{settings.SITE_ROOT()}report/insuree_missing_photo/pdf/'
    IME_URL = f'/{settings.SITE_ROOT()}report/insurees_pending_enrollment/pdf/?dateFrom=2019-04-01&dateTo=2019-04-30&officerId=1&locationId=20'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(
            username="testLocationAdmin", roles=[create_admin_role().id])
        cls.admin_token = BaseTestContext(user=cls.admin_user).get_jwt()

    def test_single_enrolled_families_report(self):
        report_role = create_test_role(perm_names=[
                                       "gql_reports_families_insurees_overview_perms"], name="EnrolledFamiliesReportRole")
        report_user = create_test_interactive_user(
            username="testEnrolledFamiliesUser", roles=[report_role.id])
        report_token = BaseTestContext(user=report_user).get_jwt()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {report_token}"}
        response = self.client.get(self.EFO_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_single_enrolled_families_report_access_denied(self):
        # Test that a user without proper permissions gets access denied
        empty_role = create_test_role(perm_names=[], name="EmptyRole")
        unauthorized_user = create_test_interactive_user(
            username="testUnauthorizedUser", roles=[empty_role.id])
        unauthorized_token = BaseTestContext(user=unauthorized_user).get_jwt()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {unauthorized_token}"}
        response = self.client.get(self.EFO_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_single_insuree_family_overview_report(self):
        report_role = create_test_role(perm_names=[
                                       "gql_reports_families_insurees_overview_perms"], name="InsureeFamilyOverviewReportRole")
        report_user = create_test_interactive_user(
            username="testReportUser", roles=[report_role.id])
        report_token = BaseTestContext(user=report_user).get_jwt()
        with self.settings(ROW_SECURITY=True):
            headers = {"HTTP_AUTHORIZATION": f"Bearer {report_token}"}
            response = self.client.get(self.IFO_URL, format='json', **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_insuree_family_overview_report_access_denied(self):
        # Test that a user without proper permissions gets access denied
        empty_role = create_test_role(perm_names=[], name="EmptyRole")
        unauthorized_user = create_test_interactive_user(
            username="testUnauthorizedUser", roles=[empty_role.id])
        unauthorized_token = BaseTestContext(user=unauthorized_user).get_jwt()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {unauthorized_token}"}
        response = self.client.get(self.IFO_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_single_insuree_missing_photo_report(self):
        if not connection.vendor == 'postgresql':
            self.skipTest("This test can only be executed for PSQL database")
        report_role = create_test_role(perm_names=[
                                       "gql_reports_families_insurees_overview_perms"], name="InsureeMissingPhotoReportRole")
        report_user = create_test_interactive_user(
            username="testMissingPhotoUser", roles=[report_role.id])
        report_token = BaseTestContext(user=report_user).get_jwt()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {report_token}"}
        response = self.client.get(self.IMP_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_single_insuree_missing_photo_report_access_denied(self):
        # Test that a user without proper permissions gets access denied
        empty_role = create_test_role(perm_names=[], name="EmptyRole")
        unauthorized_user = create_test_interactive_user(
            username="testUnauthorizedUser", roles=[empty_role.id])
        unauthorized_token = BaseTestContext(user=unauthorized_user).get_jwt()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {unauthorized_token}"}
        response = self.client.get(self.IMP_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_single_insurees_pending_enrollment_report(self):
        if not connection.vendor == 'postgresql':
            self.skipTest("This test can only be executed for PSQL database")
        report_role = create_test_role(perm_names=[
                                       "gql_reports_families_insurees_overview_perms"], name="InsureesPendingEnrollmentReportRole")
        report_user = create_test_interactive_user(
            username="testPendingEnrollmentUser", roles=[report_role.id])
        report_token = BaseTestContext(user=report_user).get_jwt()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {report_token}"}
        response = self.client.get(self.IME_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_single_insurees_pending_enrollment_report_access_denied(self):
        # Test that a user without proper permissions gets access denied
        empty_role = create_test_role(perm_names=[], name="EmptyRole")
        unauthorized_user = create_test_interactive_user(
            username="testUnauthorizedUser", roles=[empty_role.id])
        unauthorized_token = BaseTestContext(user=unauthorized_user).get_jwt()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {unauthorized_token}"}
        response = self.client.get(self.IME_URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
