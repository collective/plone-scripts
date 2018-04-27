# from Acquisition import aq_inner
# from DateTime import DateTime
# from Products.CMFPlone.utils import safe_unicode
import argparse
import logging
import sys

# from plone import api
from zope.site.hooks import setSite

SCRIPTNAME = u'plone-scripts: example'

parser = argparse.ArgumentParser(description=SCRIPTNAME)
parser.add_argument(
    'plonesite_path',
    default='/Plone',
    # metavar='"/Plone"',
    action="store",
    # dest="plonesite_path",
    type=str,
    nargs='?',
    help='Path to the Plone site',
)
parser.add_argument(
    '-b',
    '--commit_batch_size',
    type=int,
    action="store",
    dest="commit_batch_size",
    default=100,
    metavar="N",
    nargs='?',
    help='Do a transaction commit every N items. Default: 100',
)
parser.add_argument(
    '--hostname',
    action="store",
    dest="hostname",
    default="nohost",
    nargs='?',
    help='Define the hostname, Plone should use for creating urls. Default: nohost',  # NOQA: E501
)
parser.add_argument(
    '--protocol',
    action="store",
    dest="protocol",
    default="http",
    nargs='?',
    help='Define the protocol, Plone should use for creating urls. Default: http',  # NOQA: E501
)
parser.add_argument(
    '--quiet',
    action='store_true',
    help='Only show errors. Useful for cronjobs.',
)
parser.add_argument(
    '--verbose',
    action='store_true',
    help='Show debug infos.',
)


# remove -c script_name from args before argparse runs:
if '-c' in sys.argv:
    index = sys.argv.index('-c')
    del sys.argv[index]
    del sys.argv[index]


args = parser.parse_args()


log = logging.getLogger(SCRIPTNAME)
if args.quiet:
    log.setLevel(logging.ERROR)
elif args.verbose:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)


handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt='%m/%d/%Y %H:%M:%S')
handler.setFormatter(formatter)
log.addHandler(handler)


# script configuration:
plonesite_path = args.plonesite_path
commit_batch_size = args.commit_batch_size
protocol = args.protocol
hostname = args.hostname
port = protocol == 'http' and '80' or '443'


class ScriptWrapper():
    """
    """

    def __init__(self, portal):
        """
        """
        setSite(portal)
        self.portal = portal
        request = self.portal.REQUEST
        request['PARENTS'] = [self.portal]
        request.setServerURL(
            protocol=protocol,
            hostname=hostname,
            port=port,
        )
        request.setVirtualRoot('')

    def run(self):
        """ run your code here """
        print(self.portal.news.absolute_url())


if __name__ == "__main__":
    script_wrapper = ScriptWrapper(
        app.unrestrictedTraverse(plonesite_path),  # noqa: F821

    )
    script_wrapper.run()
