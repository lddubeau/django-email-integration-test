import unittest
from io import StringIO

from django.core.management.base import CommandError
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.test.testcases import SimpleTestCase
from django.conf import settings


def call_command(*args, **kwargs):
    from django.core.management import call_command as cc
    stdout = StringIO()
    stderr = StringIO()
    kwargs["stdout"] = stdout
    kwargs["stderr"] = stderr
    cc(*args, **kwargs)
    return stdout.getvalue(), stderr.getvalue()


class ConfigurationTestCase(unittest.TestCase):
    maxDiff = None

    def fail_check(self, expect):
        with self.assertRaisesRegex(ImproperlyConfigured, expect):
            call_command("email_integration_test")

    def missing_conf(self, conf):
        settings.EMAIL_INTEGRATION_TEST = dict(settings.EMAIL_INTEGRATION_TEST)
        del settings.EMAIL_INTEGRATION_TEST[conf]
        self.fail_check(r"EMAIL_INTEGRATION_TEST\['{}'\] must be set"
                        .format(conf))

    def missing_mailbox_conf(self, conf):
        settings.EMAIL_INTEGRATION_TEST = dict(settings.EMAIL_INTEGRATION_TEST)
        mailbox = settings.EMAIL_INTEGRATION_TEST["MAILBOX"] = \
            dict(settings.EMAIL_INTEGRATION_TEST["MAILBOX"])
        del mailbox[conf]
        self.fail_check((r"EMAIL_INTEGRATION_TEST\['MAILBOX'\]\['{}'\] must "
                         "be set").format(conf))

    @override_settings()
    def test_no_email_integration_test(self):
        del settings.EMAIL_INTEGRATION_TEST
        self.fail_check("EMAIL_INTEGRATION_TEST must be set in your settings")

    @override_settings(EMAIL_INTEGRATION_TEST="Q")
    def test_bad_email_integration_test(self):
        self.fail_check("EMAIL_INTEGRATION_TEST must be a dictionary")

    @override_settings()
    def test_no_identifier(self):
        self.missing_conf("IDENTIFIER")

    @override_settings()
    def test_no_destinations(self):
        self.missing_conf("DESTINATIONS")

    #
    # If SERVER_EMAIL is not set, Django gives it a default value. So we do not
    # test for an error if it is unset.
    #

    #
    # If DEFAULT_FROM_EMAIL is not set, Django gives it a default value. So we
    # do not test for an error if it is unset.
    #

    @override_settings()
    def test_no_mailbox(self):
        self.missing_conf("MAILBOX")

    @override_settings()
    def test_bad_mailbox(self):
        settings.EMAIL_INTEGRATION_TEST = dict(settings.EMAIL_INTEGRATION_TEST)
        settings.EMAIL_INTEGRATION_TEST["MAILBOX"] = "Q"
        self.fail_check(r"EMAIL_INTEGRATION_TEST\['MAILBOX'\] must be a "
                        "dictionary")

    @override_settings()
    def test_no_mailbox_type(self):
        self.missing_mailbox_conf("TYPE")

    @override_settings()
    def test_bad_mailbox_type(self):
        settings.EMAIL_INTEGRATION_TEST = dict(settings.EMAIL_INTEGRATION_TEST)
        mailbox = settings.EMAIL_INTEGRATION_TEST["MAILBOX"] = \
            dict(settings.EMAIL_INTEGRATION_TEST["MAILBOX"])
        mailbox["TYPE"] = "POP3"
        self.fail_check(r"invalid value for "
                        r"EMAIL_INTEGRATION_TEST\['MAILBOX'\]"
                        r"\['TYPE'\]; we only support IMAP4_SSL")

    @override_settings()
    def test_no_mailbox_host(self):
        self.missing_mailbox_conf("HOST")

    @override_settings()
    def test_no_mailbox_user(self):
        self.missing_mailbox_conf("USER")

    @override_settings()
    def test_no_mailbox_password(self):
        self.missing_mailbox_conf("PASSWORD")


class RunTestCase(SimpleTestCase):
    maxDiff = None

    # Django's test framework sets the email backend to the locmem one, we have
    # to restore it for testing.
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_simple(self):
        stdout, stderr = call_command("email_integration_test")
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    @override_settings()
    def test_timeout(self):
        # We keep the backend that Django's test framework sets. This makes it
        # so that we won't see the emails in the IMAP mailbox, and we'll get a
        # timeout.

        conf = settings.EMAIL_INTEGRATION_TEST = \
            dict(settings.EMAIL_INTEGRATION_TEST)
        conf["TIMEOUT"] = 5
        with self.assertRaisesRegex(CommandError,
                                    "timeout; did not get answers for {}, {}"
                                    .format(settings.SERVER_EMAIL,
                                            settings.DEFAULT_FROM_EMAIL)):
            call_command("email_integration_test")
