# encoding: utf-8
"""Unit tests for ckan/logic/auth/delete.py.

"""

import pytest

import ckan.logic.auth.delete as auth_delete
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from ckan import model

logic = helpers.logic


@pytest.mark.usefixtures("clean_db", "with_request_context")
class TestDeleteAuth:
    def test_anon_cant_delete(self):
        context = {"user": None, "model": model}
        params = {}
        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth("resource_delete", context=context, **params)

    def test_no_org_user_cant_delete(self):
        user = factories.User()
        org = factories.Organization()
        dataset = factories.Dataset(
            owner_org=org["id"], resources=[factories.Resource()]
        )

        response = auth_delete.resource_delete(
            {"user": user["name"], "model": model},
            {"id": dataset["resources"][0]["id"]},
        )

        assert not response["success"]

    def test_org_user_can_delete(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "editor"}]
        org = factories.Organization(users=org_users)
        dataset = factories.Dataset(
            owner_org=org["id"], resources=[factories.Resource()], user=user
        )

        response = auth_delete.resource_delete(
            {"user": user["name"], "model": model, "auth_user_obj": user},
            {"id": dataset["resources"][0]["id"]},
        )

        assert response["success"]

    @pytest.mark.ckan_config("ckan.plugins", "image_view")
    @pytest.mark.usefixtures("with_plugins")
    def test_anon_cant_delete_2(self):
        context = {"user": None, "model": model}
        params = {}
        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                "resource_view_delete", context=context, **params
            )

    @pytest.mark.ckan_config("ckan.plugins", "image_view")
    @pytest.mark.usefixtures("with_plugins")
    def test_no_org_user_cant_delete_2(self):
        user = factories.User()
        org = factories.Organization()
        dataset = factories.Dataset(
            owner_org=org["id"], resources=[factories.Resource()]
        )

        resource_view = factories.ResourceView(
            resource_id=dataset["resources"][0]["id"]
        )

        context = {"user": user["name"], "model": model}

        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                "resource_view_delete", context=context, id=resource_view["id"]
            )

    @pytest.mark.ckan_config("ckan.plugins", "image_view")
    @pytest.mark.usefixtures("with_plugins")
    def test_org_user_can_delete_2(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "editor"}]
        org = factories.Organization(users=org_users)
        dataset = factories.Dataset(
            owner_org=org["id"], resources=[factories.Resource()], user=user
        )

        resource_view = factories.ResourceView(
            resource_id=dataset["resources"][0]["id"]
        )

        context = {"user": user["name"], "model": model}

        response = helpers.call_auth(
            "resource_view_delete", context=context, id=resource_view["id"]
        )

        assert response


def test_anon_cant_clear():
    context = {"user": None, "model": model}
    params = {}
    with pytest.raises(logic.NotAuthorized):
        helpers.call_auth("resource_view_clear", context=context, **params)


@pytest.mark.usefixtures("with_request_context")
def test_normal_user_cant_clear():
    user = factories.User()

    context = {"user": user["name"], "model": model}

    with pytest.raises(logic.NotAuthorized):
        helpers.call_auth("resource_view_clear", context=context)


@pytest.mark.usefixtures("with_request_context")
def test_sysadmin_user_can_clear():
    user = factories.User(sysadmin=True)

    context = {"user": user["name"], "model": model}
    response = helpers.call_auth("resource_view_clear", context=context)

    assert response


@pytest.mark.usefixtures("clean_db")
@pytest.mark.ckan_config(u"ckan.auth.allow_dataset_collaborators", True)
class TestPackageMemberDeleteAuth(object):

    def _get_context(self, user):

        return {
            'model': model,
            'user': user if isinstance(user, basestring) else user.get('name')
        }

    def setup(self):

        self.org_admin = factories.User()
        self.org_editor = factories.User()
        self.org_member = factories.User()

        self.normal_user = factories.User()

        self.org = factories.Organization(
            users=[
                {'name': self.org_admin['name'], 'capacity': 'admin'},
                {'name': self.org_editor['name'], 'capacity': 'editor'},
                {'name': self.org_member['name'], 'capacity': 'member'},
            ]
        )

        self.dataset = factories.Dataset(owner_org=self.org['id'])

    def test_delete_org_admin_is_authorized(self):

        context = self._get_context(self.org_admin)
        assert helpers.call_auth(
            'package_member_delete',
            context=context, id=self.dataset['id'])

    def test_delete_org_editor_is_not_authorized(self):

        context = self._get_context(self.org_editor)
        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                'package_member_delete',
                context=context, id=self.dataset['id'])

    def test_delete_org_member_is_not_authorized(self):

        context = self._get_context(self.org_member)
        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                'package_member_delete',
                context=context, id=self.dataset['id'])

    def test_delete_org_admin_from_other_org_is_not_authorized(self):
        org_admin2 = factories.User()
        factories.Organization(
            users=[
                {'name': org_admin2['name'], 'capacity': 'admin'},
            ]
        )

        context = self._get_context(org_admin2)
        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                'package_member_delete',
                context=context, id=self.dataset['id'])

    def test_delete_missing_org_is_not_authorized(self):

        dataset = factories.Dataset(owner_org=None)

        context = self._get_context(self.org_admin)
        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                'package_member_delete',
                context=context, id=dataset['id'])

    def test_list_org_admin_is_authorized(self):

        context = self._get_context(self.org_admin)
        assert helpers.call_auth(
            'package_member_list',
            context=context, id=self.dataset['id'])

    def test_list_org_editor_is_not_authorized(self):

        context = self._get_context(self.org_editor)
        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                'package_member_list',
                context=context, id=self.dataset['id'])
