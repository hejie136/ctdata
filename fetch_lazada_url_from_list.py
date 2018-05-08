import requests
from bs4 import BeautifulSoup
import pymongo
import time

headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
            "upgrade-insecure-requests":"1",
            "Accept-Language": "en-us,en;q=0.8"
        }

proxy_ips = []

def get_proxy_ips():
    """
        get 20 proxy ip list
    """
    if proxy_ips:
        return
    print("Start to get proxy ips")
    req = requests.get('https://www.us-proxy.org/', headers=headers)
    if req.status_code != 200:
        return False
    html = req.text
    bs4 = BeautifulSoup(html, "lxml")
    for td in bs4.select("#proxylisttable tr"):
        try:
            ip, port = td.select("td")[:2]
            iport = "%s:%s" % (ip.text, port.text)
            proxy_ips.append(iport)
        except:
            print("no ip port")


# fetch lazada store url list 
store_name = "dd-store"
page = 200 
i = 100
while i < page:
    url = "http://www.lazada.com.my/tb-collection/?dir=desc&itemperpage=120&sort=ratingdesc&page=%s" % i
    # print(url)
    # get_proxy_ips()
    # for idx, proxy_ip in enumerate(proxy_ips):
    #     print("start to try proxy IP:%s" % proxy_ip)
    #     if idx == 3:
    #         proxy_ips = []
    #         get_proxy_ips()
    #         proxy_ips[idx + 1:] = proxy_ips
    #     if idx == 8:
    #         print("No product, need check it")
    #         break

    c = requests.get(url, headers=headers) # , proxies={"http": proxy_ip})
    soup = BeautifulSoup(c.text, "lxml")
    db = pymongo.MongoClient("mongodb://localhost:27017/").lazada
    hrefs = ["https://www.lazada.com.my" + h.attrs['href'] for h in soup.select(".c-product-card__name")] 

    for url in hrefs:
        print(url)
        print(db.product.update({"url": url}, {"status":0, "url":url}, upsert=True))
    i += 1
