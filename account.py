"""
Bank Account class
"""

from datetime import datetime
from collections import namedtuple  # noqa

import pytz
import itertools
import numbers

from time_zone import TimeZone
from transactions import Transaction

transactions = dict()


class Account:
    """Account object"""

    transaction_counter = itertools.count(1)
    _tz = TimeZone('UTC')
    _interest_rate = 0.005
    _transaction_codes = {
        'deposit': 'D',
        'withdraw': 'W',
        'interest': 'I',
        'rejected': 'X'
    }

    def __init__(self,
                 number: str,
                 first_name: str,
                 last_name: str,
                 initial_balance: numbers.Real = 0,
                 zone: str = None) -> None:

        if zone is not None:
            self.tz = TimeZone(zone=zone)
        self._account_number = number
        self._first_name = None
        self._last_name = None
        self.first_name = first_name
        self.last_name = last_name
        self._full_name = None
        self._balance = Account.validate_initial_balance(initial_balance,
                                                         min_value=0)

    @property
    def account_number(self):
        return self._account_number

    @property
    def tz(self):
        return self._tz

    @tz.setter
    def tz(self, time_zone: TimeZone) -> None:
        if not isinstance(time_zone, TimeZone):
            raise ValueError('Time Zone must be a valid TimeZone object.')
        self._tz = time_zone

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, name: str) -> None:
        self._first_name = Account.validate_name(name, 'first name')
        self._full_name = None

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, name: str) -> None:
        self._last_name = Account.validate_name(name, 'last name')
        self._full_name = None

    @property
    def full_name(self):
        if self._full_name is None:
            self._full_name = f'{self.first_name} {self.last_name}'
        return self._full_name

    @property
    def balance(self):
        return self._balance

    @classmethod
    def get_interest_rate(cls):
        return cls._interest_rate

    @classmethod
    def set_interest_rate(cls, value):
        if not isinstance(value, numbers.Real):
            raise ValueError('Interest rate must be a real number.')
        if value < 0:
            raise ValueError('Interest rate cannot be negative.')
        cls._interest_rate = value

    def generate_conf_number(self, code: str, id_num: int, dt: datetime) -> str:
        """Generate confirmation number for every transaction."""

        dt_stamp = dt.strftime('%Y%m%d%H%M%S')
        transactions[id_num] = {
            'id_num': id_num,
            'code': code,
            'acc_num': self.account_number,
            'dt': dt
        }

        return f'{code}-{self.account_number}-{dt_stamp}-{id_num}'

    def deposit(self, amount: float) -> str:
        """Deposit amount on the balance."""

        amount = Account.validate_real_number(amount, min_value=0.01)

        dt = datetime.now(tz=pytz.utc)
        id_num = next(Account.transaction_counter)
        code = Account._transaction_codes['deposit']
        confirmation = self.generate_conf_number(code, id_num, dt)

        self._balance += amount

        return confirmation

    def withdraw(self, amount: numbers.Real) -> str:
        """Withdraw amount from the balance."""

        amount = Account.validate_real_number(amount, min_value=0.01)

        id_num = next(Account.transaction_counter)
        dt = datetime.now(tz=pytz.utc)

        if self._balance - amount < 0:
            code = Account._transaction_codes['rejected']
            return self.generate_conf_number(code, id_num, dt)

        code = Account._transaction_codes['withdraw']
        confirmation = self.generate_conf_number(code, id_num, dt)

        self._balance -= amount

        return confirmation

    def pay_interest(self):
        """Deposit interest on the balance."""

        interest = self._balance * Account._interest_rate

        dt = datetime.now(tz=pytz.utc)
        id_num = next(Account.transaction_counter)
        code = Account._transaction_codes['interest']

        confirmation = self.generate_conf_number(code, id_num, dt)
        self._balance += interest

        return confirmation

    @staticmethod
    def get_transaction(confirmation: str, tz: str) -> Transaction:
        """Return transaction by confirmation number."""

        id_num = int(confirmation.split('-')[-1])

        return Transaction(**transactions[id_num], tz=tz)

    @staticmethod
    def validate_name(value: str, field_name: str) -> str:
        """Validate the first name and the last name of the account holder."""

        if not isinstance(value, str):
            raise ValueError(
                f'{field_name.capitalize()} must be a string'
            )
        if len(value.strip()) == 0:
            raise ValueError(
                f'{field_name.capitalize()} can not be empty string.'
            )

        return value.strip()

    @staticmethod
    def validate_initial_balance(value: numbers.Real,
                                 min_value: numbers.Real) -> numbers.Real:
        """Validate the initial balance of the account holder."""

        if not isinstance(value, numbers.Real):
            raise ValueError('The value must be a real number.')

        if min_value is not None and value < min_value:
            raise ValueError(f'The value must be at least {min_value}.')

        if value < 0:
            raise ValueError('The value must be a positive number.')

        return value

    @staticmethod
    def validate_real_number(value: numbers.Real,
                             min_value: numbers.Real = 0):
        """Validate the amount passed to a payment method."""

        value = Account.validate_initial_balance(value, min_value)

        if value == 0:
            raise ValueError('The value can not be 0.')

        return value

    # @staticmethod
    # def parse_confirmation_code(confirmation_code: str, tz=None):
    #     """Parse confirmation code."""
    #
    #     Confirmation = namedtuple(
    #         'Confirmation',
    #         'account_number transaction_code transaction_id time_utc time'
    #     )
    #
    #     parts = confirmation_code.split('-')
    #     if len(parts) != 4:
    #         raise ValueError('Invalid confirmation code!')
    #
    #     code, acc_num, dt_raw_utc, id_num = parts
    #
    #     try:
    #         dt = (datetime.strptime(dt_raw_utc, '%Y%m%d%H%M%S').
    #               astimezone(pytz.timezone('UTC')))
    #     except ValueError as ex:
    #         raise ValueError('Invalid transaction datetime!') from ex
    #
    #     if tz is None:
    #         tz = TimeZone('UTC')
    #
    #     if not isinstance(tz, TimeZone):
    #         raise ValueError('Invalid timezone specified!')
    #
    #     dt_format = '%Y-%m-%d %H:%M:%S (%Z)'
    #
    #     dt_preferred = dt.astimezone(pytz.timezone(tz.name))
    #
    #     dt_str = dt.strftime(dt_format)
    #     dt_preferred_str = dt_preferred.strftime(dt_format)
    #
    #     return Confirmation(acc_num, code, id_num, dt_str, dt_preferred_str)
