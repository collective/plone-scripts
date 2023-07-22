import argparse
import logging
import sys

import transaction as zt
from AccessControl.SecurityManagement import newSecurityManager
from bs4 import BeautifulSoup
from plone import api
from plone.app.textfield.interfaces import IRichText
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import iterSchemata
from Products.CMFCore.interfaces import IContentish
from zope.schema import getFieldsInOrder
from zope.site.hooks import setSite


def get_base_parser():
    parser = argparse.ArgumentParser(description=SCRIPTNAME)
    parser.add_argument(
        "plonesite_path",
        default="/Plone",
        # metavar='"/Plone"',
        action="store",
        # dest="plonesite_path",
        type=str,
        nargs="?",
        help="Path to the Plone site",
    )
    parser.add_argument(
        "-b",
        "--commit_batch_size",
        type=int,
        action="store",
        dest="commit_batch_size",
        default=100,
        metavar="N",
        nargs="?",
        help="Do a transaction commit every N items. Default: 100",
    )
    parser.add_argument(
        "--hostname",
        action="store",
        dest="hostname",
        default="nohost",
        nargs="?",
        help="Define the hostname, Plone should use for creating urls. Default: nohost",  # NOQA: E501
    )
    parser.add_argument(
        "--protocol",
        action="store",
        dest="protocol",
        default="http",
        nargs="?",
        help="Define the protocol, Plone should use for creating urls. Default: http",  # NOQA: E501
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors. Useful for cronjobs.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show debug infos.",
    )
    return parser


def get_logger(name, args):
    log = logging.getLogger(name)
    if args.quiet:
        log.setLevel(logging.ERROR)
    elif args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%m/%d/%Y %H:%M:%S"
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


class BaseScriptWrapper:
    """ """

    def __init__(self, app, args):
        """ """
        plonesite_path = args.plonesite_path
        portal = app.unrestrictedTraverse(plonesite_path)  # noqa: F821
        setSite(portal)
        self.portal = portal
        self.request = self.portal.REQUEST
        self.request["PARENTS"] = [self.portal]
        self.commit_batch_size = args.commit_batch_size
        protocol = args.protocol
        hostname = args.hostname
        port = protocol == "http" and "80" or "443"

        self.request.setServerURL(
            protocol=protocol,
            hostname=hostname,
            port=port,
        )
        self.request.setVirtualRoot("")
        self.args = args


#################
## customization:
#################


SCRIPTNAME = u"plone-scripts: remove_folder_layout"


parser = get_base_parser()

# custom arguments:
parser.add_argument(
    '--layout',
    action="store",
    dest="layout",
    help="layout to be replaced/removed from all folders",  # NOQA: E501
)
parser.add_argument(
    '--layout-new',
    action="store",
    dest="layout_new",
    default="",
    help="New layout to replace existing layout from all folders",  # NOQA: E501
)

# remove -c script_name from args before argparse runs:
if "-c" in sys.argv:
    index = sys.argv.index("-c")
    del sys.argv[index]
    del sys.argv[index]

args = parser.parse_args()
log = get_logger(SCRIPTNAME, args)


class ScriptWrapper(BaseScriptWrapper):
    """ """

    def run(self):
        """run your code here"""
        newSecurityManager(self.portal, self.portal.getOwner())
        brains = api.content.find(object_provides=IContentish)
        for brain in brains:
            obj = brain.getObject()
            if hasattr(obj, "layout"):
                if obj.layout != args.layout:
                    continue
                if not args.layout_new:
                    del obj.layout
                    print("removed layout for: {}".format(obj.absolute_url_path()))
                else:
                    obj.layout = args.layout_new
                    print("replaced layout for: {}".format(obj.absolute_url_path()))

        zt.commit()


if __name__ == "__main__":
    script_wrapper = ScriptWrapper(
        app,
        args,
    )
    script_wrapper.run()
