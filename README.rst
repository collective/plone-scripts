Plone command line scripts
==========================

A collection of command line scripts for Plone. For a list of all scripts and examples look into the scripts folder.

Contribute
----------

You have a useful script you want to share?
We would like you to add this to the repository via a PR.


Workflow-Transaction-Trigger
----------------------------

This script triggers a workflow transaction for objects which fulfills a certain condition, like reaching a expiration date.

Features
--------

- optional Plone site path parameter
- optional commit_batch_size parameter to force commits after N items
- quiet and verbose options

See ``--help`` for all options.


Using the script
................

To run the script you can use either a ZEO client instance or a single Zope instance. But if you use a single Zope instance without ZEO, you have to stop the running instance before you can run the script.

Show command line help:

.. code-block:: bash

    ./bin/instance run ./scripts/wf-transaction-trigger.py -h


Run the script with custom Plone site path:

.. code-block:: bash

    ./bin/instance run ./scripts/wf-transaction-trigger.py "/Plone1"


Run the script with custom Plone site path, custom batch size and in quiet mode:

.. code-block:: bash

    ./bin/instance run ./scripts/wf-transaction-trigger.py "/Plone" -b 50 --quiet

**Note:** If you are running the script in quiet mode, you probably want also to disable deprecation warnings for this instance: see `deprecation-warnings <https://docs.plone.org/develop/styleguide/deprecation.html#enable-deprecation-warnings>`_.

Setting a custom hostname, useful if you are generating emails.

.. code-block:: bash

    ./bin/instance run ./scripts/wf-transaction-trigger.py "/Plone" --quiet --hostname example.com

Import Users from CSV
=====================

Import user from a CSV files and notify them via email.

.. code-block:: bash

    ./bin/instance run scripts/import_users_from_csv.py "/Plone" --csv=scripts/users.csv   --hostname="example.com"


Fix layout properties
=====================

You can replace/remove a layout property from all objects, as follow.

.. code-block:: bash

    ./bin/instance run scripts/fix_layout_property.py --layout=galleryview --layout-new=photo-gallery



