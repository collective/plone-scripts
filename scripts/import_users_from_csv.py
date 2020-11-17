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
        with open(self.args.csv_file, "r") as f:
            users_reader = csv.DictReader(f, delimiter=";", quotechar='"')
            for user in users_reader:
                if api.user.get(username=user["email"]):
                    continue
                self.add_user(user["email"], user["email"], user["fullname"])
            transaction.commit()

    def add_user(self, username, email, fullname):
        user = api.user.create(email=email, properties={"fullname": fullname,},)
        self.notify_user(user, email, fullname)

    def notify_user(self, user, email, fullname):
        registry = getUtility(IRegistry)
        encoding = registry.get("plone.email_charset", "utf-8")
        registered_notify_template = getMultiAdapter(
            (self, self.request), name="registered_notify_template"
        )
        pwrt = getToolByName(self.portal, 'portal_password_reset')
        reset = pwrt.requestReset(email)
        reset_url = "{0}/passwordreset/{1}?userid={2}".format(
            self.portal.absolute_url(),
            reset['randomstring'],
            email,
        )
        subject = "Your user account at example.com"
        message = """Dear {fullname},

We created a user account for you.

your account login name is: {email}

Please activate your account here before: {expires}.
To activate follow this link and set your own password: {reset_url}

Your Website Admin
        """.format(
            email=email,
            fullname=fullname,
            reset_url=reset_url,
            expires=reset['expires'].strftime("%d.%m.%Y"),
        )
        try:
            mail_host = api.portal.get_tool(name="MailHost")
            api.portal.send_email(
                recipient=email, subject=subject, body=message, immediate=True,
            )
            log.info("Send email to: {0}".format(email))
        except Exception as e:
            log.debug(e)


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
