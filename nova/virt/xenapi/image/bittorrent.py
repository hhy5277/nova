# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging
import six.moves.urllib.parse as urlparse

import nova.conf
from nova.i18n import _, _LW
from nova.virt.xenapi import vm_utils

LOG = logging.getLogger(__name__)


CONF = nova.conf.CONF


class BittorrentStore(object):
    @staticmethod
    def _lookup_torrent_url_fn():
        """Load a "fetcher" func to get the right torrent URL.
        """

        if CONF.xenserver.torrent_base_url:
            if '/' not in CONF.xenserver.torrent_base_url:
                LOG.warning(_LW('Value specified in conf file for'
                             ' xenserver.torrent_base_url does not contain a'
                             ' slash character, therefore it will not be used'
                             ' as part of the torrent URL. Specify a valid'
                             ' base URL as defined by RFC 1808 (see step 6).'))

            def _default_torrent_url_fn(image_id):
                return urlparse.urljoin(CONF.xenserver.torrent_base_url,
                                        "%s.torrent" % image_id)

            return _default_torrent_url_fn

        raise RuntimeError(_('Cannot create default bittorrent URL'
                             ' without xenserver.torrent_base_url'
                             ' configuration option set.'))

    def download_image(self, context, session, instance, image_id):
        params = {}
        params['image_id'] = image_id
        params['uuid_stack'] = vm_utils._make_uuid_stack()
        params['sr_path'] = vm_utils.get_sr_path(session)
        params['torrent_seed_duration'] = CONF.xenserver.torrent_seed_duration
        params['torrent_seed_chance'] = CONF.xenserver.torrent_seed_chance
        params['torrent_max_last_accessed'] = \
                CONF.xenserver.torrent_max_last_accessed
        params['torrent_listen_port_start'] = \
                CONF.xenserver.torrent_listen_port_start
        params['torrent_listen_port_end'] = \
                CONF.xenserver.torrent_listen_port_end
        params['torrent_download_stall_cutoff'] = \
                CONF.xenserver.torrent_download_stall_cutoff
        params['torrent_max_seeder_processes_per_host'] = \
                CONF.xenserver.torrent_max_seeder_processes_per_host

        lookup_fn = self._lookup_torrent_url_fn()
        params['torrent_url'] = lookup_fn(image_id)

        vdis = session.call_plugin_serialized(
                'bittorrent', 'download_vhd', **params)

        return vdis

    def upload_image(self, context, session, instance, image_id, vdi_uuids):
        raise NotImplementedError
