# from Acquisition import aq_inner
# from DateTime import DateTime
# from Products.CMFPlone.utils import safe_unicode
import argparse
import logging
import sys
from datetime import datetime

import transaction as zt
from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from zope.site.hooks import setSite

SCRIPTNAME = u'plone-scripts: wf-transition-trigger'

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


class ScriptWrapper():
    """
    """

    def __init__(self, portal):
        """
        """
        setSite(portal)
        self.portal = portal

    def run(self):
        self.wf_transition_on_effective_date()
        self.wf_transition_on_expires_date()

    def wf_transition_on_effective_date(self):
        query = {}

        # find only objects of the following portal_type:
        # query["portal_type"] = [
        #     "Folder",
        #     "Document",
        #     "News Item",
        #     "Event",
        #     "Image",
        #     "File",
        #     "FormFolder",
        # ]

        # find only objects in this path
        # query["context"] = self.portal.unrestrictedTraverse('docs')

        # restrict search depth, starting from "context" object (folder):
        # query["depth"] = 1

        # find only object which effective date is in the past:
        query["effectiveRange"] = datetime.now()

        # find only object which WF state is private:
        query["review_state"] = "private"

        transition_name = 'publish'
        transition_msg = u'Content published by reaching effective date.'
        self.trigger_wf_transition(transition_name, transition_msg, query)

    def wf_transition_on_expires_date(self):
        query = {}

        # find only objects of the following portal_type:
        # query["portal_type"] = [
        #     "Folder",
        #     "Document",
        #     "News Item",
        #     "Event",
        #     "Image",
        #     "File",
        #     "FormFolder",
        # ]

        # find only objects in this path
        # query["context"] = self.portal.unrestrictedTraverse('docs')

        # restrict search depth, starting from "context" object (folder):
        # query["depth"] = 1

        query["expires"] = {
            'query': datetime.now(),
            'range': 'max',
        }

        query["review_state"] = "published"
        transition_name = 'reject'
        transition_msg = u'Content rejected by reaching the expires date.'
        self.trigger_wf_transition(transition_name, transition_msg, query)

    def trigger_wf_transition(self, transition_name, transition_msg, query):
        # become admin:
        newSecurityManager(self.portal, self.portal.getOwner())
        results = api.content.find(**query)
        i = 0
        if not results:
            log.info("[{0}]: Nothing to do :)".format(transition_name))
            return

        for brain in results:
            try:
                obj = brain.getObject()
            except Exception, e:
                log.warning("Could not getObject from brain: {0}, {1}".format(
                    brain.getPath(),
                    e,
                ))
            else:
                # if not obj.getEffectiveDate():
                #     continue
                i += 1
                log.info("{0} content: {1}".format(
                    transition_name.capitalize(),
                    obj.absolute_url_path(),
                ))
                api.content.transition(
                   obj=obj,
                   transition=transition_name,
                   comment=transition_msg,
                )
                if not i % commit_batch_size:
                    log.debug("Commit after {0} objects!".format(
                        i,
                    ))
                    zt.commit()
        zt.commit()
        log.info("{0} {1} objects!".format(transition_name.capitalize(), i))


if __name__ == "__main__":
    script_wrapper = ScriptWrapper(
        app.unrestrictedTraverse(plonesite_path),  # noqa: F821

    )
    script_wrapper.run()
