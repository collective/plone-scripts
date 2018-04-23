Plone command line scripts
==========================

A collection of command line scripts for Plone.


Workflow-Transaction-Trigger
----------------------------

This script triggers a workflow transaction for objects which fulfils a certain condition, like reaching a expiration date.

Features
--------

- optional Plone site path paramter
- optional commit_batch_size parameter to force commits after N items
- quiet and verbose options

See ``--help`` for all options.


Using the script
................

Show commandline help:

.. code-block:: bash

    ./bin/instance_reserved run ./scripts/wf-transaction-trigger.py -h


Run the script with custom Plone site path:

.. code-block:: bash

    ./bin/instance_reserved run ./scripts/wf-transaction-trigger.py "/Plone1"


Run the script with custom Plone site path, custom batch size and in quiet mode:

.. code-block:: bash

    ./bin/instance_reserved run ./scripts/wf-transaction-trigger.py "/Plone" -b 50 --quiet

**Note:** If you are running the script in quiet mode, you probably want also to disable deprecation warnings for this instance: see `deprecation-warnings <https://docs.plone.org/develop/styleguide/deprecation.html#enable-deprecation-warnings>`_.
