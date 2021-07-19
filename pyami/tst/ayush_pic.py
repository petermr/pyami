def image_extract(pmcid):

    url = f"https://europepmc.org/article/PMC/{pmcid}"

    import chromedriver_autoinstaller
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as ec
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
    from selenium.webdriver.common.alert import Alert
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.chrome.options import Options
    import urllib
    from selenium import webdriver

    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    webdriver = webdriver.Chrome(
        options=options
    )
    print("Started Searching")
    webdriver.get(url)

    images = []
    a = 0
    keep_seaching = True
    while(keep_seaching):
        try:

            results = WebDriverWait(webdriver, 10).until(ec.visibility_of_element_located(
                (By.XPATH, "//a[@class='figures--figure-box']")))
            results = webdriver.find_elements_by_xpath(
                "//a[@class='figures--figure-box']")
        except:
            break
        try:
            button_scroll = WebDriverWait(webdriver, 2).until(ec.visibility_of_element_located(
                (By.XPATH, "//i[@class='fas fa-angle-right fa-stack-1x']")))
        except:
            break

        for result in results:
            img_data = result.get_attribute("style")
            img_data = img_data.strip("background-image: ")
            img_data = img_data.strip('l("')
            img_data = img_data.lstrip('");')
            if img_data not in images:
                images.append(img_data)

        if button_scroll:
            webdriver.execute_script("arguments[0].click();", button_scroll)

        else:
            break

    for image in images:
        response = urllib.request.urlopen(str(image))
        with open(f'{pmcid}_{a}.jpg', 'wb') as f:
            f.write(response.file.read())
        a += 1


image_extract("PMC8120281")
