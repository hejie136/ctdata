# -*- coding: utf-8 -*
from hashlib import sha256
from hmac import HMAC
import arrow 
#time module
from urllib.parse import urlencode
import requests
from lxml import etree
import json
#js object notation
import html
import pdb
try:
    from .temp_script import ChinaBrandResource
    from .lazada_fee import get_sale_price, get_special_price
    from .lazada_brand import lazada_brand
    from .lazada_category_attrs import get_extra_attrs
    from .lazada_category import lazada_category
except:
    from temp_script import ChinaBrandResource
    from lazada_fee import get_sale_price, get_special_price
    from lazada_brand import lazada_brand
    from lazada_category_attrs import get_extra_attrs
    from lazada_category import lazada_category


import re
import pymongo
import traceback
import random
import collections
import timeout_decorator
from bs4 import BeautifulSoup
import time
import functools
import base64
from urllib.parse import quote_plus


class Lazada():
    def __init__(self, **kwargs):
        self.__api_key = kwargs.get(
            'api_key', '6946b89c23d2cabbf3be1b5f63b1d41a3de990da').encode('utf-8')
        self.__user_id = kwargs.get('user_id', 'zchv@msn.com')
        self.__url = kwargs.get('url',
                                'https://api.sellercenter.lazada.com.my/')
        self.__accountId = kwargs.get('accountId', 'MY10WA4')
        self.store_name = kwargs.get('name', 'rolandarts')
        self.sku_pre = kwargs.get('sku_pre', 'LA01-')
        password = quote_plus("37H*#2&@Jh9KVS")
        self.__mongodb = pymongo.MongoClient("mongodb://localhost/").cb_info
        # self.__mongodb = pymongo.MongoClient('mongodb://ctdata_F2&J#(Hs5:' #                                      + password
        #                                      + '@mongo-server1:55188/?authSource=admin').cb_info

        self.CB = kwargs.get('supply', ChinaBrandResource())
        self.__color = ['Black', 'Beige', 'Blue', 'Brown', 'Gold', 'Green',
                        'Grey', 'Multicolor', 'Olive', 'Orange', 'Pink',
                        'Purple', 'Red', 'Silver', 'Turquoise', 'Violet',
                        'White', 'Yellow', 'Clear', 'Apricot', 'Aqua',
                        'Avocado', 'Blueberry', 'Blush Pink', 'Bronze',
                        'Charcoal', 'Cherry', 'Chestnut', 'Chili Red',
                        'Chocolate', 'Cinnamon', 'Coffee', 'Cream',
                        'Floral', 'Galaxy', 'Hotpink', 'Ivory', 'Jade',
                        'Khaki', 'Lavender', 'Magenta', 'Mahogany', 'Mango',
                        'Maroon', 'Neon', 'Tan', 'Watermelon red', 'Lake Blue',
                        'Lemon Yellow', 'Army Green', 'Rose', 'Dark blue',
                        'Camel', 'Burgundy', 'Light blue', 'Champagne',
                        'Light green', 'Dark Brown', 'Navy Blue',
                        'Light Grey', 'Off White', 'Light yellow',
                        'Emerald Green', 'Fluorescent Green',
                        'Fluorescent Yellow', 'Deep green', 'Rose Gold',
                        'Neutral', '…', 'Peach']

        self.__attrs = ['name',
                        'short_description',
                        'brand',
                        'model',
                        'color_family',
                        'SellerSku',
                        'warranty_type',
                        'name_ms',
                        'price',
                        'package_content',
                        'package_weight',
                        'package_length',
                        'package_width',
                        'package_height',
                        'tax_class']
        self.__size = "Int:3XSInt:XXSInt:XSInt:SInt:MInt:LInt:XLInt:XXLInt:3XLInt:4XLInt:5XLInt:XS/SInt:S/MInt:M/LInt:L/XLInt: One sizeInt:4XS"
        self.shoes = "1771, 11303, 4143, 4135, 11305, 4137, 4144, 11306, 4180, 11346, 11350, 11359, 11352, 1818, 1780, 1818, 1780"

    def get_account_id(self):
        return self.__accountId

    def get_mongodb(self):
        return self.__mongodb

    def adapt_color(self, o_color):
        colors = self.__color
        pre_color = {c: o_color.lower().find(c.lower())-len(c)
                     for c in colors if o_color.lower().find(c.lower()) != -1}
        if pre_color:
            return min(pre_color, key=pre_color.get)
        return 'Multicolor'
