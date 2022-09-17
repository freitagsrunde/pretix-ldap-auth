#  Copyright 2022 Maximilian Haye
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
from typing import Dict, Optional, cast

import ldap3
from django import forms
from django.utils.translation import gettext_lazy as _
from ldap3.core.exceptions import LDAPException
from pretix.base.auth import BaseAuthBackend
from pretix.base.models import User
from pretix.settings import config

log = logging.getLogger(__name__)


class LdapAuthBackend(BaseAuthBackend):
    identifier = "ldap"
    verbose_name = "LDAP"

    def __init__(self):
        self._server = ldap3.Server(config.get("ldap", "url"))
        self._user_filter: str = config.get("ldap", "user_filter", fallback="(objectClass=*)")
        self._admin_filter: Optional[str] = config.get("ldap", "admin_filter", fallback=None)
        self._user_dn: str = config.get("ldap", "user_dn")

    @property
    def login_form_fields(self) -> dict:
        return {
            "uid": forms.CharField(label=_("Username"), required=True, widget=forms.TextInput({"autocomplete": "username"})),
            "password": forms.CharField(label=_("Password"), required=True, widget=forms.PasswordInput)
        }

    def form_authenticate(self, _, form_data: Dict[str, object]) -> Optional[User]:
        password = cast(str, form_data.pop("password"))
        user_dn = self._user_dn.format_map(form_data)
        user_filter = self._user_filter.format_map(form_data)
        admin_filter = self._admin_filter.format_map(form_data) if self._admin_filter else None

        connection = ldap3.Connection(self._server, user_dn, password, authentication=ldap3.SIMPLE, read_only=True, raise_exceptions=True)
        try:
            connection.bind()
        except LDAPException as e:
            log.info("Failed LDAP authentication: Bind failed: '%s'", user_dn, e)
            return None

        connection.search(user_dn, user_filter, search_scope=ldap3.BASE, attributes=ldap3.ALL_ATTRIBUTES)

        if not connection.entries:
            log.info("Failed LDAP authentication: Entry not found after bind: '%s'", user_dn)
            return None

        ldap_user = connection.entries[0]

        is_admin = False
        if admin_filter:
            connection.search(user_dn, admin_filter, search_scope=ldap3.BASE, attributes=ldap3.ALL_ATTRIBUTES)
            is_admin = len(connection.entries) > 0

        user_fields = {
            "fullname": ldap_user.cn.value,
            "is_staff": is_admin
        }

        user = User.objects.get_or_create_for_backend(
            self.identifier, user_dn, ldap_user.mail.value,
            user_fields, {}
        )

        log.info("Successfully authenticated user '%s'%s", user_dn, " as admin" if is_admin else "")

        return user
