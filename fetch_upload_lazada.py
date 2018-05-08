#!/usr/bin/python
# coding=utf8
"""
# Author: Bill Zhang
# Created Time : 2017-04-11 10:25:47

# File Name: fetch_upload_lazada.py
# Description:

"""

from bs4 import BeautifulSoup
import requests
from lazada import Lazada
import arrow
import pymongo
import re
import json
import random
import html
from lxml import etree
import traceback
import time


class LL(Lazada):
    def __init__(self, **kwargs):
        self.db = pymongo.MongoClient("mongodb://mongo.fetch:27017/").lazada_info
        self.product_info = {}
        self.store_name = "Rolandarts"
        super(LL, self).__init__(**kwargs)

    def clean_name(self, pname):
        product_info = self.product_info
        name = pname.lower()
        name = name.replace(product_info['brand'].lower(), "")
        name = name.replace(product_info['store_name'].lower(), "")
        category = product_info["category"].split(">")
        if len(category) == 1:
            name = category[0] + ' ' + name
        else:
            name = category[0] + category[-1] + ' ' + name
        return name.title().replace("&", " ").replace("\n", "  ").replace("  ", " ")

    def _remove_attrs(self, soup):
        for tag in soup.findAll(True):
            tag.attrs = None
        return soup

    def get_color(self, o_color):
        name = o_color.lower()
        s = ""
        c = self.adapt_color(name)
        if c.lower() == 'silver':
            s = self.adapt_color(name.replace(c.lower(), ''))
        if s and s != 'Multicolor':
            return s
        return c

    def get_skus(self, sku_info):
        product_info = self.product_info
        sku_info = list(sku_info["priceStore"].values())[0]
        options = sku_info['options']
        skus = {}
        cattrs = self.get_mandatory_attributes(product_info['category_id'])
        s_prices = sku_info["prices"]
        if options and cattrs:
            option = list(options.values())[0]
            print(options)
            print(cattrs)
            for k, v in option.items():
                attr_opt = re.sub(r"opt-(.*)item.*", "\\1", k, flags=re.I) 
                if attr_opt == '-':
                    continue
                skey = list(v["skus"].keys())[0]
                extra = {}
                skus[skey] = extra
                for ck, cv in cattrs.items():
                    ncv = [s.replace(' ', '-').replace(':', '-') for s in cv]
                    try:
                        c_index = ncv.index(attr_opt)
                        extra[ck] = cv[c_index]
                    except:
                        if 'One Size' in cv:
                            extra[ck] = 'One Size'
                        elif 'Int:One Size' in cv:
                            extra[ck] = 'Int:One Size'
                        elif 'Int: One Size' in cv:
                            extra[ck] = 'Int: One Size'
                        else:
                            extra[ck] = 'Not Specified'

            # skus now like {'OE702FAAA7RM79ANMY-16502631': {'size': 'EU:34'},
            # 'HE569FAAAA1NY0ANMY-21376013': {'size': 'EU:29'}}

            # add price #
            i = 0
            for sn, attr in skus.items():
                price = s_prices[sn]
                price = price['final_price']
                if price < 20:
                    price *= 1.8
                else:
                    price *= 1.5
                attr['special_price'] = round(price, 2)
                attr['price'] = round(price/0.32, 2)
                attr['special_from_date'] = '2017-06-10'
                attr['special_to_date'] = '2018-12-23'
                attr['SellerSku'] = "RA06-%s" % self.encrypted_sku(sn.split('-')[-1])
                i += 1
        if not skus:
            price = list(s_prices.values())[0]
            attr = {}
            skus['single'] = attr
            price = price['final_price']
            if price < 20:
                price *= 1.8
            else:
                price *= 1.5
            attr['special_price'] = round(price, 2)
            attr['price'] = round(price/0.32, 2)
            attr['special_from_date'] = '2017-06-10'
            attr['special_to_date'] = '2018-12-23'
            attr['SellerSku'] = "RA06-%s" % self.encrypted_sku(list(s_prices.keys())[0].split("-")[-1])
            extra = {}
            for ck, cv in cattrs.items():
                if 'One Size' in cv:
                    extra[ck] = 'One Size'
                elif 'Int:One Size' in cv:
                    extra[ck] = 'Int:One Size'
                elif 'Int: One Size' in cv:
                    extra[ck] = 'Int: One Size'
                else:
                    extra[ck] = 'Not Specified'

            attr.update(extra)
        return skus

    def get_key_words(self, pinfo):
        cname = pinfo["category"].replace("&", "and")
        cname = cname.split(" > ")
        cname.append(self.store_name)
        return json.dumps(cname)

    def encrypted_sku(self, sku):
        return "".join([chr(ord(s)+20) for s in sku])

    def get_true_cid(self, cid):
        cid = int(cid)
        if cid <= 4830:
            pass
        elif cid == 5172:
            cid -= 1
        elif cid > 5172 and cid < 10170:
            cid -= 2
        elif cid > 10168 and cid < 10914:
            cid -= 3
        elif cid >= 10914:
            cid -= 5
        return str(cid)

    def upload_lazada(self, url=None):
        self.product_info = {}
        if not url: 
            pinfo = self.db.data_my.find_one_and_update({"status": 0}, {"$set": {"status": 10}})
            if pinfo['seller_name'] in ["niceEshop", "Leegoal"]:
                print("upload  later")
                return
            url = pinfo['url']
        print('START fetch %s' % url)
        # if self.get_mongodb().lazada.find_one({"origin_url": url, "lazada":True}):
        #     print("have uploaded")
        #     return

        time.sleep(1)
        result = requests.get(url)
        soup = BeautifulSoup(result.text, 'lxml')
        sku_info = re.findall(r"var store =(.*?);</script>", result.text, re.I)
        sku_info = json.loads(sku_info[0].replace(" || {}",""))
        # pinfo
        pinfo = re.findall(r"application.*?({.*?)</script>", result.text)
        pinfo = json.loads(pinfo[0])

        product_info = self.product_info

        product_info['origin_url'] = url
        product_info['category'] = pinfo["category"]
        # get cid
        cid = sku_info[
                "richRelevance"]["data"]["categoryId"]

        product_info["category_id"] = self.get_true_cid(cid)
        product_info['brand'] = pinfo["brand"]["name"]
        product_info['store_name'] = soup.select_one(
                ".basic-info__name").text.strip()
        pinfo['name'] = soup.select_one("#prod_title").text.strip()
        product_info['name'] = self.clean_name(pinfo['name'])

        product_info["description"] = re.sub(product_info['store_name'], self.store_name, pinfo["description"], re.I)

        product_info['images'] = [
                "http://my-live.slatic.net/original/"
                + img.attrs['src'].split('-')[-2]+".jpg"
                for img in soup.select(".itm-img")]
        if len(product_info['images']) > 1:
            product_info['images'].pop()

        product_info['package_length'] = pinfo.get(
                "depth", {}).get("value", '15')
        product_info['package_height'] = pinfo.get(
                "height", {}).get("value", '3')
        product_info['package_width'] = pinfo.get(
                "width", {}).get("value", '10')
        product_info['package_content'] = soup.select_one(
                ".inbox__item").text.strip().replace("\xa0", " ")
        product_info['package_content'] = product_info['package_content'].replace(">", "").replace("<", "")
        short_desc = str(self._remove_attrs(
            soup.select_one(".prod_details")).ul)
        if '\\u003C' in short_desc:
            short_desc = short_desc.replace("\\u003C", "<")
            short_desc = short_desc.replace("\\u003E", ">")
        if BeautifulSoup(short_desc, 'lxml').ul.ul:
            short_desc = str(BeautifulSoup(short_desc, 'lxml').ul.ul)

        product_info['short_description'] = short_desc

        product_info['ship_weight'] = pinfo.get("weight", {}).get("value", 300)
        product_info['quantity'] = random.randint(35, 999)
        product_info['color'] = self.get_color(product_info['name'])
        product_info["skus"] = self.get_skus(sku_info)
        product_info['associateSku'] = list(
                product_info["skus"].values())[0]["SellerSku"]
        res = self.adapt_product()
        if res:
            self.db.data_my.update_one({"url": url}, {"$set": {"status": 1}})
            product_info['lazada'] = True
        self.save_data(product_info)

    def save_data(self, data):
        self.get_mongodb().lazada.update({"associateSku": data['associateSku']}, {"$set": data}, True)

    def adapt_product(self):
        product_info = self.product_info
        product_info["short_description"] = html.escape(
                product_info['short_description'])
        product_info["description"] = html.escape(product_info['description'])
        product_info['keywords'] = self.get_key_words(product_info)
        product_schema = etree.XML("""<Request>
            <Product>
                <PrimaryCategory>{category_id}</PrimaryCategory>
                <SPUId></SPUId>
                <Attributes>
                    <name>{name}</name>
                    <name_ms>{name}</name_ms>
                    <color_family>{color}</color_family>
                    <short_description>{short_description}</short_description>
                    <brand>OEM</brand>
                    <model>Rolandarts{associateSku}</model>
                    <warranty_type>No Warranty</warranty_type>
                    <description>{description}</description>
                </Attributes>
                <Skus id="skus">
                </Skus>
            </Product>
        </Request>
        """.format(**product_info))
        # sku add
        # package content
        for sku_info in product_info['skus'].values():
            product_sku = etree.XML("""<Sku>
                    <tax_class>default</tax_class>
                    <quantity>{quantity}</quantity>
                    <color_family>{color}</color_family>
                    <model>RA{associateSku}</model>
                    <package_length>{package_length}</package_length>
                    <package_height>{package_height}</package_height>
                    <package_weight>{ship_weight}</package_weight>
                    <package_width>{package_width}</package_width>
                    <std_search_keywords>{keywords}</std_search_keywords>
                    <package_content>{package_content}</package_content>
                    <Images>
                    </Images>
                    <Image></Image>
                </Sku>""".format(**product_info))
            for tag, tv in sku_info.items():
                new_tag = etree.Element(tag)
                new_tag.text = str(tv)
                attr_type = self.check_attrs_type(
                        product_info['category_id'], tag)
                if attr_type == 'sku':
                    product_sku.xpath("//Sku")[0].append(new_tag)
                else:
                    product_schema.xpath("//Attributes")[0].append(new_tag)

            # image
            for image_src in product_info["images"]:
                e_image_src = etree.Element("Image")
                e_image_src.text = image_src
                product_sku.find("Images").append(e_image_src)
            product_schema.xpath("//Skus")[0].append(product_sku)

        # print(etree.tostring(product_schema))
        result = self._post("CreateProduct",
                           data=etree.tostring(product_schema))
        if result:
            return True


if __name__ == "__main__":
    l = LL()
    while True:
        try:
            l.upload_lazada()
        except:
            with open('fetch_lazada.log', 'a') as f:
                traceback.print_exc(file=f)
                traceback.print_exc()
