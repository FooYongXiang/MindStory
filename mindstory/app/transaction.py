from datetime import datetime
class Transaction:
    def __init__(self, amount, user_email, random_code):
        self._amount = amount
        self._user_email = user_email
        self._date_time = datetime.now()
        self._random_code = random_code

    def get_amount(self):
        return self._amount

    def get_user_email(self):
        return self._user_email

    def get_date_time(self):
        return self._date_time

    def get_random_code(self):
        return self._random_code

    def set_amount(self, amount):
        self._amount = amount

    def set_user_email(self, email):
        self._user_email = email

    def set_random_code(self, random_code):
        self._random_code = random_code