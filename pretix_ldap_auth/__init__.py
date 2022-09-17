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

from django.utils.translation import gettext_lazy as _

from ._version import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class LdapApp(PluginConfig):
    name = "pretix_ldap_auth"
    verbose_name = "LDAP Authentication"

    class PretixPluginMeta:
        name = _("LDAP Authentication")
        author = "Maximilian Haye"
        description = _("Authenticates users against an LDAP server")
        version = __version__
        visible = False
        category = "INTEGRATION"
        compatibility = "pretix ~= 4.12"


default_app_config = "pretix_ldap_auth.LdapApp"
