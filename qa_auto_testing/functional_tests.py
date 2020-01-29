# Steps to follow to get Selenium working in your project: 
# run `pip install selenium`
# Add your we driver to the local directory 
# `geckodriver.exe` or `chromedriver.exe` 
# e.g.: In our case, the driver is in `qa_auto_testing`
# folder as the `functional_test.py` script that uses 
# the driver. Once that is complete, you can start writing 
# the automated test. 


from selenium import webdriver

browser = webdriver.Chrome()
browser.get('http://127.0.0.1:8000/')
print(browser.title)
assert 'CPH Indicator Visualization Tool' in browser.title