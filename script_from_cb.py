import pdb
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
        #self.CB = ChinaBrandResource()
        self.db = pymongo.MongoClient("mongodb://localhost/").cb_info 
        self.__mongodb = self.db 


    def fetch_list_to_mongo(self, base_url, category, real_page_num):
        page_num = 1
        db = self.db

        while True:
            if page_num > real_page_num:
                return 

            
            url = base_url.split(".html")
            url = "%s_page%s.html%s" % (url[0], page_num, url[1])
            #url = "%s%s.html" % (base_url,page_num)

            print(url)    
            print("page_num: "+ str(page_num))
            try:
                products = requests.get(url).text 
            except:
                return 
            page_data = BeautifulSoup(products, 'lxml')
            product_num = 0
            a = 1
            while a:
                product_sku = 0
                b = 1

                while b:
                    try:
                        stock_inpage = json.loads(page_data.select(".same-style")[product_num].find_all("a")[product_sku].attrs.get("data-switch"))['warehouse'][0]['stock']
                        sku_inpage = page_data.select(".same-style")[product_num].find_all("a")[product_sku].attrs.get("data-sku")
                    
                        url_inpage = json.loads(page_data.select(".same-style")[product_num].find_all("a")[product_sku].attrs.get("data-switch"))['warehouse'][0]['goods_link']
                    except:
                        product_sku += 1
                        b = 0 
                        continue 

                    product_sku += 1

                    print(url_inpage, sku_inpage, stock_inpage)
                    if int(stock_inpage) > 10:
                        db.pre_upload.update({"sku": sku_inpage}, {"$set": {"fetch_status":0, "url": url_inpage, "stock":stock_inpage, "category": category}}, True)
                    try:
                        page_data.select(".same-style")[product_num].find_all("a")[product_sku]
                    except:
                        b = 0


                product_num += 1                                                  
                print("the product list_num in the %s page is: %s" % (str(page_num),str(product_num)))
                try:
                    page_data.select(".same-style")[product_num]
                except:
                    a = 0


            page_num += 1 





    def get_page_num(self, url):
        data = requests.get(url).text

        data_page = BeautifulSoup(data, 'lxml')

        text = data_page.select(".listspan .pagination li")[0].text
        result = re.findall(r'(\d+)', text)[-1]
        return int(result)



    def get_categoryName(self, url):
        Name = url.split("-")[1:]
        i = 0
        category_name = ""
        while Name[i] != 'c' and Name[i]:
            category_name = category_name + "-" + Name[i]
            i += 1
            try:
                Name[i]
            except:
                return category_name
        return category_name


    def fetch_all_product(self, lazada_category_name):
        py = pymongo.MongoClient("mongodb://localhost/").cb_info 

        abc = 1
        while True:
            get_date_num = 1
            


            abc += 1
            if abc > 100:
                break



            try:
                row = py.pre_upload.find_one({'fetch_status': 0})
                try: 
                    if py.all_cb_sku.find_one({'sku': row['sku']}):
                        py.pre_upload.update({'sku':row['sku']}, {"set": {'fetch_status': 1}})
                        print("\n SKU EXIST \n")
                        continue 
                except:
                    continue

                if not row:
                    break 
                
                
                
                print("Start upload SKU %s" % row['sku'])

                try:
                    product_page_url = row['url']
                except:
                    py.pre_upload.update({'sku': row['sku']}, {"$set": {'fetch_status': 1}})
                    continue
                
                fetch_status = self.fetch_product_detail(product_page_url, lazada_category_name)
                py.pre_upload.update({'sku': row['sku']}, {"$set": {'fetch_status': 1}})
            except:
                temp = py.pre_upload.update({'sku': row['sku']}, {'$set': {'fetch_status': 1, 'message': 'Exception'}})
                if not temp:
                    break
                with open('fetch_cb_log.log', 'a') as f:
                    traceback.print_exc(file=f)
                    traceback.print_exc() 
                     

    def fetch_product_detail(self, url="", lazada_category_name=None):
        product_page = self.rq.get(url)

        #已获取一个商品详情界面，要求获取其中的所有产品。
        sub_soup = BeautifulSoup(product_page.text,'lxml')
        self.adpter_data(url, sub_soup, lazada_category_name)
        return True 


    def adpter_data(self, url, soup, lazada_category_name):
        time.sleep(1)

        cat_id = [(c.text, c.attrs.get('href')) for c in soup.select(".path a")[1:]]

        cid = re.findall(r"-(\d+)", cat_id[-1][-1])[0]
        try:
            lazada_cid = self.db.all_cb_sku.find_one({"cid": cid})['lazada_cid']
        except:
            lazada_cid = lazada_category_name  

        try:
            category = soup.select_one(".path").text 
        except:
            return 

        try:
            color = soup.select_one(".color .selected a").attrs.get("title").lower()
            if color == "":
                color = "multicolor"
        except:
            color = "multicolor"

        goods_desc = str(soup.select_one(".xxkkk"))
        desc_img = [img.attrs.get('src') for img in soup.select(".xxkkk img")] 
        goods_state = soup.select_one(".supply-status").text.split(':')[-1] 
        list_date = soup.select_one(".listing-time").text.split(':')[-1] 
        #original_img = [img.attrs.get('src').replace("gloimg.chinabrands.com/cb", "gloimg.chinabrands.com") for img in soup.select("#big-img-wrap img")]
        original_img = [img.attrs.get('data-original') for img in soup.select("#big-img-wrap img")]
        if not original_img:
            original_img = [img.attrs.get('data-zoom-image') for img in soup.select("#big-img-wrap img")]

        price = soup.select_one(".price .my_shop_price").attrs.get('orgp')
        quantity = soup.select_one(".goods-num").attrs.get("data-promote-num")
        try:
            
            size = soup.select_one(".attr-ul .selected a").attrs.get('data-value')
        except:
            size = ''

        sku = soup.select_one(".sku").text.split(':')[-1].strip()
        status = 1 if 'restocking' in goods_state.lower() or 'supply' in goods_state.lower() else 0 
        title = soup.select_one(".goods-title").attrs.get('title') 
        downloaded = soup.select_one(".downloaded-time").text.split(':')[-1].strip() 

        sku_data = {'cat_id': cat_id,
                    'category': category,
                    'cid': cid, 
                    'lazada_cid': lazada_cid,
                    'color': color,
                    'desc_img': desc_img,
                    'goods_desc': goods_desc,
                    'goods_state':goods_state,
                    'list_date': list_date,
                    'original_img': original_img,
                    'price': price,
                    'quantity': quantity,
                    'size': size,
                    'sku': sku,
                    'status': status,
                    'title': title,
                    'url': url,
                    'lazada': 0,
                    'lazada1': 0,
                    'downloaded': downloaded,
                    'warehouse': 'YB'}

        package_info = self.get_sku_specification(goods_desc)
        sku_data.update(package_info)

        print(sku_data) 

        self.__mongodb.all_cb_sku.replace_one({'sku':sku}, sku_data, True)

        




    def get_sku_specification(self, description):
        goods_desc = BeautifulSoup(description, 'lxml')
        speci_list = []
        specific = goods_desc.select(".xxkkk20")

        for string in specific:
            string = string.stripped_strings
            temp = ''
            for i in string:
                i = i.strip()
                if ':' in i:
                    temp = i 
                else:
                    i = temp + i 
                    sp = re.sub("[^a-zA-Z0-9:().]+", '',i).strip()
                    sp_split = sp.split(":")
                    try:
                        if len(sp_split) != 2:
                            continue 
                    except:
                        continue
                    speci_list.append(sp_split)
        sp_dict = dict(speci_list)
        print(" 检验数据：%s" % speci_list)

        sp_dict['Package Content'] = sp_dict.get('Package Content') or sp_dict.get('Package Contents', "see the product detail")

        clean_sp = {}
        for k,v in sp_dict.items():
            k = k.split("(")[0].strip()
            k = k.replace(" ", "_")
            k = k.replace(".", "_")
            clean_sp[k.lower()] = v 

        if clean_sp.get('package_size'):
            p_size = clean_sp.get('package_size').split('cm')[0].split('x')
            clean_sp['packeage_length'] = p_size[0].strip() 
            clean_sp['package_width'] = p_size[1].strip() 
            clean_sp['package_height'] = p_size[2].strip()
        else:
            clean_sp['package_length'] = 1
            clean_sp['package_width'] = 1
            clean_sp['package_height'] = 1 

        try:
            clean_sp['ship_weight'] = re.findall(r"(0\.)*(\d+\.\d*)", clean_sp['package_weight'])[0][-1] 
        except:
            try:
                clean_sp['ship_weight'] = re.findall(r"(0\.)*(\d+\.\d*)", clean_sp['packageweight'])[0][-1]
            except:
                try:
                    clean_sp['goods_weight'] = clean_sp['weight']
                except:
                    clean_sp['ship_weight'] = 1 

        clean_sp['goods_brand'] = clean_sp.get('brand', "")
        return clean_sp 




                    


                    

if __name__ == "__main__":

    cbTool = ChinaBrandTools()

    # 自己要传的参数
    lazada_category_name = 10002886
    base_url = "https://www.chinabrands.com/dropshipping-card-reader.html?searchUrl=%2Fsearch%2Fkeywords-notice.html&cat_id="
    category = cbTool.get_categoryName(base_url) 

    real_page_num = cbTool.get_page_num(base_url)
    
    print(real_page_num)
    time.sleep(1)
    #real_page_num = 8
    cbTool.fetch_list_to_mongo(base_url, category, real_page_num)
    #cb中lazada对应的category_id 
    cbTool.fetch_all_product(lazada_category_name)

