import os

SECRET_KEY = "q"

INSTALLED_APPS = (
    'django_email_integration_test',
)

EMAIL_INTEGRATION_TEST = {
    "IDENTIFIER": "email_integration_test",
    "DESTINATIONS": ["dest"],
    "MAILBOX": {
        "TYPE": "IMAP4_SSL",
        "HOST": "host",
        "USER": "user",
        "PASSWORD": "pass",
    },
}

EMAIL_USE_SSL = True
EMAIL_PORT = 465

# Put the variables that should not be shared, and those you should override
# from the defaults above in the secrets.py file.
#
# You should set or override:
#
# SERVER_EMAIL
# DEFAULT_FROM_EMAIL
# EMAIL_HOST
# EMAIL_HOST_USER
# EMAIL_HOST_PASSWORD
# EMAIL_INTEGRATION_TEST["MAILBOX"]["HOST"]
# EMAIL_INTEGRATION_TEST["MAILBOX"]["PORT"]
# EMAIL_INTEGRATION_TEST["MAILBOX"]["USER"]
# EMAIL_INTEGRATION_TEST["MAILBOX"]["PASSWORD"]
# EMAIL_INTEGRATION_TEST["DESTINATIONS"]
#

exec(open(os.path.join("./secrets.py")).read())
