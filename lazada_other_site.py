from lazada import Lazada
from lxml import etree
import html
import traceback
from lazada_fee import get_sale_price, get_special_price
import arrow
import random
from temp_script import ChinaBrandResource
import time
import pymongo
import re
import requests
import json

class LazadaOtherSite(Lazada):
    def update_title(self, list_product):
        for cb_product in list_product:
            pinfo = {}
            # pinfo['name'] = cb_product['Attributes']['name'].replace("&", " ")
            #pinfo['name'] = self.get_trans_name(pinfo['name'], "th")
            short_desc = cb_product['Attributes']['short_description']

            if '\\u003C' in short_desc:
                short_desc = short_desc.replace("\\u003C", "<")
                short_desc = short_desc.replace("\\u003E", ">")

            short_desc = short_desc.replace("</ul>", "<li>This product is eligible for Free Delivery</li><li>Buy More to Save More. Happy Shopping!</li></ul>")

            pinfo['short_desc'] = html.escape(short_desc)
            lz_description = cb_product['Attributes']['description']
            lz_description = lz_description.replace("lazada_MY112E5.gif", "lazada_MY112E5.png")

            pinfo['description'] = html.escape(lz_description)
            product_schema = etree.XML("""<Request><Product>
                    <Attributes>
                        <!--<short_description>{short_desc}</short_description>
                        <description>{description}</description>
                        <description_en>{description}</description_en>-->
                    </Attributes>
                    <Skus>
                    </Skus>
                </Product>

            </Request>""".format(**pinfo))
            for sinfo in cb_product['Skus']:
                print(sinfo['SellerSku'])
                product_sku = etree.XML("""<Sku>
                    <SellerSku>{SellerSku}</SellerSku>
                    <active>true</active>
                </Sku>""".format(**sinfo))
                product_schema.xpath("//Skus")[0].append(product_sku)
            result = self._post("UpdateProduct",
                                        data=etree.tostring(product_schema, encoding='utf-8'))

    def get_trans_name(self, name, target="zh_CN"):
        name = name.replace("- Intl", "").strip()
        name = name.replace(" ", ",", 3)
        print(name)
        url = "https://translation.googleapis.com/language/translate/v2?key=AIzaSyBgivFlsgQIUTSC2Q8-YF1yVqdRZYCdZsw"
        data = {'format': 'text',
                 'q': name,
                 'source': 'en',
                 'format': 'html',
                 'target': target}

        c = requests.post(url, data=data)
        cnr = json.loads(c.text)
        try:
            name = cnr['data']['translations'][0]['translatedText']
        except:
            pass
        return (name.replace(",", " ")  + " - Intl")

    def get_clean_title(self, clean_title, cid):
        cname = self.get_category_name(cid)
        if cname:
            cname = cname.replace("&", ' ')
            cname = cname.split(" / ")
            clean_title = cname[0].strip() + " " \
                + cname[-1].strip().replace('?', '') + " " + clean_title
            clean_title = re.sub(' +', ' ', clean_title).lower().title()
        return clean_title.replace("&", " ")[:255]

    def active_product(self, list_product):
        accountId = self.get_account_id()
        rm_sku = []
        for cb_product in list_product:
            # time.sleep(1)
            pinfo = {}
            try:
                product_schema = etree.XML("""<Request><Product>
                        <Skus>
                        </Skus>
                    </Product>
                </Request>""".format(**pinfo))
                for sinfo in cb_product['Skus']:
                    self.remove_elements_by_tag(product_schema, "Sku")
                    print(sinfo['Status'])
                    product_sku = etree.XML("<Sku> <SellerSku>" + sinfo['SellerSku']+
                                                "</SellerSku><active>true</active></Sku>")
                    product_schema.xpath("//Skus")[0].append(product_sku)
                    #print(etree.tostring(product_schema))

                    result = self._post("UpdateProduct",
                                    data=etree.tostring(product_schema))
            except:
                with open('%s.log' % accountId , 'a') as f:
                    print(sinfo['SellerSku'], file = f)
                    traceback.print_exc(file=f)
                    traceback.print_exc()

    def update_product(self, list_product, pre_remove,disable=False, remove=False):
        accountId = self.get_account_id()
        if remove:
            for cb_product in list_product:
                for sinfo in cb_product['Skus']:
                    pre_remove.append(sinfo['SellerSku'])
                    if len(pre_remove) >= 10:
                       self.remove_product(pre_remove)
                       pre_remove = []
                    continue
            return


        for cb_product in list_product:
            # time.sleep(1)
            pinfo = {}
            lz_description = cb_product['Attributes']['description'].replace("http://s.chaotiinfo.com/lazada_MY112E5.gif",
                    "http://45.32.121.94/lazada_MY112E5.png")
            short_desc = cb_product['Attributes']['short_description']

            if '\\u003C' in short_desc:
                short_desc = short_desc.replace("\\u003C", "<")
                short_desc = short_desc.replace("\\u003E", ">")

            short_desc = short_desc.replace("</ul>", "<li>This product is eligible for Free Delivery</li><li>Buy More to Save More. Happy Shopping!</li></ul>")

            pinfo['short_desc'] = html.escape(short_desc)
            pinfo['name'] = cb_product['Attributes']['name'].replace("&", " ")

            # # replace desc image to lazada
            pinfo['description'] = html.escape(lz_description)
            try:
                product_schema = etree.XML("""<Request><Product>
                         <Attributes>
                           <name>{name}</name>
                    	   <short_description>{short_desc}</short_description>
                    	   <description>{description}</description>
                    	   <description_en>{description}</description_en>
                         </Attributes>
                        <Skus>
                       </Skus>
                    </Product>
                </Request>""".format(**pinfo))
                for sinfo in cb_product['Skus']:
                    self.remove_elements_by_tag(product_schema, "Sku")
                    # if "CM00" not in sinfo['SellerSku']:
                    #     print(sinfo['SellerSku'])
                    #     print("no need back")
                    #     continue
                    if disable:
                        print(sinfo['Status'])
                        product_sku = etree.XML("<Sku> <SellerSku>" + sinfo['SellerSku']+
                                                "</SellerSku><active>false</active></Sku>")
                    else:
                        product_sku, cb_sku = self.get_price_quantity(sinfo)

                    if not product_sku:
                        continue
                    if "CM02" in cb_sku['encrypted_sku']:
                        db = pymongo.MongoClient("mongodb://mongo.server:55088/").pf_info
                        pfh = db.lazada_sku.find_one({"encrypted_sku": cb_sku['encrypted_sku']})
                        cid = pfh.get('category', 0)
                        cname = pfh.get('title') or pfh.get('name')
                        new_name = self.get_clean_title(cname, cid)
                        new_name = self.get_trans_name(new_name, "id")
                        product_schema.xpath("//name")[0].text = new_name
                    product_schema.xpath("//Skus")[0].append(product_sku)
                    # print(etree.tostring(product_schema))

                    result = self._post("UpdateProduct",
                                    data=etree.tostring(product_schema))
            except:
                with open('%s.log' % accountId , 'a') as f:
                    print(sinfo['SellerSku'], file = f)
                    traceback.print_exc(file=f)
                    traceback.print_exc()

    def adjust_price_quantity(self, list_product):
        for cb_product in list_product:
            # time.sleep(1)
            for sinfo in cb_product['Skus']:
                encrypted_sku = sinfo['SellerSku']
                print("special sku: %s" % encrypted_sku)
                if "RA06" not in encrypted_sku or "CM08" not in encrypted_sku:
                    print("no need  adjust")
                    return
                cb_sku = {}
                cb_sku['SellerSku'] = encrypted_sku
                cb_sku['special_price'] = round(sinfo['special_price']*1.5, 2)
                cb_sku['price'] = get_sale_price(cb_sku['special_price']*1.8, 0.6)

                cb_sku['quantity'] = random.randrange(10, 666)
                self.adjust_price(cb_sku)


    def get_price_quantity(self, sinfo, cucode=None, ajax=False):
        encrypted_sku = sinfo['SellerSku']
        country = cucode or self.get_account_id()[0:2]
        print("special sku: %s" % encrypted_sku)
        cb_sku = {}
        mongo = pymongo.MongoClient("mongodb://mongo.server:55088/")
        if "RA01" in encrypted_sku or "CM01" in encrypted_sku:
            sku = encrypted_sku.split('-')[-1]
            cb_sku = mongo.cb_info.all_cb_sku.find_one({'sku': sku})
            level='CB'
        elif "CM02" in encrypted_sku:
            sku = encrypted_sku.replace("CM02-","")
            cb_sku = mongo.pf_info.pf_sku.find_one({"SKU":sku})
            try:
                cb_sku['price'] = round((float(cb_sku['CostPrice']) + 5)/7)
                cb_sku['ship_weight'] = round((float(cb_sku['Weight']) + 10)/1000, 2)
                level='pfh'
            except:
                self.remove_product([encrypted_sku,])
                print("Remove it")
                return False
        elif "CM00" in encrypted_sku:
            cb_sku = mongo.lazada.findOne({"associateSku":{"$regex": encrypted_sku+"*"}})

            cb_sku['price'] = sinfo['special_price']
            cb_sku['ship_weight'] = 0.1
            level= 'CM00'

        if not cb_sku.get('price'):
            print('have offline %s' % cb_sku['sku'])
            # self.remove_product([encrypted_sku])
            return False

        cb_sku['encrypted_sku'] = encrypted_sku
        cb_sku['special_price'] = get_special_price(cb_sku['price'],
                                                    cb_sku['ship_weight'],
                                                    country = country, level=level)
        print(encrypted_sku, cb_sku['price'], cb_sku['ship_weight'], cb_sku['special_price'])

        cb_sku['price'] = get_sale_price(cb_sku['special_price'])
        start_date = arrow.now()
        cb_sku['special_from_date'] = start_date.strftime("%Y-%m-%d")
        cb_sku['special_to_date'] = start_date.replace(days=+365
                                                       ).strftime("%Y-%m-%d")
        # quantity
        cb_sku['quantity'] = random.randrange(30, 666)

        # use for requests
        if ajax:
            return cb_sku

        product_sku = etree.XML("""<Sku>
                <SellerSku>{encrypted_sku}</SellerSku>
                <quantity>{quantity}</quantity>
                <price>{price}</price>
                <special_price>{special_price}</special_price>
                <special_from_date>{special_from_date}</special_from_date>
                <special_to_date>{special_to_date}</special_to_date>
            </Sku>""".format(**cb_sku))

        return product_sku, cb_sku

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    #-db DATABSE -u USERNAME -p PASSWORD -size 20
    parser.add_argument("-s", "--site", help="lazada site number")

    args = parser.parse_args()

    print( "now process site:{}\n\n ".format(args.site))
    site_info = [{
        "api_key": '6946b89c23d2cabbf3be1b5f63b1d41a3de990da',
        "user_id": "zchv@msn.com",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "accountId": "MY10WA4"
    }, {
        "api_key": b'i50qSobssxxZEl1vyjE2dbKzd5XQ4xfE_9MvJLl_Vuvm8URak4CoHH6z',
        "user_id": "ct@lazada.ph",
        "url": "https://api.sellercenter.%s/" % "lazada.com.ph",
        "accountId": "PH10KNV"},
    {
        "api_key": b'TrwkupHsatgLSJ29-v0GyQm_XFif-nzQ6o9K1HqU5M5RQGq4ZPTjdG7m',
        "user_id": "ct@lazada.sg",
        "url": "https://api.sellercenter.%s/" % "lazada.sg",
        "accountId": "SG10K9L"
    }, {
        "api_key": b'faiiWFTyeNygj32Yv5e1YKWhASk4ce1Y9PyWsSPEpd4s5z_NgUzwwmdr',
        "user_id": "ct@lazada.th",
        "url": "https://api.sellercenter.%s/" % "lazada.co.th",
        "accountId": "TH10XO0"
    }, {
        "api_key": b'g7km1MXol8AtXMwRBNikP0fa8VROYWR_h6FNp_PZxFpyVzHfWYcfgv_D',
        "user_id": "ct@lazada.id",
        "url": "https://api.sellercenter.%s/" % "lazada.co.id",
        "accountId": "ID11MKJ"
    }, {"api_key": 'U_Oobajpv6G6B4wIgrq349_ARwJ6Z9lFSHZqm705nEiDv6fP-fLSgkV2',
        "user_id": "citi@ctdata.my",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "name": "citimall",
        "accountId": "MY112E5"
    }, {
        "api_key": b'QGz5Smumqy3bxUZzoWf-OIjTH_eo_q_qbpOT6Cjer2TLdVm-ARViZD3g',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.com.ph",
        "accountId": "PH10OU4"},
    {
        "api_key": b'N5bfnEcFk6GCgiZRIPJi38jlqHSxYbocHgWKFcMM-04bhg5TXQADsADF',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.sg",
        "accountId": "SG10OCO"
    }, {
        "api_key": b'54oyaJGpM2Z8CIUsu4JTvm3OLETUjRMQbZ_JOy-bxkOQKl0h5Rn1CPBy',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.co.th",
        "accountId": "TH1157F"
    }, {
        "api_key": b'EzIAOY-49evRsMxzP71d-2yAWkCcp1c0m7t75DGF0FV1iWxqzh4OR-2o',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.co.id",
        "accountId": "ID120DF"
    }]
    site = site_info[int(args.site)]
    l = LazadaOtherSite(**site)
    offset = 0
    pre_remove = []
    while True:
        try:
            update_before = arrow.Arrow(2017, 8, 27).floor('hour')
            print(site)
            update_before = arrow.now().floor('hour')
            product = l.get_product(offset=offset, limit=100,
                                    update_before=update_before,
                                    status='all',
                                    # OrderBy='sku',
                                    CreatedAfter = "2017-07-01T10:00:00+08:00"
                                    # CreatedBefore = "2017-04-22T10:00:00+08:00"
                                    )
            product_info = product['Products']
            print(len(product_info))
            l.get_mongodb().all_lazada_sku.insert_many(product_info,
                                                       ordered=False)
            continue
            # l.update_product(product_info, pre_remove, remove=True)
            l.adjust_price_quantity(product_info)
            # l.update_title(product_info)
            if len(product_info) <30 and offset == 0:
                break
            if len(product_info) < 20 and offset > 0:
                offset = 0
                continue
            offset += 100
        except:
            with open('%s.log' % site['accountId'], 'a') as f:
                traceback.print_exc(file=f)
                traceback.print_exc()
            break