#Use the UploadImage or MigrateImage API to load your product images to Lazada image repository and get the image URL.
    def upload_image(self, image_url, strict=False):
        data = etree.XML("""<?xml version="1.0"?>
                <Request>
                    <Image>
                    <Url id="image_url"></Url>
                    </Image>
                </Request>
               """)
        



        data.cssselect("#image_url")[0].text = image_url
        result = self._post("MigrateImage", data=etree.tostring(data))
        try:
            new_image_url = result['Image']['Url']
        except:
            if strict:
                return False
            new_image_url = image_url
        return new_image_url

    def get_lazada_category_from_cb(self, cid):
        return cid

    @functools.lru_cache()
    def get_category_name(self, cid):
        cid = int(cid)
        lc = dict(lazada_category)
        return lc.get(cid)

    @timeout_decorator.timeout(20000)
    def create_product_from_CB(self, cb_product_info, category):
        
        #pdb.set_trace()
        """
        adpter schema: data map
        """


        if not len(cb_product_info):
            print("URL %s is not online")
            return
        # remove skus before update again
        # status 之前不设置为一吗？？？
        skus = [cb['sku'] for cb in cb_product_info if int(cb['status']) == 1]
        if not skus:
            print("no active product continue")
            return
        # /bin/bash: F1: No such file or directory
        d = collections.defaultdict(list)
        for cb in cb_product_info:
            d[cb.get('color', '')].append(cb)
            #cb['color']映射到cb 或者 “”映射到cb

        for color, lcb in d.items():
            self.create_product_from_CB_Sub(category, lcb)
        #what'mean of lcb?  Is cb a dict?????????


    def create_product_from_CB_Sub(self, category, cb_product_info):
        #为啥category变成了浮点型
        category = int(category)
        CB = ChinaBrandResource() 
        try:
            #下一句是我注释掉的
            #float(cb_product_info[0]['size'])
            # if size is pure number do not use that
            if 'pant' in cb_product_info[0]['title'].lower():
                return
        except:
            pass
       
       
        
        test_p = self.get_account_id()
        print(test_p)


        country = test_p[0:2] 
        #country = self.get_account_id()[0:2]
        #country == MY?
        cb_product = cb_product_info[0]
        #cb_product大体等于从cb抓取出来的一系列数据了
        lz_description = cb_product['goods_desc']
        # replace desc image to lazada
        # for desc_image in cb_product['desc_img']:
        #     lz_description = lz_description.replace(
        #         desc_image, self.upload_image(desc_image))
        lz_short_description = CB.get_li_feature(lz_description)
        if cb_product['color']:
            short_desc_extra = "<ul><li><strong>It is %s!</strong></li>" % cb_product['color']
            # 若cb中抓取到color则在title中补充到颜色属性
            cb_product['title'] = cb_product['title'] + "(%s)" % cb_product['color'].replace("&", "and")
        else:
            short_desc_extra = "there is no color from cb" 
            #新添的
        # if cb_product['size']:
        #     short_desc_extra += "<li>Its size is %s!</strong></li>" % cb_product['size']

        # 在简短描述里面加上颜色属性
        lz_short_description = lz_short_description.replace('<ul>', short_desc_extra)

        cb_product['color'] = self.adapt_color(cb_product['color'])
        lz_brand = cb_product['goods_brand'] if self.check_brand_exist(
            cb_product['goods_brand']) else 'OEM'

        # 得到Package Content放入lz_sku_spec中
        lz_sku_spec = CB.get_sku_specification(lz_description)

        cb_product['title'] = self.get_clean_title(cb_product,
                                                   lz_sku_spec, category)
        print("----------------------\n\n%s\n\n------------------"
              % cb_product['title'])
        if country != "MY":
            cb_product['title'] += " - intl"
        # add statics pictrure to description
        #对html来说，<, > , ?, & 和引号等有特殊意义 , 例如<a>表示连接 ,如果你确实需要在网页显示 '<a>'这一个东东，就必须escape(转义),变成 '& lt;a& gt;'
        lz_product = {"category": category, "name": cb_product['title'],
                      "brand": lz_brand,
                      "model": int(time.time()),
                      "color": cb_product['color'],
                      "description": html.escape(
                          lz_description.replace('max-width:1000px',
                                                 'max-width:100%')),
                      "short_description": html.escape(lz_short_description)}
        product_schema = etree.XML("""<Request>
            <Product>
                <PrimaryCategory>{category}</PrimaryCategory>
                <SPUId></SPUId>
                <Attributes>
                    <name>{name}</name>
                    <name_ms>{name}</name_ms>
                    <color_family>{color}</color_family>
                    <short_description>{short_description}</short_description>
                    <brand>{brand}</brand>
                    <model>{model}</model>
                    <warranty_type>No Warranty</warranty_type>
                    <description>{description}</description>
                </Attributes>
                <Skus id="skus">
                </Skus>
            </Product>
        </Request>
        """.format(**lz_product))

        variation = True
        c_skus = []

        for cb_sku in cb_product_info:
            # c_skus used for complete_sku意思是加上c_skus[]之后表示已经完成sku了？
            c_skus.append(cb_sku['sku'])
            cb_sku['encrypted_sku'] = self.encrypt_sku(cb_sku['sku'])
            # package content
            cb_sku['special_price'] = get_special_price(cb_sku['price'],
                                                        cb_sku['ship_weight'],
                                                        country = country)
            if float(cb_sku['ship_weight']) > 0.5:
                return 

            cb_sku['price'] = get_sale_price(cb_sku['special_price'])
            start_date = arrow.now()
            cb_sku['special_from_date'] = start_date.strftime("%Y-%m-%d")
            cb_sku['special_to_date'] = start_date.replace(days=+365
                                                        ).strftime("%Y-%m-%d")
            cb_sku['package_content'] = lz_sku_spec.get('Package Content',
                                                        '1 x see product description')
            # quantity
            cb_sku['quantity'] = random.randrange(3, 50)
            cb_sku['keywords'] = self.get_key_words(cb_sku, category)
            product_sku = etree.XML("""<Sku>
                    <SellerSku>{encrypted_sku}</SellerSku>
                    <tax_class>default</tax_class>
                    <quantity>{quantity}</quantity>
                    <price>{price}</price>
                    <special_price>{special_price}</special_price>
                    <special_from_date>{special_from_date}</special_from_date>
                    <special_to_date>{special_to_date}</special_to_date>
                    <color_family>{color}</color_family>
                    <model>LA{encrypted_sku}</model>
                    <package_length>{package_length}</package_length>
                    <package_height>{package_height}</package_height>
                    <package_weight>{ship_weight}</package_weight>
                    <package_width>{package_width}</package_width>
                    <package_width>{package_width}</package_width>
                    <package_content>{package_content}</package_content>
                    <std_search_keywords>{keywords}</std_search_keywords>
                    <Images>
                    </Images>
                    <Image></Image>
                </Sku>""".format(**cb_sku))

            # extra SKU attrs
            # extra_attr_str = get_extra_attrs(category)
            cattrs = self.get_mandatory_attributes(category)
            extra_attr = {}
            for ck, cv in cattrs.items():
                if cb_sku['size'] in cv:
                    extra_attr[ck] = cb_sku['size']
                elif ck == 'ring_size':
                    if cb_sku['size'] and cb_sku['size'].isdigit():
                        sku_size = cb_sku['size']
                    else:
                        cb_sku['title'] = cb_sku['title'] + "(Size:%s)" % cb_sku['size'].replace("&", "and")
                        product_schema.xpath("//name")[0].text = cb_sku['title']
                        sku_size = 'Not Specified'
                        # do not associated product if no size
                        variation = False
                    extra_attr[ck] = sku_size
                elif ck == 'size':
                    if cb_sku['size']:
                        format_size = re.sub('2', 'X', cb_sku['size']).upper()

                        if category in self.shoes:
                            sku_size = "EU:" + cb_sku['size']

                        elif format_size in self.__size and format_size in cv:

                            sku_size = 'Int:'+ format_size
                        else:
                            cb_sku['title'] = cb_sku['title'] + "(Size:%s)" % cb_sku['size'].replace("&", "and")
                            product_schema.xpath("//name")[0].text = cb_sku['title']
                            sku_size = "Int: One size"
                            # do not associated product if no size
                            variation = False
                    else:
                        sku_size = 'Not Specified'
                        variation = False
                    extra_attr[ck] = sku_size
                else:
                    if 'One Size' in cv:
                        extra_attr[ck] = 'One Size'
                    elif 'Int:One Size' in cv:
                        extra_attr[ck] = 'Int:One Size'
                    elif 'Int: One Size' in cv:
                        extra_attr[ck] = 'Int: One Size'
                    elif 'color' in ck:
                        extra_attr[ck] = 'Multicolor'
                    else:
                        extra_attr[ck] = 'Not Specified'
                    variation = False

            for tag, tv in extra_attr.items():
                new_tag = etree.Element(tag)
                new_tag.text = str(tv)
                attr_type = self.check_attrs_type(category, tag)
                if attr_type == 'sku':
                    product_sku.xpath("//Sku")[0].append(new_tag)
                else:
                    product_schema.xpath("//Attributes")[0].append(new_tag)

            # check if image exist mongodb
            images = self.__mongodb.all_cb_sku.find_one({"sku": cb_sku["sku"]}).get("limages")
            if images:
                self.remove_elements_by_tag(product_sku, 'Images')
                product_sku.append(etree.XML(images))
            else:
                # image
                for image_src in cb_sku['original_img'][:8]:
                    image_src = self.upload_image(image_src, strict=True)
                    if not image_src:
                        continue
                    e_image_src = etree.Element("Image")
                    e_image_src.text = image_src
                    product_sku.find("Images").append(e_image_src)

                # save image to mongodb
                self.__mongodb.all_cb_sku.update(
                    {'sku': cb_sku['sku']},
                    {"$set": {"limages": etree.tostring(
                        product_sku.find("Images"))}})
            if not variation:
                self.remove_elements_by_tag(product_schema, "Sku")
                product_schema.xpath("//Skus")[0].append(product_sku)
                result = self._post("CreateProduct",
                                    data=etree.tostring(product_schema))
                # if have been upload to lazada save it.
                if result:
                    self.complete_sku(cb_sku['sku'], 10)
            else:
                product_schema.xpath("//Skus")[0].append(product_sku)
        print("\n\n\n\nthe API model of CreateProduct: \n%s" % product_schema)
        #import pdb;pdb.set_trace()

        result = self._post("CreateProduct", data=etree.tostring(product_schema))
        # if have been upload to lazada save it.
        if result:
            self.complete_sku(c_skus, 10)

    #status mean of diffrent num 1 2 -1
    def complete_sku(self, cb_sku, status):
        if isinstance(cb_sku, str):
            cb_sku = [cb_sku, ]
        # $in表示匹配cb_sku  
        self.__mongodb.all_cb_sku.update_many({'sku': {"$in": cb_sku}},
                                              {"$set": {"lazada": status}})
        print(status)

    def encrypt_sku(self, sku):
        return self.sku_pre + str(sku)

    def old_encrypt_sku(self, sku):
        return 'LACB-' + str(sku)

    def get_true_sku(self, esku):
        if '-' in esku:
            return esku.split('-')[-1].split("#")[0]
        return self.__mongodb.cb_sku.find_one({"encrypted_sku": esku})['sku']

    def get_category_from_title(self, category, title):
        url = "http://www.lazada.com.my/catalog/"
        db = self.__mongodb
        category = category.replace("'s", "")
        category = category.split(">")
        category = category[1:]  # + category[-1:] + category[-1:]
        category = " ".join(category)

        titles = [title + " " + category, title]
        for title in titles:
            sr = requests.get(url, params={"q": title})
            srs = BeautifulSoup(sr.text, "lxml")
            s_url = ""
            for s in srs.select(".c-product-card__name")[:1]:
                s_url = s['href']
            if not s_url:
                continue
            s_url = "http://www.lazada.com.my" + s_url
            pr = requests.get(s_url)
            prsoup = BeautifulSoup(pr.text, "lxml")
            cstring = prsoup.select_one(".breadcrumb__list").text
            cstring = cstring.split("\n\n\n")
            cstring = [cs.strip() for cs in cstring if cs][:-1]
            cstring = ".*" + ".*".join(cstring) + ".*"
            r = db.cid.find_one({"c": {"$regex": cstring, "$options": "i"}})
            cid = r['c'].split(":")[-1]
            print(r, "VVVVVVVVVvvvvvvvv", title )
            return cid

    def remove_poor_product(self):
        skus = self.get_product(status='rejected')
        s_skus = []
        [s_skus.extend(s['Skus']) for s in skus['Products']]
        seller_skus = [s['SellerSku'] for s in s_skus]
        chunks = [seller_skus[x:x+10] for x in range(0, len(seller_skus), 10)]
        for c in chunks:
            print(c)
            self.remove_product(c)

    def remove_product(self, skus):
        data = etree.XML("""<?xml version="1.0"?>
                <Request>
                    <Product>
                    <Skus>
                    <Sku>
                    </Sku>
                    </Skus>
                   </Product>
                </Request>
               """)
        for sku in skus:
            sellerSku = etree.Element("SellerSku")
            sellerSku.text = sku
            data.xpath('//Sku')[0].append(sellerSku)
        try:
            result = self._post("RemoveProduct",
                                data=etree.tostring(data))
        except:
            return False
        if result:
            return True

    def check_brand_exist(self, brand):
        # check is brand on lazada
        return brand in lazada_brand

    def get_special_price_data(self, day_offset=+365):
        start_date = arrow.now().replace(days=-1)
        special_from_date = start_date.strftime("%Y-%m-%d")
        special_to_date = start_date.replace(days=day_offset).strftime("%Y-%m-%d")
        return special_from_date, special_to_date

    def update_price_quantity(self, cb_sku_no):
        CB = ChinaBrandResource()
        cb_skus = CB.updated_product_by_encryptsku(cb_sku_no)
        product_list = etree.XML("""<Request><Product>
                        <Skus>
                        </Skus>
                    </Product>
                </Request>""")
        for cb_sku in cb_skus:
            cb_sku['special_price'] = get_special_price(cb_sku['price'],
                                                        cb_sku['ship_weight'])
            cb_sku['price'] = get_sale_price(cb_sku['special_price'])
            cb_sku['special_from_date'], cb_sku['special_to_date'] = \
                self.get_special_price_data()
            # quantity
            cb_sku['quantity'] = 0
            if cb_sku.get('is_on_sale', 0) in (1, '1'):
                cb_sku['quantity'] = random.randrange(30, 666)
            product_sku = etree.XML("""<Sku>
                    <SellerSku>{encrypted_sku}</SellerSku>
                    <Quantity>{quantity}</Quantity>
                    <Price>{price}</Price>
                    <SalePrice>{special_price}</SalePrice>
                    <SaleStartDate>{special_from_date}</SaleStartDate>
                    <SaleEndDate>{special_to_date}</SaleEndDate>
                </Sku>""".format(**cb_sku))
            product_list.xpath('//Skus')[0].append(product_sku)
            self.__mongodb.cb_sku.update({'sku': cb_sku['sku']}, cb_sku)
        result = self._post("UpdatePriceQuantity",
                            data=etree.tostring(product_list))
        print(result)
        if result:
            return True

    def get_clean_title(self, cb_sku, spec, cid):
        re.sub("%s |%s " % (cb_sku.get('goods_brand'), spec.get('model')),
                                                "", cb_sku['title'], flags=re.I)
        clean_title = cb_sku['title']
        cname = self.get_category_name(cid)
        if cname:
            cname = cname.replace("&", ' ')
            cname = cname.split(" / ")
            clean_title = cname[0].strip() + " " \
                + cname[-1].strip().replace('?', '') + " " + clean_title
        clean_title = re.sub(' +', ' ', clean_title)
        return clean_title.lower().title()

    def get_key_words(self, cb_sku, cid):
        cname = self.get_category_name(cid)
        if cname:
            cname = cname.replace("&", ' ')
            cname = cname.split(" / ")
        else:
            cname = cb_sku['title'].split(' ')
        return json.dumps(cname)

    def remove_empty_elements(self, doc):
        for element in doc.xpath('//*[not(node())]'):
            element.getparent().remove(element)

    def remove_elements_by_tag(self, all_node, tag):
        for bad in all_node.xpath("//%s" % tag):
              bad.getparent().remove(bad)
        return all_node

    @functools.lru_cache()
    def get_category_attributes(self, cid):
        cid = int(cid)
        #pdb.set_trace()
        result = self._post("GetCategoryAttributes",
                            extra_param={"PrimaryCategory": cid})
        return result

    def check_attrs_type(self, cid, attr_name):
        attributes = self.get_category_attributes(cid)
        for attr in attributes:
            if attr['name'] == attr_name:
                return attr['attributeType']

    @functools.lru_cache()
    def get_mandatory_attributes(self, cid):
        attributes = self.get_category_attributes(cid)
        format_attr = {}
        #在lazada中得到这个分类的属性
        print("refetch category")
        for attr in attributes:
            if 1 in (attr.get('mandatory', 0), attr.get('isMandatory', 0)) and attr['name'] not in self.__attrs or attr['name'] == 'size':
                format_attr[attr['name']] = [k['name'] for k in attr['options']]
        return format_attr
    #priority not > and > or。
    def create_product(self):
        pass

    def add_product(self):
        return self._post("MigrateImage")

    def get_product(self, limit=100, offset=0, update_before="",
                    status='live', skus=None, **kwargs):
        update_before = update_before or arrow.now().floor('hour')
        extra_param = kwargs
        # extra_param['UpdatedAfter'] = str(arrow.Arrow(2017, 2, 22).floor('hour'))
        extra_param['UpdatedBefore'] = str(update_before)
        if skus:
            extra_param['SkuSellerList'] = json.dumps(skus)
        extra_param['Filter'] = status
        extra_param['Limit'] = limit
        extra_param['Offset'] = offset
        return self._post("GetProducts", extra_param=extra_param)

    def set_packed(self, *args, **kwargs):
        extra_param = {"DeliveryType": "dropship",
                       "ShippingProvider": "LGS-FM40"}
        extra_param.update(kwargs)
        if not extra_param.get("TrackingNumber") \
                and extra_param.get("OrderItemIds"):
            extra_param["OrderItemIds"] = json.dumps(
                extra_param["OrderItemIds"])
            result = self._post("SetStatusToPackedByMarketplace",
                                extra_param=extra_param)
            extra_param['TrackingNumber'] = \
                result['OrderItems'][0]["TrackingNumber"]

        if extra_param.get("TrackingNumber") and \
                extra_param.get("OrderItemIds"):
            return self._post("SetStatusToReadyToShip",
                              extra_param=extra_param)
        return False

    def get_document(self, *args, **kwargs):
        extra_param = {"DocumentType": kwargs.get("DocumentType",
                                                  "shippingLabel"),
                       "OrderItemIds": kwargs.get("OrderItemIds")}

        if extra_param.get("OrderItemIds"):
            extra_param["OrderItemIds"] = json.dumps(
                extra_param["OrderItemIds"])
            result = self._post("GetDocument",
                                extra_param=extra_param)
            try:
                return base64.b64decode(result["Document"]["File"])
            except:
                # need RTS firstly
                if self.set_packed(*args, **kwargs):
                    return self.get_document(*args, **kwargs)

    def get_order(self, *args, **kwargs):
        extra_param = kwargs
        return self._post("GetOrder", extra_param=extra_param)

    def get_orders(self, *args, **kwargs):
        extra_param = kwargs
        return self._post("GetOrders", extra_param=extra_param)

    def get_pending_orders(self, status="pending", createAfter=None):
        createAfter = createAfter or \
            str(arrow.now().replace(days=-3).floor('hour'))
        return self.get_orders(CreatedAfter=createAfter).get("Orders")


    @functools.lru_cache()
    def get_order_items(self, order_id):
        extra_param = {'OrderId': order_id}
        return self._post("GetOrderItems", extra_param=extra_param)

    def ready_to_ship(self, o, supply, country="MY",
                      ship_method='MYLGSO', force=False):
        oadpter = {"order_platforms": 6,
                   "original_account": self.__accountId, }
        oadpter['user_order_sn'] = self.store_name.split("-")[0] + str(o['OrderNumber'])
        # if force:
        #     oadpter['user_order_sn'] += "-extra"
        oadpter['country'] =  country
        oadpter['original_order_id'] = o['OrderId']
        oadpter['firstname'] = o['CustomerFirstName']
        oadpter['lastname'] = o['CustomerLastName']
        oadpter['shipping_method'] = ship_method
        oadpter['addressline1'] = o['AddressShipping']['Address1']
        oadpter['city'] = o['AddressShipping']['City']
        oadpter['zip'] = o['AddressShipping']['PostCode'] or '27 8000'

        oadpter['goods_info'] = []
        oitems = self.get_order_items(o['OrderId'])
        oitems = oitems['OrderItems']
        for i in oitems:
            goods_sn = self.get_true_sku(i['Sku'])
            print(goods_sn)
            goods_no = 1
            check = 0
            try:
                from lazada_resources.models import cbskuMap
                change_sku = cbskuMap.objects.get(o_sku=goods_sn, active=True).c_sku
                for sku in change_sku.split('-'):
                    oadpter['goods_info'].append({'goods_sn': sku,
                                          'goods_number': 1})
                check = True
                continue
            except:
                pass
            if not ('CM01' in i['Sku'] or 'LA01' in i['Sku']) or check:
                # need adjust
                return False

            oadpter['goods_info'].append({'goods_sn': str(goods_sn),
                                          'goods_number': str(goods_no)})
        print(oadpter)
        result = supply.put_order(**oadpter)
        return result

    def adjust_price(self, cb_sku):
        product_list = etree.XML("""<Request><Product>
                        <Skus>
                        </Skus>
                    </Product>
                </Request>""")
        cb_sku['SaleStartDate'], cb_sku['SaleEndDate'] = \
            self.get_special_price_data(+100)

        product_sku = etree.XML("""<Sku></Sku>""")
        for key, value in cb_sku.items():
            new_tag = etree.Element(key)
            new_tag.text = str(value)
            product_sku.xpath('//Sku')[0].append(new_tag)

        product_list.xpath('//Skus')[0].append(product_sku)
        result = self._post("UpdatePriceQuantity",
                            data=etree.tostring(product_list))
        return result

    def adjust_discount_date(self, end_date="2017-02-22"):
        cbinfos = self.__mongodb.cb_sku.find({"special_to_date": end_date})

        for cb_sku in cbinfos:

            product_list = etree.XML("""<Request><Product>
                        <Skus>
                        </Skus>
                    </Product>
                </Request>""")

            if not cb_sku.get("encrypted_sku"):
                continue
            print(cb_sku['encrypted_sku'])
            cb_sku['special_from_date'], cb_sku['special_to_date'] = \
                self.get_special_price_data(+100)

            product_sku = etree.XML("""<Sku>
                    <SellerSku>{encrypted_sku}</SellerSku>
                    <SaleStartDate>{special_from_date}</SaleStartDate>
                    <SaleEndDate>{special_to_date}</SaleEndDate>
                </Sku>""".format(**cb_sku))
            product_list.xpath('//Skus')[0].append(product_sku)
            cb_sku.pop('_id', None)
            self.__mongodb.cb_sku.update_many({'sku': cb_sku['sku']}, {"$set" :
                                                                       {"special_from_date": cb_sku['special_from_date'],
                                                                        "special_to_date":cb_sku['special_to_date']}})

            result = self._post("UpdatePriceQuantity",
                                data=etree.tostring(product_list))
            if result:
                c = self.__mongodb.cb_sku.update({'sku': cb_sku['sku']}, {"$set": {"lazada_uploaded": True}})
                print(c)
            print(etree.tostring(product_list))
            print(result)

    def start_update_product_desc(self):
        cb_info = self.__mongodb.cb_sku.find({"encrypted_sku":
                                              {'$regex': 'LA01-*'},
                                              "lazada_uploaded": True})
        self.update_product_desc(cb_info)

    def change_status(self, sku, status):
        try:
            product_schema = etree.XML("""<Request><Product>
                    <Skus>
                        <Sku>
                         <SellerSku>%s</SellerSku>
                         <active>%s</active>
                        </Sku>"
                    </Skus>
                </Product>
            </Request>""" % (sku, status))
            print(sku, status)
            result = self._post("UpdateProduct",
                            data=etree.tostring(product_schema))
        except:
            with open('%s.log' % self.__accountId, 'a') as f:
                traceback.print_exc(file=f)
                traceback.print_exc()

    def update_product_desc(self, list_product):
        CB = ChinaBrandResource()
        for cb_product in list_product:
            desc = {}
            lz_description = cb_product['goods_desc']
            # replace desc image to lazada
            lz_short_description = CB.get_li_feature(lz_description)
            # color size
            if cb_product['color']:
                short_desc_extra = "<ul><li><strong>Its main color is %s!</strong></li>" % cb_product['color']
            if cb_product['size']:
                short_desc_extra += "<li>Its size is %s!</strong></li>" % cb_product['size']
            lz_short_description = lz_short_description.replace('<ul>', short_desc_extra)
            desc['short_description'] = html.escape(lz_short_description)
            desc['SellerSku'] = cb_product['encrypted_sku']
            try:
                product_schema = etree.XML("""<Request><Product>
                        <Attributes>
                            <short_description>{short_description}</short_description>
                        </Attributes>
                        <Skus>
                        <Sku>
                            <SellerSku>{SellerSku}</SellerSku>
                        </Sku>
                        </Skus>
                    </Product>
                </Request>""".format(**desc))

                result = self._post("UpdateProduct",
                                    data=etree.tostring(product_schema))
                print(result)
            except:
                traceback.print_exc()

    def _post(self, action, extra_param=None, data=None):
        url = self.__url
        parameters = { 'UserID': self.__user_id,
            'Version': '1.0',
            'Action': action,
            'Format': 'JSON',
            'Timestamp': str(arrow.utcnow().floor('hour'))}
        if extra_param:
            parameters.update(extra_param)
        concatenated = urlencode(sorted(parameters.items())).replace("+", "%20")
        print(parameters)
        parameters['Signature'] = HMAC(self.__api_key, concatenated.encode(),
                                       sha256).hexdigest()


        print(parameters['Signature'])
        result = requests.post(url, params=parameters, data=data or {})
        # if 'seller sku is exist' in result.text.lower():
        #     print("\n\n!!!SELLER_SKU_IS_EXIST change to update product\n\n")
        #     return self._post("UpdateProduct", data=data)
        print(result.text[:500])
        result = json.loads(result.text)
        #将python json格式解码成Python数据风格json.dumps : dict转成str     json.dump是将python数据保存成json

        #json.loads:str转成dict json.load是读取json数据 
        # self.__mongodb.cb_lazada_result.insert(result)
        if result.get("SuccessResponse"):
            return result.get("SuccessResponse").get("Body")

