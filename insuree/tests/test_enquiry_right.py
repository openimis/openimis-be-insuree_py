"""
The enquiry and the insuree register are two different grants.

`insurees` is what the claim form's picker calls: `insuree.InsureeChfIdPicker` ->
`fetchInsuree` sends `chfId` together with `ignoreLocation: true`. Gating the resolver
on 101101 alone meant that letting a claim clerk pick an insuree also let them browse
the register and open the insuree page - there was no way to give one without the
other. 101105, the enquiry right, buys the identifier lookup and the nationwide scope
it needs, and nothing else:

  * with 101105 only, a CHFID or a uuid resolves anywhere in the country;
  * with 101105 only, a query carrying neither is refused - it would be a nationwide
    listing of the register, which is what 101101 is for;
  * `ignoreLocation` is honoured only for 101105. It used to be granted by the asking,
    so any holder of 101101 escaped their districts by setting a flag. Without the
    right the scope stays applied, silently: the lookup succeeds and resolves to
    nothing, which keeps the enquiry dialog and the picker working inside the
    districts a role is entitled to.

101105 was declared long ago, is seeded on the standard roles and was checked nowhere,
so it is the id this already meant - no new right to mint, catalogue and grant.
"""

import json

from core.rights_role_test_case import RightsRoleGraphQLTestCase
from core.test_helpers import create_right_only_user
from insuree.apps import InsureeConfig
from insuree.test_helpers import create_test_insuree
from location.test_helpers import create_basic_test_locations, create_test_village


LOOKUP_QUERY = """
query ($chfId: String!) {
  insurees(chfId: $chfId, ignoreLocation: true) {
    edges { node { uuid chfId } }
  }
}
"""

# What `fetchInsuree` actually sends: the picker projects the photo, the gender, the
# first point of service and the whole family, so the enquiry right has to carry the
# field resolvers too or the lookup resolves and then fails field by field.
PICKER_QUERY = """
query ($chfId: String!) {
  insurees(chfId: $chfId, ignoreLocation: true) {
    edges { node {
      uuid chfId lastName otherNames dob
      photo { folder filename photo }
      gender { code }
      currentVillage { id uuid code name type }
      family {
        id uuid poverty address
        location { id uuid code name type }
        headInsuree { id uuid chfId lastName }
        clientMutationId
      }
    } }
  }
}
"""

LIST_QUERY = """
query {
  insurees(first: 5) {
    edges { node { uuid chfId } }
  }
}
"""


class InsureeEnquiryQueryTestCase(RightsRoleGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        # Two villages, each under a district of its own: the caller is entitled to
        # the first one, the insuree lives in the second.
        cls.home_village = create_test_village({"code": "NATHOME"})
        cls.away_village = create_test_village({"code": "NATAWAY"})
        cls.away_insuree = create_test_insuree(
            with_family=True,
            is_head=True,
            custom_props={"current_village": cls.away_village},
            family_custom_props={"location": cls.away_village},
        )
        cls.home_districts = [cls.home_village.parent.parent.code]

    def _user(self, name, perms):
        return create_right_only_user(name, perms, district_codes=self.home_districts)

    def _chf_ids(self, response):
        content = json.loads(response.content)
        edges = content["data"]["insurees"]["edges"]
        return [edge["node"]["chfId"] for edge in edges]

    def test_the_enquiry_right_has_its_own_id(self):
        self.assertEqual(
            InsureeConfig.gql_query_insuree_inquire_perms, ["101105"]
        )

    def test_enquiry_right_alone_resolves_a_chfid_anywhere(self):
        user = self._user("enq_ins_pick", ["gql_query_insuree_inquire_perms"])
        self.assert_user_lacks_named_perms(user, ["gql_query_insurees_perms"])
        response = self.assert_gql_ok(
            user, LOOKUP_QUERY, variables={"chfId": self.away_insuree.chf_id}
        )
        self.assertEqual(self._chf_ids(response), [self.away_insuree.chf_id])

    def test_enquiry_right_alone_does_not_open_the_register(self):
        user = self._user("enq_ins_list", ["gql_query_insuree_inquire_perms"])
        self.assert_gql_unauthorized(user, LIST_QUERY)

    def test_no_insuree_right_at_all_is_refused(self):
        user = self._user("enq_ins_none", [])
        self.assert_gql_unauthorized(
            user, LOOKUP_QUERY, variables={"chfId": self.away_insuree.chf_id}
        )

    def test_register_reader_still_lists_and_still_gets_its_districts(self):
        user = self._user("enq_ins_reader", ["gql_query_insurees_perms"])
        self.assert_gql_ok(user, LIST_QUERY)

    def test_ignore_location_without_the_enquiry_right_stays_scoped(self):
        """No error - the flag is simply not honoured, so the lookup finds nothing."""
        user = self._user("enq_ins_scoped", ["gql_query_insurees_perms"])
        response = self.assert_gql_ok(
            user, LOOKUP_QUERY, variables={"chfId": self.away_insuree.chf_id}
        )
        self.assertEqual(self._chf_ids(response), [])

    def test_enquiry_right_alone_serves_the_picker_projection(self):
        """The query the claim form really sends, with no register right at all."""
        user = self._user("enq_ins_proj", ["gql_query_insuree_inquire_perms"])
        self.assert_user_lacks_named_perms(
            user, ["gql_query_insurees_perms", "gql_query_families_perms"]
        )
        response = self.assert_gql_ok(
            user, PICKER_QUERY, variables={"chfId": self.away_insuree.chf_id}
        )
        self.assertEqual(self._chf_ids(response), [self.away_insuree.chf_id])

    def test_enquiry_right_alone_does_not_open_the_family_register(self):
        """The Families page is guarded by 101001, and stays that way."""
        user = self._user("enq_ins_fam", ["gql_query_insuree_inquire_perms"])
        self.assert_gql_unauthorized(
            user,
            "query { families(first: 5) { edges { node { uuid } } } }",
        )

    def test_both_rights_together_resolve_out_of_district(self):
        user = self._user(
            "enq_ins_both",
            ["gql_query_insurees_perms", "gql_query_insuree_inquire_perms"],
        )
        response = self.assert_gql_ok(
            user, LOOKUP_QUERY, variables={"chfId": self.away_insuree.chf_id}
        )
        self.assertEqual(self._chf_ids(response), [self.away_insuree.chf_id])
