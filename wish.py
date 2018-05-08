import requests
from temp_script import ChinaBrandResource, ChinaBrandTools
import re
import time
import json
import pymongo
import traceback
import random
import timeout_decorator
from bs4 import BeautifulSoup
import html2text
from wish_color import colors
from datetime import datetime
from configparser import ConfigParser


class Wish():
    def __init__(self):
        self.___key = b'6946b89c23d2cabbf3be1b5f63b1d41a3de990da'
        self.__url = 'https://merchant.wish.com/api/v2'
        config = ConfigParser()
        config.read('config.ini')
        self.token = dict(config._sections['WISH'])
        self.token['client_secret'] = '8a3fdde1f9304cf282a1ebafcdf42898'
        self.config = config
        self.CB = ChinaBrandResource()
        self.__mongodb = pymongo.MongoClient("mongodb://localhost:55088/"
                                             ).cb_info
        self.__color = colors
        self.__forbid_sku = ["163650601","164819701","164787801","163114002","159407701","159470704","123595401","123583503","173235502","187859601","187860403","155817701","180558905"]

    def adapt_color(self, o_color):
        colors = self.__color
        pre_color = {c: o_color.lower().find(c.lower())-len(c)
                     for c in colors if o_color.lower().find(c.lower()) != -1}
        if pre_color:
            return min(pre_color, key=pre_color.get)
        return 'Multicolor'

    def get_sku_infos(self, sku):
        db = pymongo.MongoClient("mongodb://localhost:5/").cb_info
        all_sku = db.all_cb_sku.find({"sku": {"$regex": "^%s.*" % sku[:-2]}})
        if not all_sku.count():
            cbt = ChinaBrandTools()
            main_url = cbt.fetch_cb_product_from_sku(sku)
            cbt.fetch_product_detail(main_url)
            all_sku = db.all_cb_sku.find({"sku": {"$regex": "^%s.*" % sku[:-2]}})
        if all_sku.count():
            return all_sku

    @timeout_decorator.timeout(2000)
    def create_product_from_CB(self, cb_product_info):
        """
        adpter schema: data map
        """
        cb_product_info = self.CB.get_product_info(sku)
        if not cb_product_info:
            print("URL %s is not online")
            return
        # remove skus before update again
        skus = [cb for cb in cb_product_info if int(cb['status']) == 1]
        if not skus and skus[0].get('sku') in self.__forbid_sku:
            self.complete_sku(sku, -1)
            return
        # defaultdict
        parent_sku = ""
        for inx, cb_sku in enumerate(skus):
            if cb_sku.get('quantity_new') > 0:
                cb_sku['quantity'] = int(random.randint(10, 100))
            else:
                continue
            category = cb_sku['category']
            cb_sku['category'] = category
            cb_sku['encrypted_sku'] = self.encrypt_sku(cb_sku['sku'])
            cb_sku['name'] = self.get_clean_title(cb_sku)
            cb_sku['color'] = self.adapt_color(cb_sku['color'])
            cb_sku['tags'] = category
            # self.get_tags(cb_sku['name'], category)
            cb_sku['special_price'] = 49#self.get_special_price(cb_sku['price'], self.CB.get_shipping_fee(weight=cb_sku['ship_weight']))
            cb_sku['price'] = 89# self.get_sale_price(cb_sku['special_price'])

            cb_sku['main_image'] = cb_sku['original_img'][0].replace('https',
                                                                     'http')
            extra_images = cb_sku['original_img'][1:] + cb_sku['desc_img']
            cb_sku['extra_images'] = [img.replace('https', 'http')
                                      for img in extra_images]
            cb_sku['parent_sku'] = parent_sku
            if inx == 0:
                parent_sku = cb_sku['encrypted_sku']
                cb_sku['parent_sku'] = parent_sku
                cb_sku['desc'] = self.get_clean_desc(cb_sku['goods_desc'])
                cb_sku['wish_uploaded'] = self.create_product(**cb_sku) or False
            else:
                cb_sku['wish_uploaded'] = self.create_variant(**cb_sku) or False
            # if have been upload to lazada save it.
            self.complete_sku(cb_sku['sku'], -1)

    def get_clean_desc(self, desc):
        text = BeautifulSoup(desc, "lxml")
        [x.extract() for x in text.findAll('img')]
        return html2text.html2text(str(text)).replace("**", "")

    def get_sale_price(self, origin_price):
        x = random.randint(2, 8)/10
        return round(origin_price/x, 2)

    def get_special_price(self, origin_price, ship_fee):
        origin_price = float(origin_price)
        if origin_price <= 5:
                x = 1.4
        elif(origin_price > 5 and origin_price <= 10):
                x = 2.6
        elif(origin_price > 10 and origin_price <= 20):
                x = 5
        elif(origin_price > 20):
            return round((origin_price*1.8 + 1.2*ship_fee)-1)

        return round((origin_price*1.2 + 1.2*ship_fee)+x)

    def get_suggest_tags(self, kw=''):
        c = requests.post('https://merchant.wish.com/api/contest-tag/search', data={'q': kw})
        result = json.loads(c.text)
        tags = result.get('data', {}).get('tags')
        if not tags:
            return [kw,]
        l_tags = [t['tag'] for t in tags]
        l_tags.sort(key=len)
        return l_tags

    def get_tags(self, title="", category=""):
        c_str = category.lower()
        lc_str = c_str.split(">")
        l_tags = lc_str[1:]

        lendest_c = lc_str[-1].split('&')
        for endest_c in lendest_c:
            endest_c = endest_c.strip()
            if 'women' in c_str or 'woman' in c_str:
                l_tags.extend(self.get_suggest_tags('womens ' + endest_c)[:3])

            elif 'men' in c_str or 'man' in c_str:
                l_tags.extend(self.get_suggest_tags('mens ' + endest_c)[:3])

            else:
                l_tags.extend(self.get_suggest_tags(endest_c)[:3])

        l_tags.append(lc_str[-2].strip())
        l_tags.append(self.get_promotion_word() + lc_str[-1])
        l_tags.append(" ".join(title.split(" ")[-8:]).strip())
        l_tags.extend(self.get_suggest_tags(" ".join(title.split("for")[0].split(" ")[-3:]).strip())[:2])
        return ",".join(l_tags)

    def get_clean_title(self, cb_sku):
        spec = self.CB.get_sku_specification(cb_sku['goods_desc'])
        re.sub("%s |%s " % (cb_sku.get('goods_brand'), spec.get('model')),
                                                "", cb_sku['title'], flags=re.I)
        clean_title = self.get_promotion_word() + \
            cb_sku['category'].split('>')[-1].strip() + " "  + cb_sku['title']
        clean_title = re.sub(' +', ' ', clean_title)
        return clean_title.strip().lower().title()

    def get_promotion_word(self):
        words = ["Fashion",
                 "New",
                 "Save",
                 "More",
                 "Luxury",
                 "The",
                 "High Quality",
                 "Quality",
                 "Sale",
                 "Hot Sale",
                 "Awesome",
                 "Gift",
                 "Nice",
                 "New Arrival",
                 "professional",
                 "Beautiful",
                 "cheap",
                 "discount",
                 "outlet",
                 "wonders"]
        return random.choice(words) + " "

    def complete_sku(self, cb_sku, status):
        if isinstance(cb_sku, str):
            cb_sku = [cb_sku, ]
        self.__mongodb.all_cb_sku.update_many({'sku': {"$in": cb_sku}},
                                              {"$set": {"wish": status}}, True)

    def remove_product(self, sku=None):
        action = '/product/disable'
        data = {
            "parent_sku": sku,
        }
        result = self._post(action, data=data)
        print(result)

    def update_tags(self, sku=None):
        if not sku:
            return
        print(sku)
        db = pymongo.MongoClient("mongodb://localhost:27017/").cb_info
        sku_info = db.all_cb_sku.find_one({"sku": sku.split('-')[-1],
                                           "status": 1})
        if not sku_info:
            self.remove_product(sku=sku)
            print("no reltive product, remove")
            return
        l_tags = db.wish_tags.find_one({"cid": sku_info['cid']})
        if not l_tags:
            print("no reltive tags")
            return
        tags = random.choice(l_tags['tags'])
        print(tags)
        data = {
            "parent_sku": sku,
            "tags": tags
        }
        print(self.update_product(**data))

    def update_product(self, **kwargs):
        # update need kwargs key equal wish api keys
        action = '/product/update'
        result = self._post(action, data=kwargs)
        return bool(result)

    def create_product(self, **kwargs):
        action = '/product/add'
        data = {
               "name": kwargs['name'],
               "parent_sku": kwargs['parent_sku'],
               "description": kwargs['desc'],
               "tags": kwargs['tags'],
               "sku": kwargs['encrypted_sku'],
               "inventory": kwargs['quantity'],
               "price": kwargs['special_price'] + 3,
               "shipping": 5,
               "color": kwargs['color'],
               "size": kwargs['size'],
               "msrp": kwargs['price']+10,
               "shipping_time": '5-25',
               "main_image": kwargs['main_image'],
               "brand": kwargs['goods_brand'],
               "extra_images": "|".join(kwargs['extra_images'][:19])
        }
        result = self._post(action, data=data)
        return bool(result)

    def create_variant(self, **kwargs):
        action = '/variant/add'
        data = {
                "parent_sku": kwargs['parent_sku'],
                "sku": kwargs['encrypted_sku'],
                "inventory": kwargs['quantity'],
                "price": kwargs['special_price'],
                "shipping": 1,
                "color": kwargs['color'],
                "size": kwargs['size'],
                "msrp": kwargs['price'],
                "shipping_time": '10-25',
                "main_image": kwargs['main_image']
        }
        result = self._post(action, data=data)
        return bool(result)

    def encrypt_sku(self, sku):
        return 'COM01-' + str(sku)

    def remove_empty_elements(self, doc):
        for element in doc.xpath('//*[not(node())]'):
            element.getparent().remove(element)

    def get_access_token(self):
        data = self.token
        if datetime.now() > datetime.fromtimestamp(int(data['expiry_time'])):
            data = self.refresh_token()
        return data.get('access_token')

    def refresh_token(self):
        action = '/oauth/refresh_token'
        url = self.__url + action
        data = {k: self.token.get(k)
                for k in ['refresh_token', 'client_secret', 'client_id']}
        data['grant_type'] = 'refresh_token'
        result = requests.post(url, data=data)
        result = json.loads(result.text)
        print(result)
        new_token = result['data']
        new_token.pop("reason", None)
        config = ConfigParser()
        config["WISH"] = new_token
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        return new_token

    def get_pending_orders(self):
        action = '/order/get-fulfill'
        result = self._post(action)
        return result['data']

    def put_order(self, supply, ship_method = None):
        ship_method = ship_method or 'WISHDLE'
        orders = self.get_pending_orders()
        if not orders:
            return
        all_order_result = {}
        for o in orders:
            o = o['Order']
            oadpter = {}
            oadpter['user_order_sn'] = 'rolandarts' + str(o['order_id'])
            oadpter['country'] = o['ShippingDetail']['country']
            oadpter['firstname'] = o['ShippingDetail']['name']
            oadpter['lastname'] = ''
            oadpter['shipping_method'] = ship_method
            oadpter['addressline1'] = o['ShippingDetail']['street_address1']
            oadpter['city'] = o['ShippingDetail']['city']
            oadpter['zip'] = o['ShippingDetail']['zipcode']

            oadpter['goods_info'] = []
            goods_sn = o['sku'].split('-')[-1]
            if '187860403' in goods_sn:
                goods_sn = "187860404"

            if '181874902' in goods_sn:
                goods_sn = "181874901"

            if '17835870' in goods_sn:
                goods_sn = '178358701'

            if '20216200' in goods_sn:
                goods_sn = '202162005'

            oadpter['goods_info'].append({'goods_sn': str(goods_sn),
                                              'goods_number': o['quantity']})
            print(oadpter)
            result = supply.put_order(**oadpter)
            print(result)
            all_order_result.update(result)
        return all_order_result

    def _post(self, action, extra_param=None, data=None):
        data = data or {}
        # remove empty values
        data = {k: v for k, v in data.items() if v}
        url = self.__url + action
        parameters = {}
        if extra_param:
            parameters.update(extra_param)
        data['access_token'] = self.get_access_token()
        data['format'] = 'json'
        result = requests.post(url, params=parameters, data=data)
        # print(result.text)
        result = json.loads(result.text)
        self.__mongodb.wish_result.insert(result)
        time.sleep(0.2)
        print(url)
        return result


if __name__ == "__main__":
    l = Wish()
    py = pymongo.MongoClient("mongodb://localhost:55088/").cb_info
    while True:
        sku_info = py.all_cb_sku.find_one({"cat_id.0.0": "Beauty & Health",
                                           "status": 1, "wish": None})
        if not sku_info:
            break
        sku = sku_info.get('sku')

        all_sku = py.all_cb_sku.find({"sku": {"$regex": "^%s.*" % sku[:-2]},
                                      'status': 1,"wish":None, "quantity_new": {"$gt":2}})
        if not all_sku:
            continue
        try:
            all_sku = list(all_sku)
            if not all_sku:
                l.complete_sku(sku, -11)
                print("no enough stock")
                continue
            skus = [sku['sku'] for sku in all_sku]
            print("Start upload URL %s" % str(skus))

            l.complete_sku(skus, -1)
            l.create_product_from_CB(all_sku)
        except:
            with open('wish_log.log', 'a') as f:
                # print("Error URL: %s-%s" % (row['cid'], row['sku']), file=f)
                traceback.print_exc(file=f)
                traceback.print_exc()
            print("Error URL %s" % str(skus))
