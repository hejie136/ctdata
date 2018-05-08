import requests
import time 
import json
import hashlib
from bs4 import BeautifulSoup
import pymongo
import re 
import traceback
import pdb


APP_SECRET = "5702f0eea31d2f4b4003df15e08a2348"

class ChinaBrandResource():
    
    def __init__(self ,EMAIL="zchv@msn.com", 
            PASSWORD="2K2bXsl2#$bls(@DD",
            APP_ID="1365535200",
            APP_SECRET="5702f0eea31d2f4b4003df15e08a2348",
            visit_from="api"):
        self.__email = EMAIL
        self.__password = PASSWORD
        self.__app_secret = APP_SECRET
        self.__app_id = APP_ID
        self.__mongodb = pymongo.MongoClient("mongodb://localhost/").new_cb_info
        self.__token = None 
        self.__base_url = 'https://%s.chinabrands.cn/v2' % visit_from

    def get_category(self):
        req_url = '%s/category/index' % self.__base_url
        result = self._post(url = req_url)
        return result

    def get_shipping_fee(self, sku=None, weight=None, method='WISHAMNJ'):
        weight = float(weight)
        #return round((90*weight +8)/8.0, 2)
        #question 2
        req_url = '%s/shipping/cost' % self.__base_url
        data = {'country' : "US",
                'shipping' : method,
                'goods' : json.dumps([{'sku' : sku, 'quantity' : '1'},])
                }

        result = self._post(url=req_url, data=data)
        return float(result.get(method, {}).get('shipping_fee') + 1.2)

    def put_order(self, **kwargs):
        req_url = '%s/order/creat' % self.__base_url
        data = [{"user_order_sn": kwargs['user_order_sn'],
            "country": kwargs['country'],
            "warehouse": 'YB',
            "firstname": kwargs['firstname'],
            "lastname": kwargs['lastname'],
            "addressline1": kwargs['addressline1'],
            "addressline2": kwargs['addressline2'],
            "shipping_method": kwargs['shipping_method'],
            "city": kwargs['city'],
            "zip": kwargs['zip'],
            "order_remark": "",
            "order_platforms": kwargs.get("order_platforms", ""),
            "original_order_id": kwargs.get("original_order_id", ""),
            "original_account": kwargs.get("original_account",""),
            "insure_fee": 0,
            "use_point": 1,
            "goods_info": kwargs['goods_info'],
            }, ]

        json_data = json.dumps(data)
        signature_string = hashlib.md5(self.__app_secret+json_data)
        post_data = {'signature': signature_string, 'order': json_data}
        result = self._post(url=req_url, data=post_data)
        print(result)
        for vv in result.values():
            data[0].updata(vv)
        # self.__mongodb.order_result.insert(data[0])
        return result

    
    def pay_order(self, order_sn):
        req_url = '%s/order/pay' % self.__base_url
        json_data = json.dumps(order_sn)
        signature_string = hashlib.md5((self.__app_secret+json_data).encode()).hexdigest()
        post_data = {'signature': signature_string, 'order': json_data}
        result = self._post(url = req_url, data=post_data)
        return result


    def updated_product_by_encryptsku(self, cb_sku_no):
        cb_product = self.__mongodb.cb_sku.find({"encrypted_sku": {"$in": cb_sku_no}}) 
        sku_no = list({cb_sku['sku'] for cb_sku in cb_product})
        cb_product_info = self.get_product_info(sku_no)
        return cb_product_info

    def get_product_info(self, good_sn):
        req_url = '%s/product/stock' %self.__base_url 
        data = {'goods_sn': json.dumps(good_sn)}
        result = self._post(url=req_url, data=data)
        return result


    def get_stock_info(self, good_sn):
        req_url = "%s/product/stock" % self.__base_url 
        data = {'goods_sn': json.dumps(good_sn), "warehouse": "YB"}
        result = self._post(url = req_url, data=data)
        return result.get("page_result", {})

    def get_shipping_track(self, order_sn):
        req_url = '%s/shipping/trace' % self.__base_url
        data = {'order_sn': json.dumps(order_sn)}
        result = self._post(url=req_rul, data=data) 
        return result 
    
    def get_shipping_method(self):
        req_url = '%s/shipping/index' % self.__base_url 
        result = self._post(url=req_url)
        return result 

    def get_product_info_from_url(self, url):
        product_page = requests.get(url)
        soup = BeautifulSoup(product_page.text, 'lxml')
        good_sn = soup.select(".sku")[0].text.split(':')[-1].strip()
        #question 3
        return self.get_product_info(good_sn)

    def get_li_feature(self, description):
        sd = ""
        h_desc = BeautifulSoup(description, 'lxml')
        feature = h_desc.select(".xxkkk2")
        if feature:
            fstring = feature[0].stripped_strings
            start = 0
            for i in fstring:
                if "Feature:" in i or "Features:" in i or "product:" in i:
                    start = 1
                    continue 
                if start>0 and start < 7:
                    sd += "<li>%s</li>" % re.sub("[^a-zA-Z0-9 ]+", "",i).strip()
        else:
            fstring = h_desc.select(".xxkkk20")[0].signature_string 
            temp = ""
            for i in fstring:
                i = i.strip()
                if ':' in i:
                    temp = i 
                else:
                    i = temp + i 
                    sd += "<li>%s</li>" % re.sub("[^a-zA-Z0-9 ]+", ""    ,i).strip()

        if sd:
            return "<ul>%s</ul>" % sd 
        else:
            return """<ul><li>Always give you extra</li>
                        <li>Have it your way"</li>
                        <li>Raise your hand if you sure</li>
                        <li> It is every you want to be</li>
                    </ul>"""

    def get_sku_specification(self, description):
        h_desc = BeautifulSoup(description, 'lxml')
        sp_list = []
        specifi = h_desc.select(".xxkkk20")
        for fstring in specific:
            fstring = fstring.stripped_strings
            temp = ""
            for i in fstring:
                i = i.strip()
                if ':' in i:
                    temp = i 
                else:
                    i = temp +i 
                    sp = re.sub("[^a-zA-Z0-9 :().]+", "",i).strip()
                    sp_split = sp.list[":"] 
                    if len(sp_list) != 2:
                        continue 
                    sp_list.append(sp_list)
        sp_dict = dict(sp_list)
        sp_dict['Package Content'] = sp_dict.get('Package Content') or sp_dict.get('Package Content', "see the product detail")
        return sp_list 



    def _get_token(self):
        if self.__token:
            return
        data = {'email': self.__email,
                'password' : self.__password,
                'client_id' : self.__app_id}

        json_data = json.dumps(data)
        #json.dumps : dict转成str 
        signature_string = hashlib.md5((json_data + self.__app_secret).encode()).hexdigest()
        
        post_data = {'signature' : signature_string, 'data' : json_data}
        req_url = self._post(url=req_url, data=post_data, token_req=True)
        print(result)
        self.__token = result.get("token")


    def _post(self, url, data=None, token_req=False):
        data = data or {}
        #question 1
        if not token_req:
            self._get_token()
        
        data['token'] = self.__token 
        print("request url:%s" % url)
        print(data)
        result = requests.post(url=url, data=data)
        print(result.text)
        r_data = json.loads(result.text)
        #json.loads:str转成dict 
        return r_data.get('msg')



