from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import csv

# служебные импорты
import time
import functools


# декоратор для измерения скорости выполнения функций
def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__} executed in {end_time - start_time} seconds")
        return result

    return wrapper


class ParsBybit():
    exhange_rates = {}

    def __init__(self, url, timeout_cookies, timeout_pars):
        """
        url: url to pars
        timeout_cookies: timeout in seconds
        timeout_pars: timeout in seconds
        """
        self.url = url
        self.timeout_cookies = timeout_cookies
        self.timeout_pars = timeout_pars

    @classmethod
    def BS4_Parser(cls, bank, html_code, transaction, currency):
        soup = BeautifulSoup(html_code, 'html.parser').find('span', class_='price-amount')

        if cls.exhange_rates.get(bank) is not None:
            # Ключ уже существует
            pass
        else:
            # Ключ отсутствует, создаем его
            cls.exhange_rates[bank] = {'buy': {}, 'sell': {}}

        if transaction == 'buy':
            cls.exhange_rates[bank]['buy'][currency] = soup.text
            print(soup.text, 'buy')
        elif transaction == 'sell':
            cls.exhange_rates[bank]['sell'][currency] = soup.text
            print(soup.text, 'sell')

    @timer_decorator
    def pars_html(self, banks):
        # options для настройки драйвера ( чтобы добавить куки и т.д. )
        options = webdriver.FirefoxOptions()
        # options.add_argument("--headless")  # Включение режима headless
        options.add_argument("--lang=en-US,en;q=0.9")
        # options.add_argument("--window-size=1920, 1080")  # размер окна, если использовать граф интерфейс

        # Инициализация драйвера с объектом options
        driver = webdriver.Firefox(options=options)
        driver.maximize_window()

        try:
            # ADDED COOKIES
            driver.set_page_load_timeout(self.timeout_cookies)

            try:
                # Загрузка страницы
                driver.get(url=self.url)

            except TimeoutException:
                # Ваши куки
                cookies = [
                    {'domain': '.bybit.com', 'expiry': 1703763852, 'httpOnly': False, 'name': '_ym_isad',
                     'path': '/',
                     'sameSite': 'None', 'secure': True, 'value': '2'},
                    # {'domain': '.bybit.com', 'name': '_ga_SPS4ND2MGC', 'path': '/',
                    #  'sameSite': 'None', 'secure': False, 'value': 'GS1.1.1703710762.1.1.1703711137.60.0.0'},
                ]

                for cookie in cookies:
                    driver.add_cookie(cookie)

            for bank in banks:
                # еще один таймаут, чтобы страница не грузилась долго
                driver.set_page_load_timeout(self.timeout_pars)
                # объект для явного ожидания, чтобы не было ошибок, что элемент не найден на странице
                wait = WebDriverWait(driver, 1)

                try:
                    # Загрузка страницы
                    driver.get(url=self.url)

                except TimeoutException:
                    # это сработает, если куки не успели примениться
                    try:
                        driver.find_element(By.XPATH,
                                            value='//button[@class="ant-btn css-7o12g0 ant-btn-primary css-7o12g0 ant-btn-custom '
                                                  'ant-btn-custom-middle ant-btn-custom-primary bds-theme-component-light"]').click()
                        print('кукисы не успели примениться')
                    except NoSuchElementException:
                        print('кукисы успели примениться')

                    # парсинг покупок
                    driver.find_element(By.ID, 'paywayAnchorList').click()
                    driver.find_element(By.XPATH, f'//div[@class="content"]/span[@title="{bank}"]').click()
                    driver.find_element(By.CSS_SELECTOR,
                                        "#paywayList .btn-confirm").click()

                    def XPATH_wait_until(XPATH_text):
                        """
                        эта функция жмет на кнопку продажи и покупки.
                        """
                        btn = wait.until(
                            EC.visibility_of_element_located(
                                (By.XPATH, f'{XPATH_text}')
                            )
                        )
                        btn.click()

                    ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='buy',
                                         currency='USDT')  # html код покупки (usdt)
                    XPATH_wait_until('//div[@class="by-switch__item"]')  # выбираем продажи

                    # если выйдет предупреждение
                    try:
                        btn = wait.until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, ".otc__dialog.by-modal .by-button--contained.by-button--brand, "
                                                  ".otc__root .by-button--contained.by-button--brand, .otc__select-dropdown"
                                                  ".by-button--contained.by-button--brand")
                            )
                        )
                        btn.click()
                    except:
                        print('предупреждения не было')

                    ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='sell',
                                         currency='USDT')  # html код продажи (usdt)
                    driver.find_element(By.XPATH, '//div[@class="by-switch__item"]').click()  # кнопка продажи

                    currencies = ['BTC', 'ETH', 'USDC']
                    for currency in currencies:
                        driver.find_element(By.XPATH,
                                            '//div[@class="ant-select-selector"]').click()  # список с валютами

                        btn = wait.until(
                            EC.visibility_of_element_located(
                                (By.XPATH, f"//div[@class='fiat-otc-option-flex' and contains(., '{currency}')]")
                            )
                        )
                        btn.click()

                        if currency == 'BTC':
                            XPATH_wait_until('//div[@class="by-switch__item"]')  # выбираем продажа или покупка

                            ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='sell',
                                                 currency=currency)  # продажа

                            XPATH_wait_until('//div[@class="by-switch__item"]')  # выбираем продажа или покупка

                            ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='buy',
                                                 currency=currency)  # покупка
                        elif currency == 'ETH':
                            XPATH_wait_until('//div[@class="by-switch__item"]')  # выбираем продажа или покупка

                            ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='buy',
                                                 currency=currency)  # покупка

                            XPATH_wait_until('//div[@class="by-switch__item"]')  # выбираем продажа или покупка

                            ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='sell',
                                                 currency=currency)  # продажа
                        elif currency == 'USDC':
                            XPATH_wait_until('//div[@class="by-switch__item"]')  # выбираем продажа или покупка

                            ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='sell',
                                                 currency=currency)  # продажа
                            XPATH_wait_until('//div[@class="by-switch__item"]')  # выбираем продажа или покупка

                            ParsBybit.BS4_Parser(bank=bank, html_code=driver.page_source, transaction='buy',
                                                 currency=currency)  # покупка
        except Exception as e:
            print("ошибка", e)
        finally:
            # посмотреть кукисы
            # print(driver.get_cookies())

            driver.quit()

        return ParsBybit.exhange_rates


# timeout зависит от интернета ( тут скорость указана для интернета 80-90 мбит/с )
pars = ParsBybit(url='https://www.bybit.com/fiat/trade/otc/?actionType=1&token=USDT&fiat=RUB&paymentMethod=',
                 timeout_cookies=1.75,
                 timeout_pars=2)

# функция выполняется от 5 до 15 секунд ( зависит от скорости интернета )
dict_currencies = pars.pars_html(banks=['Raiffeisenbank'])
print(dict_currencies)

with open('data.csv', 'w', newline='') as csvfile:
    fieldnames = ['Валюта', 'Банк', 'Курс']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for bank, values in dict_currencies.items():
        for operation, currencies in values.items():
            for currency, rate in currencies.items():
                writer.writerow({'Валюта': currency, 'Банк': f'{bank}', 'Курс': f"{rate}₽ ({operation})"})

    print('данные успешно записаны')
