import argparse
import datetime as dt
import logging
from time import sleep

from tello_renewal.renew import Renewer
from tello_renewal.utils.logging import configure_logging
from tello_renewal.utils.config import get_settings
from tello_renewal.emailer import Emailer

configure_logging()
logger = logging.getLogger(__name__)


def main(dry_run: bool) -> None:
    if dry_run:
        logger.info("Executing dry run")

    emailer = Emailer(
        get_settings().smtp.server,
        get_settings().smtp.port,
        get_settings().smtp.from_email,
    )
    emailer.login(
        get_settings().smtp.username,
        get_settings().smtp.password,
    )

    with Renewer(
        get_settings().tello.email,
        get_settings().tello.password,
        get_settings().tello.card_expiration,
        emailer,
        dry_run,
    ) as renewer:
        renewer.login()

        if (days_until_renewal := (renewer.renewal_date - dt.date.today()).days) > 1:
            logger.warning(f"Renewal date is {days_until_renewal} days away on {renewer.renewal_date:%m/%d/%Y}")
            if dry_run:
                logger.info("Proceeding with dry run anyway...")
            else:
                logger.info("Exiting...")
                return
        logger.info(f"New balance: {renewer.new_balance}")

        renewer.open_renewal_page()
        renewer.autofill_card_expiration()
        renewer.check_notification_box()
        renewer.submit_order()
        sleep(30)


def entrypoint() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)


if __name__ == "__main__":
    entrypoint()
