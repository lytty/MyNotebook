from selenium import webdriver
from selenium.webdriver.common.keys import Keys

googledriver_path = 'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'
driver = webdriver.Chrome(executable_path=googledriver_path)
driver.get('http://www.python.org')
assert "Python" in driver.title
elem = driver.find_element_by_name("q")
elem.send_keys('pycon')
elem.send_keys(Keys.RETURN)
print(driver.page_source)
