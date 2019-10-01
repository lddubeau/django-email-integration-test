This Django package provides a comment designed to perform **integration tests**
for your email setup *after deployment.*

**THIS IS NOT A REPLACEMENT FOR UNIT TESTING YOUR CODE.**

Presumably you already do unit testing of the code that generates emails and use
the appropriate setup to avoid actually sending emails to anyone. Perhaps you
run automated tests in development that do actually contact a server and send
emails but the parameters of the test are most likely significantly different
from the production context. Even if your run your tests in a Docker container
that mimics your production environment, at the very least, the IP of your test
server will be different from the IP used in production.

Ultimately none of the above tests are enough to *absolutely* guarantee that
once your app runs in production with the production settings your emails are
going to get through without problem. It really depends on how the mail relays
between your server and the final destination are setup. It is really easy to
*think* your email setup works when in fact it does not. Typically, mail sent to
``SERVER_EMAIL`` and similar addresses is forwarded elsewhere, forwarding can be
broken by SPF or other mechanisms designed to reduce spam. The relay you were
hoping to use may not allow relaying from your specific address, etc.

The only way to be sure that the setup is working from end-to-end is to send
emails *from the production machine and using the production settings*, and
check that they were received.

Requirements
============

We support Django from 2.2 onwards and Python from 3.6 onwards.

If want to *contribute* support for earlier versions of Django or Python, you
should open an issue first so that we can discuss your plans. (Do not suggest
support for Python 2.7, Python 3.x versions that are no longer supported, or
Django versions that are no longer supported: your suggestion will be rejected.)

Management Command
==================

Once this package is installed and added to your Django APPS settings, you get a
new command::

  manage.py email_integration_test

There are no options.

Configuration
=============

This package has a custom setting. Here is an example::

  EMAIL_INTEGRATION_TEST = {
    "IDENTIFIER": "my server",
    "DESTINATIONS": ["foo@example.com", "bar@example.com"],
    "TIMEOUT": 5 * 60,
    "ADDITIONAL_FROM_ADDRESSES": ("foo@myserver.com",),
    "MAILBOX": {
      "TYPE": "IMAP4_SSL",
      "HOST": "example.com",
      "PORT": 1111,
      "USER": "fnord@example.com",
      "PASSWORD": "password1234",
  }

All settings specific to this package belong under the
``EMAIL_INTEGRATION_TEST`` setting.

``IDENTIFIER`` (mandatory string): a name you choose to identify your server for
the sake of email tests.

``DESTINATIONS`` (mandatory iterable of strings): the addresses to which to send
emails.

``TIMEOUT`` (optional number, default of 5 * 60 seconds): a number in
seconds. If the test emails do not arrive during this time, the test has failed.

``ADDITIONAL_FROM_ADDRESSES`` (optional iterable of strings, defaults to an
empty iterable): use this setting to specify other addresses to test *sending
from* in addition to sending from ``SERVER_EMAIL`` and
``DEFAULT_FROM_EMAIL``. (Why this setting? It is possible to configure mail
relays to accept relaying *from* some addresses but not other addresses. So for
some use-case scenarios, it is useful to have the capability to test from more
than ``SERVER_EMAIL`` and ``DEFAULT_FROM_EMAIL``.

``MAILBOX`` (mandatory dictionary): specifies the mailbox to use to check that
the emails were correctly sent. This mailbox *must* be able to read the emails
sent to at least one of the addresses in ``DESTINATIONS``. It contains the
following options:

* ``TYPE`` (mandatory string): the type of mailbox. Currently only
  ``"IMAP4_SSL"`` is supported.

* ``HOST`` (mandatory string): the host to connect to.

* ``PORT`` (optional number): the port to use to connect to ``HOST``. If blank,
  the default port for ``TYPE`` is used.

* ``USER`` (mandatory string): the user name to use to log in.

* ``PASSWORD`` (mandatory string): the password for ``USER``.

Your email backend must be configured so that ``django.core.mail.send_mail``
works. How to do this depends on which backend you use.

How it works
============

When you run ``email_integration_test``, then for each unique email address
``address`` in the tuple made from ``SERVER_EMAIL``, ``DEFAULT_FROM_EMAIL`` and
the addresses in ``ADDITIONAL_FROM_ADDRESSES``:

 * send an email from ``address`` to ``DESTINATIONS`` with the subject::

     Server {IDENTIFIER} is testing sending to {address} at {now} ({uid})

   where ``IDENTIFIER`` and ``address`` are the variables defined above, ``now``
   is the time at which we started sending emails and ``{uid}`` is a unique
   identifier associated with ``address``.

Then the tool polls the mailbox specified in ``MAILBOX`` for evidence that the
emails arrived at their destination. They must arrive within ``TIMEOUT`` for the
test to be successful.

Pick your mail provider carefully
=================================

This is true both in production and for testing this code. Some mail providers
impose restrictions on what they accept.

Example 1: GMail does not allow using *authenticated* SMTP access to send emails
with a ``From:`` address which is different from the address of the account used
for logging into the SMTP server. If you have the account ``foo@gmail.com`` and
try to send emails as if they were from ``foo@example.com``, your emails *will*
go through but they'll be from ``foo@gmail.com``. The explanation is that they
do this to prevent spam, but the fit between this objective and the means to get
there is extremely loose. Since the SMTP access is authenticated, Google *would*
have the capability to deal with spammers. They just don't want that burden so
they prevent the ability to send emails from other addresses. (There's a way to
get Gmail to allow you to select an email address that you prove you control,
but I've got no evidence that this also works for SMTP accesses. Besides this
method requires giving Google your user name and password into another mail
server. I don't trust Google that much.)

This makes GMail a poor candidate for running the test suite (and probably
production but you may have a scenario where it makes sense to use it in
production).

Contributing
============

Once you've cloned the repo, create a new ``./secrets.py`` with appropriate
values. Running the test suite requires real access to a server providing SMTP
and IMAP 4 interfaces. *You* must pick a server *you* have access to.

Tests can be run with::

  $ make dev-venv
  $ make test
