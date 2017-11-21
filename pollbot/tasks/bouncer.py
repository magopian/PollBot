import os.path


from pyquery import PyQuery as pq
from pollbot.exceptions import TaskError
from pollbot.utils import (build_version_id, Channel, get_version_channel,
                           get_version_from_filename)
from . import get_session, heartbeat_factory, build_task_response


async def bouncer(product, version):
    """Fetch bedrock download page to grab the bouncer download link and then make sure
    it redirects to the expected version."""
    channel = get_version_channel(version)
    if channel is Channel.ESR:
        url = "https://www.mozilla.org/en-US/{}/organizations/all/".format(product)
    elif channel is Channel.RELEASE:
        url = 'https://www.mozilla.org/en-US/{}/all/'.format(product)
    else:
        url = 'https://www.mozilla.org/fr/{}/channel/desktop/'.format(product)

    with get_session() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                msg = 'Download page not available  ({})'.format(resp.status)
                raise TaskError(msg)
            body = await resp.text()
            d = pq(body)

            if channel is Channel.NIGHTLY:
                link_path = "#desktop-nightly-download > .download-list > .os_linux64 > a"
                url = d(link_path).attr('href')
            elif channel is Channel.BETA:
                link_path = "#desktop-beta-download > .download-list > .os_linux64 > a"
                url = d(link_path).attr('href')
            else:  # channel in (Channel.RELEASE, Channel.ESR):
                link_path = "#fr > .linux64 > a"
                url = d(link_path).attr('href')

            async with session.get(url, allow_redirects=False) as resp:
                url = resp.headers['Location']
                filename = os.path.basename(url)
                last_release = get_version_from_filename(filename)

            status = build_version_id(last_release) >= build_version_id(version)
            message = "Bouncer for {} redirects to version {}".format(channel.value, last_release)
            return build_task_response(status, url, message)


heartbeat = heartbeat_factory('https://download.mozilla.org/')
