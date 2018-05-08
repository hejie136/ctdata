import pdb
from script_from_cb import ChinaBrandTools as adpter
import requests
import time 
import json
import hashlib 
from bs4 import BeautifulSoup 
import pymongo 
import re 
import traceback 

class ChinaBrandTools():
    def __init__(self):
        self.rq = requests.Session()
        self.db = pymongo.MongoClient("mongodb://localhost/").lxy_cb_info 






    def get_real_page(self, url):
        data = requests.get(url).text
        data_soup = BeautifulSoup(data, 'lxml')
        text = data_soup.select(".listspan .pagination li")[0].text
        num = re.findall(r'(\d+)', text)[-1]
        return int(num)


    def get_categoryName(self, url):
        try:
            text = url.split(".html")[0]
            name = text.split("dropshipping-")[-1]
        except:
            name = 'No Found'
        return name 

    def fetch_data_to_mongo(self, url, category_name, real_cat_product_page):
        page_num = 1
        db = self.db

        while page_num <= real_cat_product_page:
            upload_sku_number = 1
            page_num += 1
            text = url.spilt(".html")
            url = "%s_page%s.html%s" % (url[0], page_num, url[1])

            print("Start upload the page of %s---------->" % str(page_num))
            try:
                products_list = requests.get(url).text 
                products_list_soup = BeautifulSoup(products_list, 'lxml')
            except:
                return 
            
            #一个页面有两层，第一层是SPU,第二层是SKU
            SPU_exist = 1
            spu_no = 0
            #当代页面找不到此SPU时，循环结束
            while SPU_exist:

                sku_no = 0
                SKU_exist = 1
                while SKU_exist:
                    try:
                        sku_stock = json.loads(products_list_soup.select(" .same-style")[spu_no].find_all('a')[sku_no].attr.get('data-switch'))['warehouse'][0]['stock']
                        sku_name = products_list_soup.select(".same-style")[spu_no].find_all("a")[sku_no].attr.get('data-sku')
                        sku_url = json.loads(products_list_soup.select(" .same-style")[    spu_no].find_all('a')[sku_no].attr.get('data-switch'))['warehouse'][0]['goods_link']

                    except:
                        spu_no += 1
                        SKU_exist = 0
                        #?????
                        continue
                    sku_no += 1


                    if int(sku_stock) > 10:

                        result = "上传的第%s个，SKU_number: %s---->SKU_stock: %s" % (upload_sku_number,sku_name, sku_stock)
                        print(result)
                        upload_sku_number += 1
                        db.pre_upload.update({"sku": sku_name}, {"$set": {"fetch_status";0, 'url': sku_url, "stock": sku_stock, "category": category_name}}, True)
                        # True 代表
                
                try:
                    products_list_soup.select(".same-style")[spu_no]
                except:
                    SPU_exist = 0

            page_num += 1 
                    





    def fetch_all_product(lazada_category_id):
        #从mongodb中找出要上传sku的url,加载其详情界面适配数据并上传
        db = self.db 

        #找到所有fetch_status=0的sku_url
        while True:
            try:
                row = py.pre_upload.find_one({'fetch_status': 0})
                try:
                    if py.all_cb_sku.find_one({"sku": row['sku']}):
                        py.pre_upload.update({"sku": row['sku']}, {"$set": {'fetch_status': 1}})
                        print("\n SKU EXIST \n")
                        continue
                except:
                    pass 

                if not row:
                    break 

                try:
                    product_page_url = row['url']
                except:
                    py.pre_upload.update({'sku': row['sku']},{"$set": {'fetch_status':1, 'message': 'Exception'}})
                    continue 
                result = self.fetch_product_detail(product_page_url, lazada_category_id)
                py.pre_upload.update({"sku": row['sku']}, {'$set': {fetch_status: 1}})

            except:
                temp = py.pre_upload.update({'sku': row['sku']},{"$set": {'fetch_status':1, 'message': 'Exception'}})
                if not temp:
                    break 
                with open('lxy_fetch_cb_log', 'a') as f:
                    #a:只可写不可读， a+覆盖模式写
                    traceback.print_exc(file=f)
                    traceback.print_exc() 

    def fetch_product_detail(self, url='', lazada_category_id=None):
        product_page = self.rq.get(url)
        soup = BeautifulSoup(product_page, 'lxml')
        self.adpter_data(url, soup, lazada_category_id)
        return True

    def adpter_data(url, product_page, lazada_category_id):
        time.sleep(1)
        cid_id = [(c.text, c.attr.get("href")) for c in product_page.select(".path a")[1:]]
        cid = re.findall(r'-(\d+)', cid_id[-1][-1])[0]
        lazada_cid = lazada_category_id 
        try:
            category = product_page.select(".path").text 
        except:
            return 
        try:
            color = product_page.select_one(".color .selected a").attr.get("title").lower
            if color == '':
                color = 'multicolor'
        except:
            color = 'multicolor'
	goods_desc = str(product_page.select_one(".xxkkk"))
        desc_img = [img.attrs.get('src') for img in product_page.select(".xxkkk img")]
        goods_state = product_page.select_one(".supply-status").text.split(':')[-1]
        list_date = product_page.select_one(".listing-time").text.split(':')[-1]
         #original_img = [img.attrs.get('src').replace("gloimg.chinabrands.    com/cb", "gloimg.chinabrands.com") for img in soup.select("#big-img-wrap i    mg")]
        original_img = [img.attrs.get('data-original') for img in product_page.select("#big-img-wrap img")]
         if not original_img:
        original_img = [img.attrs.get('data-zoom-image') for img in product_page.select("#big-img-wrap img")]
 
        price = product_page.select_one(".price .my_shop_price").attrs.get('orgp')
        quantity = product_page.select_one(".goods-num").attrs.get("data-promote-n    um")
        try:
            size = product_page.select_one(".attr-ul .selected a").attrs.get('data    -value')
        except:
            size = ''
 
        sku = product_page.select_one(".sku").text.split(':')[-1].strip()
        status = 1 if 'restocking' in goods_state.lower() or 'supply' in goods_state.lower() else 0 
        title = product_page.select_one(".goods-title").attr.get("title")
                                     

        





if __name__ == '__main__':

    cbTool = ChinaBrandTools()

    url = ''
    lazada_category_id = 0

    #该类别产品占多少页
    real_cat_product_page  = cbTool.get_real_page()
    category_name = cbTool.get_categoryName(url)
    #将该类别所有产品对应的url传入mongodb
    cbTool.fetch_data_to_mongo(url, category_name, real_cat_product_page)

    cbTool.fetch_all_product(lazada_category_id)
