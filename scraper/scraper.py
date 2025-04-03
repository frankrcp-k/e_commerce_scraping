import time
import re
import pandas as pd
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#Declare functions
def scrape_data(url:str, class_:str, driver:webdriver)->list:
    url = url
    class_= class_
    driver = driver
    driver.get(url)

    #scroll down to bottom
    last_height = 0
    print("Extracting elements...")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_))
        )

        new_height = driver.execute_script("return document.body.scrollHeight")
        if last_height == new_height or new_height > 150000:
            break
        
        last_height = new_height
    
    #extract product elements
    soup = BeautifulSoup(driver.page_source, "html.parser")
    elements = soup.find_all("div", class_=class_)

    print(len(elements), " Elements extracted")
    return elements

def extract_data_from_elements(elements:list, source: str) -> pd.DataFrame:
    data = []
    if source == 'lotuss':
        for element in elements:
            product_name = element.find(id="product-title").text
            price_element = element.find("p", class_="sc-cVAmsi itbQEF").text.split("/")
            product_price = price_element[0].replace("฿","").strip()
            product_unit = price_element[1].strip() if len(price_element) > 1 else "N/A"

            data.append((product_name, product_price, product_unit))

    elif source == 'freshket':
        for element in elements:
            product_name = element.find(id="product-content").find("h3").text.strip().split(" ")[0]
            product_price = element.find(id="price-value").text
            product_unit = element.find(id="product-content").find("p").text.split("/")[0]

            data.append((product_name, product_price, product_unit))

    return pd.DataFrame(data, columns=["product_name", f"product_price_{source}", f"product_unit_{source}"])

def extract_unit(text:str)->str:
    match = re.search(r"(\d+\s?[กรัม|ก.|กก.|แพ็คละ|หวีละ|กก.ละ]+)", text)
    return match.group(1) if match else None


def clean_product_name(text:str)->str:
    replace = ["โครงการหลวง", "โลตัส", "โอ้ เวจจี้", "เวจ สเตอร์", "มินนะมาเมะ", "FRESH HOUR "]
    for term in replace:
        text = text.replace(term, "")
    
    return text.strip().split(" ")[0]

def clean_and_min_price(df:pd.DataFrame, column:str)->pd.DataFrame:
    df = df.copy()
    df_cleaned = (
        df
        .loc[df.dropna(subset=[column]).groupby("product_name")[column].idxmin()]
        .reset_index(drop=True)
    )
    
    return df_cleaned


# Set up Chrome options for headless browsing
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Firefox(options=options)



#extract and transform data from lotuss
df_lotuss = extract_data_from_elements(scrape_data("https://www.lotuss.com/th/category/fresh-food-deal/vegetable-and-fruit?sort=relevance:DESC", "product-grid-item", driver), "lotuss")
df_lotuss.loc[df_lotuss["product_unit_lotuss"] == "N/A", "product_unit_lotuss"] = df_lotuss.loc[df_lotuss["product_unit_lotuss"] == "N/A", "product_name"].apply(extract_unit)
df_lotuss["product_name"] = df_lotuss["product_name"].apply(clean_product_name)
df_lotuss["product_price_lotuss"] = pd.to_numeric(df_lotuss["product_price_lotuss"], errors="coerce").astype("Int64")
df_lotuss = clean_and_min_price(df_lotuss, "product_price_lotuss")


#extract and transform data from freshket
df_freshket = extract_data_from_elements(scrape_data("https://freshket.co/market/fruit-vegetable", "MuiGrid-root MuiGrid-item MuiGrid-grid-xs-6 MuiGrid-grid-sm-6 MuiGrid-grid-md-4 MuiGrid-grid-lg-3", driver), "freshket")
df_freshket["product_price_freshket"] = pd.to_numeric(df_freshket["product_price_freshket"], errors="coerce").astype("Int64")
df_freshket = clean_and_min_price(df_freshket, "product_price_freshket")


#merge 2 dataframe and write excel file
filepath = sys.argv[1]
today = pd.to_datetime('today').date()
df_merged = pd.merge(df_freshket, df_lotuss, on="product_name", how="outer").sort_values(by="product_name")
df_merged["date_extracted"] = today
df_merged.to_excel(f"{filepath}", index=False)