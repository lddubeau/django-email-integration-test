import datetime
from imaplib import IMAP4_SSL
import uuid
import ssl
import time
from typing import Optional, Any, Dict, List

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from django.core.mail import send_mail


def require_setting(name: str) -> Any:
    try:
        ret = getattr(settings, name)
    except AttributeError:
        raise ImproperlyConfigured(f"{name} must be set in your settings")

    return ret


def require_conf(conf: Dict[str, Any], name: str,
                 path: Optional[str] = None) -> Any:
    sub = "" if path is None else f"['{path}']"
    try:
        ret = conf[name]
    except KeyError:
        raise ImproperlyConfigured(f"EMAIL_INTEGRATION_TEST{sub}['{name}'] "
                                   "must be set")

    return ret


def handle_response(desc: str, response) -> Any:
    result = response[0]
    if result != "OK":
        raise CommandError(f"{desc} failed with {result}")
    return response[1]


class Command(BaseCommand):
    """
    Perform an email integration test.
    """
    help = __doc__

    def send_emails(self, verbose: bool, from_addresses: List[str],
                    identifier: str,
                    destinations: List[str]) -> Dict[uuid.UUID, str]:
        now = datetime.datetime.now()

        uid_to_from_address = {}

        for from_address in from_addresses:
            uid = uuid.uuid1()
            subject = f"Server {identifier} is testing sending from " \
                f"{from_address} at {now} ({uid})"
            if verbose:
                self.stdout.write(f"Sending from {from_address} to "
                                  f"{destinations} an email titled: {subject}")
            # Retry sending the same email until we don't get a connection
            # reset error. (Alas Dreamhost seems unstable.)
            while True:
                try:
                    send_mail(subject, "", from_address, destinations)
                    break
                except ConnectionResetError:
                    time.sleep(1)
                    pass

            uid_to_from_address[uid] = from_address

        return uid_to_from_address

    def _check_sent(self, verbose: bool, imap: IMAP4_SSL,
                    timeout: int,
                    uid_to_from_address: Dict[uuid.UUID, str]) -> None:
        handle_response("select INBOX", imap.select())

        end = time.time() + timeout
        while True:
            if time.time() > end:
                # We sort the addresses to get a stable output.
                unresponsive = ", ".join(uid for uid in
                                         sorted(uid_to_from_address.values()))
                raise CommandError("timeout; did not get answers for "
                                   f"{unresponsive}")
            remaining_uids = {}

            # Sending a noop prompts some IMAP servers to *really* check
            # whether there have been new emails delivered. Without it, it
            # takes longer for us to find the emails we are looking for.
            handle_response("noop", imap.noop())

            # It may be possible to reduce the number of queries to the IMAP
            # server by ORing the SUBJECT queries. However, it complicates the
            # code quite a bit.
            for uid, from_address in uid_to_from_address.items():
                if verbose:
                    self.stdout.write(f"Searching for: {uid} from "
                                      f"{from_address}...")
                mess_uid = \
                    handle_response("search",
                                    imap.uid(
                                        "search",
                                        f'SUBJECT "{uid}" '  # type: ignore
                                        f'FROM "{from_address}"'))
                if mess_uid[0] == b"":
                    remaining_uids[uid] = from_address
                else:
                    if verbose:
                        self.stdout.write(f"Found {uid}!")
                    answer = handle_response("store", imap.uid(
                        "store", mess_uid[0],
                        "+FLAGS",  # type: ignore
                        r"(\Deleted \Seen)"   # type: ignore
                    ))
                    if verbose:
                        self.stdout.write(repr(answer))

            if len(remaining_uids) == 0:
                break

            uid_to_from_address = remaining_uids
            # Give a bit of respite to the IMAP server.
            time.sleep(1)

    def check_sent(self, verbose: bool, imap_host: str, imap_port: int,
                   imap_user: str, imap_password: str, timeout: int,
                   uid_to_from_address: Dict[uuid.UUID, str]) -> None:
        context = ssl.create_default_context()
        if verbose:
            self.stdout.write("Connecting to IMAP box at "
                              f"{imap_host}:{imap_port}")
        imap = IMAP4_SSL(imap_host, imap_port,   # type: ignore
                         ssl_context=context)
        handle_response("login", imap.login(imap_user, imap_password))
        try:
            self._check_sent(verbose, imap, timeout, uid_to_from_address)
        finally:
            imap.logout()

    def handle(self, *args: Any, **options: str) -> None:
        verbosity = int(options["verbosity"])

        verbose = verbosity > 1

        conf = require_setting("EMAIL_INTEGRATION_TEST")
        if not isinstance(conf, dict):
            raise ImproperlyConfigured("EMAIL_INTEGRATION_TEST must "
                                       "be a dictionary")

        identifier = require_conf(conf, "IDENTIFIER")
        destinations = require_conf(conf, "DESTINATIONS")
        timeout = conf.get("TIMEOUT", 5 * 60)
        additional = conf.get("ADDITIONAL_FROM_ADDRESSES", ())
        server_email = require_setting("SERVER_EMAIL")
        default_from_email = require_setting("DEFAULT_FROM_EMAIL")

        mailbox = require_conf(conf, "MAILBOX")

        if not isinstance(mailbox, dict):
            raise ImproperlyConfigured("EMAIL_INTEGRATION_TEST['MAILBOX'] "
                                       "must be a dictionary")

        mailbox_type = require_conf(mailbox, "TYPE", "MAILBOX")
        if mailbox_type != "IMAP4_SSL":
            raise ImproperlyConfigured(
                "invalid value for EMAIL_INTEGRATION_TEST['MAILBOX']['TYPE']; "
                "we only support IMAP4_SSL")

        imap_host = require_conf(mailbox, "HOST", "MAILBOX")
        imap_port = mailbox.get("PORT", None)
        imap_user = require_conf(mailbox, "USER", "MAILBOX")
        imap_password = require_conf(mailbox, "PASSWORD", "MAILBOX")

        uid_to_from_address = \
            self.send_emails(verbose, list(set((server_email,
                                                default_from_email) +
                                               additional)),
                             identifier, destinations)

        self.check_sent(verbose, imap_host, imap_port, imap_user,
                        imap_password, timeout,
                        uid_to_from_address)
