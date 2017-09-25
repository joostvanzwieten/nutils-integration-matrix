nutils-integration-matrix
=========================

This python module enables [Nutils] to send a notification to a [Matrix] room
when a run has finished:

> [example.py] finished in 0:05:24

Setup
-----

Run

    pip3 install --user nutils_integration_matrix

Login to an existing account (change user id `@botusername:bothomeserver`
accordingly, this is preferably different from your personal account):

    python3 -m nutils_integration_matrix login @botusername:bothomeserver

or create a passwordless account (this requires a shared key, ask the
administrator of your homeserver):

    python3 -m nutils_integration_matrix register @botusername:bothomeserver

Create a room to push messages to:

    python3 -m nutils_integration_matrix create-room

and invite yourself (change `@yourusername:yourhomeserver` accordingly):

    python3 -m nutils_integration_matrix invite @yourusername:yourhomeserver

Finally, add the following line to your Nutils configuration file
(`~/.config/nutils/config`):

    send_status_integrations=['matrix']

If you want clickable links also add (change `https://domain/~username/`
accordingly):

    log_url_prefix='https://domain/~username/'

You can verify above steps by running

    python3 -m nutils_integration_matrix status

[Nutils]: http://nutils.org/
[Matrix]: https://matrix.org/
[example.py]: http://nutils.org/
