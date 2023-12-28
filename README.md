**1. Install firefox:**

    Mac - https://www.mozilla.org/ru/firefox/mac/
    Windows - https://www.mozilla.org/ru/firefox/windows/
    Linux - https://www.mozilla.org/ru/firefox/linux/

**2. Run main.py**
```
python main.py
```

**Instructions:**

How to run the browser in the background ( headless mood ) ?
-
uncomment - # options.add_argument("--headless")
```python
options = webdriver.FirefoxOptions()
# options.add_argument("--headless")  # Включение режима headless
options.add_argument("--lang=en-US,en;q=0.9")
```

How to add jars ?
-
At the pars_html method in the parameter banks can instruct the required banks
```python
dict_currencies = pars.pars_html(banks=['Raiffeisenbank'])
print(dict_currencies)
```