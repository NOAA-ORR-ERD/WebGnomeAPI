###########
WebGnomeAPI
###########

A web service that interfaces with py_gnome

Installing / Running
====================

webgnomeapi is a python package. To run it you need to install the dependencies, install the package, then run it:

Dependencies
------------

The webgnomeAPI is pretty worthless without py_gnome, and py_gnome is easiest to get going with conda and conda-forge.

conda
.....

If you are using a conda based system you can install all of the dependencies with conda. This requires the conda-forge channel)::

    conda config --add channels conda-forge

(You probably already did that for py_gnome)

Install the requirements::

  conda install --file conda_requirements.txt


pip
...

In theory, you can install everything webgnomeapi needs with pip, except py_gnome and its dependencies. You can give that a try with::

    pip install -r conda_requirements.txt


To run the API, you also need a redis server. If you have one installed from a another source, that will work fine. If not, then you can use conda to get it::

  conda install redis-server

(or uncomment that line in the conda_requirements.txt file)


Installing the server
---------------------

Installing the server from code can be done the usual way for a python package::

  pip install -e ./

or::

  python setup.py develop


Testing the Server
------------------

In order to run webgnomeapi, you need a redis server running first. redis can be installed with conda on the Mac, or, on Linux, with the system package manager.

Windows: Installing redis on Windows can be a bit of a challenge. We have had success with these binaries:

https://github.com/tporadowski/redis/releases


Once installed, you should be able to run a redis server with::

  redis-server

Once redis is running, you should be able to run the tests with::

  pytest webgnome_api/tests

Windows: Installing redis on Windows can be a bit of a challenge. We have had success with these binaries:

https://github.com/tporadowski/redis/releases

Though they are no longer being maintained.


Running the Server
------------------

First start up a Redis server with::

  redis-server

webgnomeapi is a Pyramid application that can be run with the paste uwsgi server::

  pserve config-example.ini


Deployment Issues
=================

websockets
----------

Even after configuring apache’s mod_proxy websocket tunnel as others online have reported working, I was unable to make a websocket connection.

Server logs reported something that seemed like the gevent server was assuming a socket was created and initialized before it actually was, as though upgrade requests were not getting through.
More investigation is needed.

This issue coupled with the requirement of https means that the python server itself needs to handle the ssl encryption and be given direct access to the web through a port of ip of it's own.

Socket.IO
---------

Due to the fact that we're using version 0.9 of the socket.io package running the application under a directory (such as gnome.orr.noaa.gov/gnomeapi) does not work.
It will assume gnome.orr.noaa.gov/socket.io still and there is no way to adjust this without modifying the library.

In addition if the client is running on a port for some reason, localhost:8080 for example. It will project this port on to its destination server,
``https://gnome.orr.noaa.gov/gnomeapi`` will become ``https://gnome.orr.noaa.gov:8080/socket.io/``.
The current solution to this last bit is to always provide a port to the client's configuration even if it's redundant ... ``https://gnome.orr.noaa.gov:443/gnomeapi``


Until we upgrade gevent we're stuck with 0.9 and this issue.


Development Notes
=================

libgoods
--------

The webgnomeapi depends on the libgoods pacakge, which is under active development at the same time.

So you need to clone and install the libgoods package, and keep it up to date with the same branch.


Ignore submodules for now!
--------------------------

If we do ever use a submodule, here's some info on that:


To make this a bit easier, we've added libgoods as a git "submodule".

(https://git-scm.com/book/en/v2/Git-Tools-Submodules)

However, you still need to keep the libgood submodule up to date as you work.

Initial Clone
.............

When you first clone the webgnomeapi repo, you get a dir for the libgood submodule, but not the actual code.

NOTE: As with all things git -- there are multipel ways to ackomlish all this, but I think this is the most straightforward.

To get the actual code, you must run two commands: ``git submodule init`` to initialize your local configuration file, and ``git submodule update`` to fetch all the data from that project and check out the appropriate commit listed in your superproject.

::

  $ git submodule init
  Submodule 'libgoods' (https://gitlab.orr.noaa.gov/gnome/libgoods) registered for path 'libgoods'

  $ git submodule update
  Cloning into '/Users/chris.barker/Junk/webgnomeapi/libgoods'...
  warning: redirecting to https://gitlab.orr.noaa.gov/gnome/libgoods.git/
  Submodule path 'libgoods': checked out 'a11d8cb43a9ac6836855f2f1455c94b21d5d707b'

You now should have the ``libgoods`` repo:

::

  $ ls libgoods/
  CHANGES.txt            conda_requirements.txt setup.py
  LICENSE.txt            libgoods
  README.rst             setup.cfg

You can go into that repo, and install the package in editable (develop) mode:

::

    $ pip install -e ./
    Obtaining file:///Users/chris.barker/Junk/webgnomeapi/libgoods
      Preparing metadata (setup.py) ... done
    Installing collected packages: libgoods
      Attempting uninstall: libgoods
        Found existing installation: libgoods 0.0.1
        Uninstalling libgoods-0.0.1:
          Successfully uninstalled libgoods-0.0.1
      Running setup.py develop for libgoods
    Successfully installed libgoods-0.0.1

And away we go!

Updating the submodule
......................

This is key -- as libgoods is under active development, we will need to keep updating it. Whenever you think (or know) that libgoods has changed, you will want to update the submodule with:

::

  git submodule update --remote

  warning: redirecting to https://gitlab.orr.noaa.gov/gnome/libgoods.git/
  From https://gitlab.orr.noaa.gov/gnome/libgoods
   * [new branch]      develop    -> origin/develop

NOTE: we should have this repo configured so that you get the right branch of the libgoods submodule, but we'll need to make sure. e.g. if the webgnomeapi repo is on the develop branch, it should pull the develop branch from libgoods as well.

NOTE2: It seems, at least by dewfault, that the submodule is checkout in in "detached HEAD" mode. So you do not want to make changes to libgoods directly in that module, but rather, make any changes in the libgoods repo itself, push them, and then run ``git submodule update --remote``.






