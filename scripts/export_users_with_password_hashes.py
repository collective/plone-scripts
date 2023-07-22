import argparse
import csv
import logging
import os
import pdb
import sys
import transaction

from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter, getUtility
from zope.site.hooks import setSite
from Products.CMFCore.utils import getToolByName

# from Acquisition import aq_inner
# from Products.CMFPlone.utils import safe_unicode


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
        "--quiet", action="store_true", help="Only show errors. Useful for cronjobs.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show debug infos.",
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
    """
    """

    def __init__(self, app, args):
        """
        """
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
            protocol=protocol, hostname=hostname, port=port,
        )
        self.request.setVirtualRoot("")
        self.args = args


#################
## customization:
#################


SCRIPTNAME = u"plone-scripts: import_users_from_csv.py"


parser = get_base_parser()

parser.add_argument(
    "--csv",
    action="store",
    dest="csv_file",
    default="users.csv",
    nargs="?",
    help="Path to CSV file with users to import. Default: users.csv",
)

# remove -c script_name from args before argparse runs:
if "-c" in sys.argv:
    index = sys.argv.index("-c")
    del sys.argv[index]
    del sys.argv[index]

args = parser.parse_args()
log = get_logger(SCRIPTNAME, args)


class ScriptWrapper(BaseScriptWrapper):
    """
    """

    def run(self):
        """ run your code here """
        self.export_users()

    def export_users(self):
        from StringIO import StringIO
        import csv
        import time

        request = self.REQUEST
        text = StringIO()
        writer = csv.writer(text)

        # core properties (username/password)
        core_properties = ['member_id','password']

        # extra portal_memberdata properties
        extra_properties = ['fullname',
                            'email',
                            'location',
                            'home_page',
                            'description']

        properties = core_properties + extra_properties

        writer.writerow(properties)

        membership=self.portal_membership
        passwdlist=self.acl_users.source_users._user_passwords

        for memberId in membership.listMemberIds():
            row = []
            for property in properties:
                if property == 'member_id':
                    row.append(memberId)
                elif property == 'password':
                    row.append(passwdlist[memberId])
                else:
                    member = membership.getMemberById(memberId)
                    row.append(member.getProperty(property))
            writer.writerow(row)


        request.RESPONSE.setHeader('Content-Type','application/csv')
        request.RESPONSE.setHeader('Content-Length',len(text.getvalue()))
        request.RESPONSE.setHeader('Content-Disposition',
                                'inline;filename=members-%s.csv' %
                                time.strftime("%Y%m%d-%H%M%S",time.localtime()))

        return text.getvalue()


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def __next__(self):
        row = next(self.reader)
        return row

    next = __next__  # BBB for Python2

    def __iter__(self):
        return self


if __name__ == "__main__":
    script_wrapper = ScriptWrapper(app, args,)
    script_wrapper.run()
