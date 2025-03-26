import sys
import sentry_sdk
from epicevents.cli import init_cli
from epicevents.config import SENTRY_DSN, SENTRY_ENV


# Initialising Sentry
def sentry_init():
    """
    Sentry has a few entries in the app :
    - In the __main__ script to log unhandled errors.
    - In epicevents.permissions.auth.check_auth() & authenticate_user()
      to log forbidden activities & authentication failures.
    """
    if SENTRY_DSN != "https://SENTRYKEY.ingest.de.sentry.io/PROJECTCODE":
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENV,
            traces_sample_rate=0.0  # deactivates perf tracking
        )


# Main app entry point
def main():
    sentry_init()
    app = init_cli()

    try:
        app(obj={})
    except Exception as e:
        if SENTRY_ENV == "production":
            # Sends to Sentry if we're in production
            sentry_sdk.capture_exception(e)
        else:
            # Log the error in non-production environments
            print(f"An error occurred: {e}")

        raise


if __name__ == "__main__":
    main()