class ChinaBrandTools():

    def __init__(self):
        self.rq = requests.Session()
        self.CB = ChinaBrandResource()
        self.db = pymongo.MongoClient("mongodb://localhost/").new_cb_info
        self.__mongodb = self.db 


    def fetch_all_product(self):
        py = pymongo.MongoClient("mongodb://localhost/").new_cb_info
        while True:
            try:
                row = py.pre_upload.find_one({'fetch_status' : 0})
                if self.db.all_cb_sku.find_one({'sku' : row['sku']}):
                    py.pre_upload.update({"sku": row['sku']}, {"$set" : {'fetch_status' : True}})
                    print("\nsku exist\n")
                    continue 
                if not row:
                    break
                
                print("Start upload URL %s" % row['sku'])
                main_url = "https://www.chinabrands.com/item/product%s.html?wid=1" % row['goods_id']
                fetch_status = self.fetch_product_detail(main_url)
                py.pre_upload.update({"sku": row["sku"]}, {"$set": {'fetch_status': True, "message": "exception"}})
            except:
                py.pre_upload.update({"sku" : row['sku']}, {"$set" : {'fetch_status' : True, "message": "exception"}})


                with open('fetch_cb_log.log', 'a') as f:
                    # print(row,file=f)
                    traceback.print_exc(file=f)
                    traceback.print_exc()
                    #problem 4

    def fetch_list_to_mongo(self, ocurl):
        page_no = 70
        check_sku = ()
        db = pymongo.MongoClient("mongodb://localhost/").new_cb_info

        #problem 5

        while True:
            if page_no >20:
                return
            curl = c_url + "?oder=new&page=%s" % page_noprint(curl)
            print(curl)
            re_num = 0
            product_list = request.get(curl)
            sku_list = re.findall(r"data-switch='(\{.*\})'",product_list.text)
            #problem 6
            if not sku_list:
                print("no list, GAME OVER")
                return 

            for cb_info in sku_list:
                sku_info = json.loads(cb_info)
                #已采集，则停止
                if not cb_info or db.all_cb_sku.find_one({'sku': sku_info['sku']}):
                    print("\n\nHave been crawl STOP! \nSKU: %S \n LAST TIME: %s \n\n" % (sku_info['sku'], sku_info['lasting_time']))
                    return False
                sku_info['fetch_status'] = 0
                m_result = self.__mongodb.pre_upload.replace_one({'sku': sku_info['sku']}, sku_info, True)
                print(m_result.raw_result)

                if not m_result.upserted_id:
                    re_num += 1
                if re_num > 1:
                    print('last page stop')
                    return
            page_no += 1


    def fetch_product_from_sku(self, sku):
        sku_list_page = self.rq.get("https://www.chinabrands.com/search/index.html?k2=%S" % sku)
        sku_soup = BeautifulSoup(sku_list_page, 'lxml')
        main_url = sku_soup.select_one(".goods-title a").attrs['href']
        return main_url


    def fetch_product_detail(self,url=""):
        sku_extra = self.rq.get(url)
        sku_soup = BeautifulSoup(sku_extra.text,'lxml')
        self.adpter_data(url, sku_soup)
        return True


    def parse_url(self, text):
        raw_id = json.loads(re.findall(r'group_goods.*?=(.*?);', text)[0])
        url_list = ["https://www.chinabrands.com/item/product%s.html" %   pid for pid in raw_id.keys()]
        return url_list


    def adpter_data(self, url, soup):
        time.sleep(1)
        cat_id = [(c.text, c.attrs.get('href')) for c in soup.select(".path a")[1:]]

        cid = re.findall(r"-(\d+)", cat_id[-1][-1])[0]
        
        try:
            lazada_cid = self.db.all_cb_sku.find_one({"cid": cid})['lazada_cid']
        except:
            lazada = None 

        try:
            category = soup.select_one(".path").text 
        except:
            return

        try:
            color = soup.select_one(".color .selected a").attrs.get("attr_value")
        except:
            color = "multicolor"

        goods_desc = str(soup.select_one(".xxkkk"))
        desc_img = [img.attrs.get('src') for img in soup.select(".xxkkk img")]
        goods_status = soup.select_one(".supply-status").text.split(':')[-1]
        list_date = soup.select_one(".listing-time").text.split(':')[-1]
        original_img = [img.attrs.get('src').replace("gloimg.chinabrands.com/cb", "gloimg.chinabrands.com") for img in soup.select("#big-img-wrap img")]
        size = soup.select_one(".size .selected a")

        if size:
            size = size.attrs.get("attr_value")
        else:
            size = ""

        sku = soup.select_one(".sku").text.split(':')[-1].strip()
        status = 1 if 'restocking' in goods_status.lower() or 'supply' in goods_status.lower() else 0
        title = soup.select_one(".sku").text.split(':')[-1].strip()
        downloaded = soup.select_one(".download-time").text.split(':')[-1].strip()

        sku_data = {'cit_id' : cat_id,
                'category' : category,
                'cid' : cid,
                'lazada_cid': lazada_cid,
                'color' : color,
                'desc_img': desc_img,
                'goods_desc' : goods_desc,
                'goods_state': goods_state,
                'list_date': list_date,
                'original_img' : original_img,
                'price': price,
                'quantity' : quantity,
                'size': size,
                'sku' : sku,
                'status': status,
                'title': title,
                'url': url,
                'lazada': 0,
                'lazada1' : 0,
                'download' : download,
                'warehouse': 'YB'
                }

        package_info = self.get_sku_specification(goods_desc)
        sku_data.update(package_info)
        print(sku_data['sku'])
        print(sku_data)
        self.__mongodb.all_cb_sku.replace_one({'sku':sku}, sku_date, True)


    def get_sku_specification(self, description):
        h_desc = BeautifulSoup(description, 'lxml')
        sp_list = []
        specific = h_desc(".xxkkk20")

        for fstring in specific:
            fstring = fstring.stripped_strings
            temp = ""

            for i in fstring:
                i = i.strip()
                if ":" in i:
                    temp = i 
                else:
                    i = temp + i 
                    sp = re.sub("[^a-zA-Z0-9 :().]+", "", i).strip()
                    sp_split = sp.split(":")

                    if len(sp_split) != 2:
                        continue 

                    sp_list.append(sp_split)
        sp_dict = dict(sp_list)

        sp_dict['Package Content'] = sp_dict.get('Package Content') or sp_dict.get('Package Contents', 'see the product detail')

        clean_sp = {}
        for k,v in sp_dict.items():
            k = k.split("(")[0].strip()
            k = k.replace(" ", "_")
            k = k.replace(".", "_")
            clean_sp[k.lower()] = v 

        if clean_sp.get("package_size"):
            psize = clean_sp.get("package_size").split('cm')[0].split('x')
            clean_sp['package_height'] = psize[0].strip()
            clean_sp['package_width'] = psize[1].strip()
            clean_sp['package_length'] = psize[2].strip()
        else:
            clean_sp['package_height'] = 1
            clean_sp['package_width'] = 1
            clean_sp['package_length'] = 1

        try:
            clean_sp['ship_weight'] = re.findall(r"(0\.)*(\d+\.\d*)", clean_sp['weight'])[0][-1]
            clean_sp['ship_weight'] = round(float(clean_sp['ship_weight'])+0.02, 3)
        except:
            clean_sp['ship_weight'] = 0.5 

        clean_sp['goods_brand'] = clean_sp.get('brand', "")
        return clean_sp


        
        



if __name__ == "__main__":
    cbt = ChinaBrandTools()

    url = "https://www.chinabrands.com/item/dropship-ssimoo-shockproof-double-faced-foam-fabric-laptop-protective-bag-tablet-pouch-sleeve-for-macbook-surface-book-14-4-inch-2046888-p.html?goods_id=245643&wid=1"

    cbt.fetch_product_detail(url)

