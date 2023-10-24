*******
Testing
*******

.. note::

   Unittests give software a base line of how it performs under as many
   situations as the author can think of. There are two objectives one
   must keep in mind while writing tests. First is coverage where you want
   to cover as many lines of code as is feasibly possible. However,
   getting 100% coverage does not mean you're done writing tests. The
   second thing you need to write tests for are business rules. Business
   rules are the specific constraints you have decided your software needs
   to follow.

First off I'm assuming you have forked this API and want to either
contribute to or derive your own code from it. In either case you will
be building a virtual environment to do your work in.

Creating a Virtual Environment
==============================

From your user account we first need to install a few packages. The below
install assumes a Debian derived OS. I don't generally use Red Hat derived
OSs, but I am sure they have some equivalent packages.

.. code-block:: console

   $ sudo apt install build-essential python3-dev git

First we need to install the *pip* utility which can be used to install
the packages for *python3.11*. Then we install the *virtualenvwrapper*
package. This is a wrapper around *virtualenv* that provides easy to use
tools for *virtualenv*. It also installs *virtualenv* for you.

You can get the full instruction if you visit
`pypa <https://github.com/pypa/get-pip>`_. But, in general this is what you do
to install `pip` system wide.

.. code-block:: console

    $ curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ sudo -H python3.11 get-pip.py

You may get warnings about installing it in the system and not in a
*virtualenv*, but we want it in the system at this point.

Now we install the *virtualenvwrapper* package.

.. code-block:: console

    $ sudo -H pip3 install virtualenvwrapper

Configure *.bashrc* to auto load the *virtualenvwrapper* package. Use your
favorite editor, I'm using *nano* here.

.. code-block:: console

    $ nano .bashrc

Then add the following lines to the bottom of the *.bashrc* file.

.. code-block:: bash

    # Setup the Python virtual environment.
    VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.11
    source /usr/local/bin/virtualenvwrapper.sh

You may need to resource the *.bashrc* file.

.. code-block:: console

    $ source .bashrc

Download *noncom-bookkeeper*. First **cd** into the path where you want
to put the package. If you forked the package then change the path
accordingly.

.. code-block:: console

    $ git clone git@github.com:cnobile2012/noncom-bookkeeper.git

Create a VE for *noncom-bookkeeper*.

.. code-block:: console

    $ cd /path/to/noncom-bookkeeper
    $ mkvirtualenv -p python3.11 nc-bookkeeper

Next we install the packages required for developing *noncom-bookkeeper*.

.. code-block:: console

   $ pip install -r requirements/development.txt

After the initial creation of the VE you can use these commands to activate
and deactivate a VE.

.. code-block:: console

    $ workon bookkeeper
    $ deactivate

Running Tests
=============

The *Makefile* in the project's root should be used to run the tests as
it will automatically clean up old coverage reports and HTML documents.

After tests are done running they will dump to the screen a basic coverage
report. You can also point your browser to a more complete HTML report in
*docs/htmlcov/index.html*.

There will be log files in the *logs* directory that are created
during the tests one for each test class. They may have minimal use if all
the tests pass, but will be invaluable if any fail.

.. code-block:: console

    $ make tests
    $ make tests TEST_PATH=tests.test_config.TestTomlMetaData
    $ make tests TEST_PATH=tests/test_config.py:TestTomlMetaData
    $ make tests TEST_PATH=tests/test_config.py:TestTomlMetaData.test_panels_property

* The 1st example will run all tests.
* The 2nd example will run tests for a specific class in the *test_config.py*
  module.
* The 3rd example give the same result as the 2nd. Be sure to notice the :
  (colon) just before the class name.
* The 4th example will run a specific test in the TestClassMethods. This also
  needs a : just before the class name.