if __name__ == "__main__":
    site  = {"api_key": 'U_Oobajpv6G6B4wIgrq349_ARwJ6Z9lFSHZqm705nEiDv6fP-fLSgkV2',
        "user_id": "citi@ctdata.my",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "accountId": "MY112E5",
             "sku_pre": "CM01-"
    }

    # l = Lazada(**site)
    l = Lazada()
    # l.get_category_attributes('10200')
    # import csv

    # for lc in lazada_category:
    #     print("start get category %s" % lc[0])
    #     try:
    #         attrs = l.get_mandatory_attributes(lc[0])
    #     except:
    #         attrs = ['exception need handle check', ]
    #     if not attrs:
    #         continue
    #     with open('lazada_attrs.csv', 'a') as csvfile:
    #         spamwriter = csv.writer(csvfile)
    #         spamwriter.writerow(list(lc) + attrs)
    # url = "https://api.sellercenter.lazada.com.my?Action=GetProducts&Format=json&SkuSellerList=%5B%2240DWX57PQ%22%2C%20%2240DXQ83P1%22%2C%20%2240DY9V5IM%22%2C%20%2240DYBLRH6%22%2C%20%2240DYA6B1G%22%2C%20%2240DXG8DXN%22%2C%20%2240DWX57PT%22%2C%20%2240DWX6RQG%22%2C%20%2240DX6M7TB%22%2C%20%2240DXFXMSL%22%5D&Timestamp=2017-02-14T05%3A43%3A16%2B00%3A00&UserID=8023lays%40gmail.com&Version=1.0&Signature=db8f531a0dfda6503e2185cccad92dea6469d3d56347a4f0d9ade212c2a9bcc0"

    # l.update_product_desc(url)

    # image_url = "https://gloimg.chinabrands.com/cb/pdm-product-pic/Clothing/2016/11/15/source-img/20161115105706_58846.jpg"
    # print(l.upload_image(image_url))
    # import csv  (Comma_Separated Value)
    # import traceback

    # f = open('Lazada_product.csv')
    # csv_f = csv.reader(f)
    # # csv_f = [('10300','https://www.chinabrands.com/item/product206076.html'),]
    
    py = pymongo.MongoClient("mongodb://localhost/").cb_info
    #    > $gt , >= $gte, < $lt, <= $lte, != $ne
    while True:
        sku_info = py.all_cb_sku.find_one({'lazada_cid': {"$ne": None},
                                           "lazada": 0, 'status': 1})

        if not sku_info:
            break
        sku = sku_info.get('sku')

        category = sku_info['lazada_cid']
        #category id info from category tree.xlsx
        #where is cb_sku
        check = py.cb_sku.find_one({"sku": sku, "lazada_uploaded": True})
        if check:
            print("SKU %s have been upload" % sku)
            #statue equates -2 repr SKU have been upload?
            l.complete_sku(sku, -2)
            continue

        all_sku = py.all_cb_sku.find({"sku": {"$regex": "^%s.*" % sku[:-2]},
                                      site['accountId']: None,
                                      "quantity_new": {"$ne": -5}})
        #where is quantity_new site['accountId']

        #pdb.set_trace()
        if not all_sku:
            break
        try:
            all_sku = list(all_sku)
            skus = [sku['sku'] for sku in all_sku]
            print("Start upload URL %s" % str(skus))

            l.complete_sku(skus, -1)
            #把statue改为-1
            l.create_product_from_CB(all_sku, category)
            #break
        except:
            with open('log.log', 'a') as f:
                # print("Error URL: %s-%s" % (row['cid'], row['sku']), file=f)
                traceback.print_exc(file=f)
                traceback.print_exc()
# https://lazada-sellercenter.readme.io/docs?spm=a2o7h.10547918.0.0.24af1e131QIzkC
