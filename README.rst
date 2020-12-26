remarkdav
=========
This is a small tool to sync webdav files (only PDF) to the reMarkable cloud (oneway).

Setup (dev)
-----------

1. Clone from Git

.. code-block::

    git clone git@github.com:hansegucker/remarkdav.git

2. Get poetry

See instructions at https://python-poetry.org/docs/#installation


3. Install dependencies

.. code-block::

    $ cd remarkdav/ # Go to your cloned directory
    $ poetry install

3. Run

.. code-block::

    $ poetry run remarkdav

Setup (production)
------------------

1. Get it via poetry (use pip with Python 3)

.. code-block::

    $ sudo pip install -G remarkdav

2. Run

.. code-block::

    $ remarkdav

Configuration
-------------
Copy the example configuration file from ``settings-example.toml`` to ``/etc/remarkdav/settings.toml`` and customise it.


Copyright
---------
© 2020 by Jonathan Weth <dev@jonathanweth.de>

remarkdav is licenced under GPL-3.0.