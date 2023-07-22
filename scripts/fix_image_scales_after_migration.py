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


SCRIPTNAME = u"plone-scripts: fix_image_scales_after_migration"


parser = get_base_parser()

## custom arguments:
# parser.add_argument(
#     '--someflag',
#     action='store_true',
#     help='Some flag to control things.',
# )

# remove -c script_name from args before argparse runs:
if "-c" in sys.argv:
    index = sys.argv.index("-c")
    del sys.argv[index]
    del sys.argv[index]

args = parser.parse_args()
log = get_logger(SCRIPTNAME, args)

# copied from: https://github.com/collective/collective.migrationhelpers/blob/master/src/collective/migrationhelpers/images.py
# Old scale name to new scale name
IMAGE_SCALE_MAP = {
    "icon": "icon",
    "large": "large",
    "listing": "listing",
    "mini": "mini",
    "preview": "preview",
    "thumb": "thumb",
    "tile": "tile",
    # BBB
    "article": "preview",
    "artikel": "preview",
    "carousel": "preview",
    "company_index": "thumb",
    "content": "preview",
    "leadimage": "tile",
    "portlet-fullpage": "large",
    "portlet-halfpage": "large",
    "portlet-links": "thumb",
    "portlet": "thumb",
    "staff_crop": "thumb",
    "staff_index": "thumb",
}


def image_scale_fixer(text, obj):
    if not text:
        return
    soup = BeautifulSoup(text, "html.parser")
    for img in soup.find_all("img"):
        src = img["src"]
        if src.startswith("http"):
            log.info(
                "Skip external image {} used in {}".format(src, obj.absolute_url())
            )
            continue

        for old, new in IMAGE_SCALE_MAP.items():
            # replace plone.app.imaging old scale names with new ones
            src = src.replace(
                u"@@images/image/{}".format(old), u"@@images/image/{}".format(new)
            )
            # replace AT traversing scales
            src = src.replace(
                u"/image_{}".format(old), u"/@@images/image/{}".format(new)
            )

        if "/@@images/" in src:
            scale = src.split("/@@images/image/")[-1]
            if "/" in scale:
                log.info(
                    u"Invalid image-link in {}: {}".format(obj.absolute_url(), src)
                )
            img["data-scale"] = scale
        else:
            # image not scaled
            img["data-scale"] = ""

        img["src"] = src
        img["data-linktype"] = "image"
        img["class"] = img.get("class", []) + ["image-richtext"]

        if "resolveuid" in src:
            uuid = src.split("resolveuid/")[1].split("/")[0]
            img["data-val"] = uuid
        else:
            log.info(
                u"Image-link without resolveuid in {}: {}".format(
                    obj.absolute_url(), src
                )
            )

    return soup.decode()


def fix_at_image_scales(context=None):
    """Run this in Plone 5.x"""
    catalog = api.portal.get_tool("portal_catalog")
    query = {}
    if hasattr(catalog, "getAllBrains"):
        results = catalog.getAllBrains()
    else:
        results = catalog.unrestrictedSearchResults(**query)
    log.info("Starting migration of image scales in rich text fields.")
    for result in results:
        try:
            obj = result.getObject()
        except (KeyError, AttributeError):
            log.warning(
                "Not possible to fetch object from catalog result for "
                "item: {0}.".format(result.getPath())
            )
            continue
        changed = False
        for schema in iterSchemata(obj):
            fields = getFieldsInOrder(schema)
            for name, field in fields:
                if not IRichText.providedBy(field):
                    continue
                text = getattr(obj.aq_base, name, None)
                if not text:
                    continue
                clean_text = image_scale_fixer(text.raw, obj)
                if clean_text == text.raw:
                    continue
                setattr(
                    obj,
                    name,
                    RichTextValue(
                        raw=clean_text,
                        mimeType=text.mimeType,
                        outputMimeType=text.outputMimeType,
                        encoding=text.encoding,
                    ),
                )
                changed = True
                log.info(
                    "Text cleanup in field {0} for {1}".format(
                        name, "/".join(obj.getPhysicalPath())
                    )
                )
        if changed:
            obj.reindexObject(idxs=("SearchableText",))
            log.info("Text cleanup for {0}".format("/".join(obj.getPhysicalPath())))


class ScriptWrapper(BaseScriptWrapper):
    """ """

    def run(self):
        """run your code here"""
        newSecurityManager(self.portal, self.portal.getOwner())
        brains = api.content.find(object_provides=IContentish)
        for brain in brains:
            obj = brain.getObject()
            if obj.language == "de-de":
                obj.language = "de"
                print("fix language for: {}".format(obj.absolute_url_path()))
        fix_at_image_scales()
        zt.commit()


if __name__ == "__main__":
    script_wrapper = ScriptWrapper(
        app,
        args,
    )
    script_wrapper.run()
