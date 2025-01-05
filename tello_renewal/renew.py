import datetime as dt
from functools import cached_property
import logging
from types import TracebackType
from typing import Callable, ClassVar, Self

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from tello_renewal.tello import BalanceQuantity, AccountBalance
from tello_renewal.emailer import Emailer

logger = logging.getLogger(__name__)


class Renewer:
    _ELEMENT_TIMEOUT: ClassVar[float] = 30

    def __init__(self, email: str, password: str, card_expiration: dt.date, emailer: Emailer, dry_run: bool = True) -> None:
        self._emailer = emailer
        self._email = email
        self._password = password
        self._card_expiration = card_expiration
        self._dry_run = dry_run

    @cached_property
    def _webdriver(self) -> webdriver.Firefox:
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument("--headless")
        return webdriver.Firefox(options=firefox_options)

    def __enter__(self) -> Self:
        self.open_login_page()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None,) -> None:
        if exc_type:
            self._emailer.send_failure_message(self._email)
        return self._webdriver.__exit__(exc_type, exc_val, exc_tb)

    def open_login_page(self) -> None:
        self._webdriver.get("https://tello.com/account/login")

    def login(self) -> None:
        email_input = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "input#i_username"))
        )
        email_input.send_keys(self._email)

        password_input = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "input#i_current_password"))
        )
        password_input.send_keys(self._password)
        email_input.send_keys(Keys.ENTER)

    @cached_property
    def renewal_date(self) -> dt.date:
        renewal_date_element = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "span.card_text > span"))
        )
        return dt.datetime.strptime(renewal_date_element.text, "%m/%d/%Y").date()

    @cached_property
    def current_balance(self) -> AccountBalance:
        balance_elements = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, "div.progress_holder div.pull-left.font-size30"))
        )
        return AccountBalance(*[
            BalanceQuantity.from_tello(e.text)
            for e in balance_elements
        ])

    @cached_property
    def plan_balance(self) -> AccountBalance:
        plan_data = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.subtitle > div.subtitle_heading"))
        ).text
        plan_minutes = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.subtitle > div:nth-child(4)"))
        ).text
        plan_texts = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.subtitle > div:nth-child(5)"))
        ).text
        return AccountBalance(
            BalanceQuantity.from_tello(plan_data),
            BalanceQuantity.from_tello(plan_minutes),
            BalanceQuantity.from_tello(plan_texts),
        )

    @cached_property
    def new_balance(self) -> AccountBalance:
        return self.current_balance + self.plan_balance

    def open_renewal_page(self) -> None:
        renew_button = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "button#renew_plan"))
        )
        renew_button.click()

    def autofill_card_expiration(self) -> None:
        expiration_month_select = Select(WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "select#cc_expiry_month"))
        ))
        expiration_month_select.select_by_value(str(self._card_expiration.month))

        expiration_year_select = Select(WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "select#cc_expiry_year"))
        ))
        expiration_year_select.select_by_value(str(self._card_expiration.year))

    def check_notification_box(self) -> None:
        notification_checkbox = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "input[type=checkbox][name=recurring_charge_notification]"))
        )
        notification_checkbox.click()

    def submit_order(self) -> None:
        finalize_order_button = WebDriverWait(self._webdriver, self._ELEMENT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "button#checkout_form_submit_holder"))
        )
        if self._dry_run:
            assert finalize_order_button.text.startswith("Finalize Order")
            logger.info(f"Found finalize order button, skipping click for dry run")
        else:
            finalize_order_button.click()
            self._emailer.send_success_message(self._email, self.new_balance)
