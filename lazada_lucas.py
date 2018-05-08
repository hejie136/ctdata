from hashlib import sha256
from hmac import HMAC
import arrow
from urllib.parse import urlencode
import requests
from lxml import etree
import json
from temp_script import ChinaBrandResource
import html
from lazada_fee import get_sale_price, get_special_price
from lazada_brand import lazada_brand
import re
import pymongo
import traceback
import random
import collections
from lazada_category_attrs import get_extra_attrs
import timeout_decorator


class Lazada():
    def __init__(self):
        self.__api_key = b'IMz24VurEFzzwdlJhGMkq6IIejnejnInqzgnEA2YoXzl5zIwfyNPIMKe'
        self.__user_id = '8023lays@gmail.com'
        self.__url = 'https://api.sellercenter.lazada.com.my/'
        self.__mongodb = pymongo.MongoClient("mongodb://localhost:27017/"
                                             ).cb_info
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

    def adapt_color(self, o_color):
        c = self.__color
        i = [i for i, v in enumerate(c) if v.lower() == o_color.lower()]
        if not i:
            i = [k for k, v in enumerate(c)
                 if v.lower() == o_color.split(' ')[-1].lower() or
                 v.lower() == o_color.split(' ')[0].lower() or
                 v.lower() == o_color.lower().split('with')[0] or
                 v.lower() == o_color.lower().split('and')[0]]
        if i:
            return c[i[0]]
        else:
            return '…'

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

    @timeout_decorator.timeout(2000)
    def create_product_from_CB(self, category, sku, adpter_schema=None):
        """
        adpter schema: data map
        """
        CB = ChinaBrandResource()
        cb_product_info = CB.get_product_info(sku)
        if not cb_product_info:
            print("URL %s is not online")
            return
        # remove skus before update again
        skus = [cb['sku'] for cb in cb_product_info if cb['status'] == 1]
        if not skus:
            self.complete_sku(sku, category)
            return

        self.remove_product(skus)

        # defaultdict
        d = collections.defaultdict(list)
        for cb in cb_product_info:
            d[cb.get('color', '')].append(cb)

        for color, lcb in d.items():
            self.create_product_from_CB_Sub(category, lcb)

    def create_product_from_CB_Sub(self, category, cb_product_info):
        CB = ChinaBrandResource()
        cb_product_info = [pinfo for pinfo in cb_product_info
                           if pinfo['status'] == 1]

        for cb_sku in cb_product_info:
            cb_sku['encrypted_sku'] = self.encrypt_sku(cb_sku['sku'])
            cb_sku['associateSku'] = self.encrypt_sku(cb_product_info[0]['sku'])
            cb_sku['lazada_uploaded'] = self.cb_product_adpter(cb_sku, category,
                                                               CB) or False
            # if have been upload to lazada save it.
            self.__mongodb.cb_sku.replace_one({'sku': cb_sku['sku']},
                                              cb_sku, True)
            self.complete_sku(cb_sku['sku'], category)

    def complete_sku(self, cb_sku, cid):
        self.__mongodb.pre_lucas_upload.replace_one({'sku': cb_sku},
                                              {'sku': cb_sku,
                                               'status': 1,
                                               "cid": cid}, True)

    def encrypt_sku(self, sku):
        return 'RA01-' + str(sku)

    def old_encrypt_sku(self, sku):
        return 'RACB-' + str(sku)

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
            sellerSku.text = self.old_encrypt_sku(sku)
            data.xpath('//Sku')[0].append(sellerSku)
        print(etree.tostring(data))
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

    def get_special_price_data(self, day_offset=+5):
        start_date = arrow.now()
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
            self.__mongodb.cb_sku.update({'sku': cb_sku['sku']}, cb_sku)
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

        result = self._post("UpdatePriceQuantity",
                            data=etree.tostring(product_list))
        print(result)
        if result:
            return True

    def cb_product_adpter(self, cb_product_info, category, CB):
        cb_sku = cb_product = cb_product_info
        lz_description = cb_product['goods_desc']
        # replace desc image to lazada
        for desc_image in cb_product['desc_img']:
            lz_description = lz_description.replace(
                desc_image, self.upload_image(desc_image))
        lz_short_description = CB.get_li_feature(lz_description)
        if cb_product['color']:
            short_desc_extra = "<ul><li><strong>Its main color is %s!</strong></li>" % cb_product['color']
            lz_short_description = lz_short_description.replace('<ul>', short_desc_extra)
            cb_sku['title'] = cb_sku['title'] + "(%s)" % cb_sku['color'].replace("&", "and")

        if cb_sku['size']:
            cb_sku['title'] = cb_sku['title'] + "(Size:%s)" % cb_sku['size'].replace("&", "and")
        print(cb_sku['title'])

        cb_product['color'] = self.adapt_color(cb_product['color'])
        lz_brand = cb_product['goods_brand'] if self.check_brand_exist(
            cb_product['goods_brand']) else 'OEM'
        lz_sku_spec = CB.get_sku_specification(lz_description)
        lz_product = {"category": category, "name": cb_product['title'],
                      "brand": lz_brand,
                      "associateSku": cb_product['associateSku'],
                      "description": html.escape(
                          lz_description.replace('max-width:1000px',
                                                 'max-width:100%')),
                      "short_description": html.escape(lz_short_description)}
        product_schema = etree.XML("""<Request>
            <Product>
                <PrimaryCategory>{category}</PrimaryCategory>
                <SPUId></SPUId>
                <AssociatedSku>{associateSku}</AssociatedSku>
                <Attributes>
                    <name>{name}</name>
                    <name_ms>{name}</name_ms>
                    <short_description>{short_description}</short_description>
                    <brand>{brand}</brand>
                    <model>RA{associateSku}</model>
                    <warranty_type>No Warranty</warranty_type>
                    <description>{description}</description>
                </Attributes>
                <Skus id="skus">
                </Skus>
            </Product>
        </Request>
        """.format(**lz_product))
        # sku add
        # package content
        cb_sku['special_price'] = get_special_price(cb_sku['price'],
                                                    cb_sku['ship_weight'])
        cb_sku['price'] = get_sale_price(cb_sku['special_price'])
        start_date = arrow.now()
        cb_sku['special_from_date'] = start_date.strftime("%Y-%m-%d")
        cb_sku['special_to_date'] = start_date.replace(days=+5
                                                       ).strftime("%Y-%m-%d")
        cb_sku['package_content'] = lz_sku_spec.get('Package Content',
                                                    'see product detail')
        # quantity
        cb_sku['quantity'] = 0
        if cb_sku.get('is_on_sale', 0) in (1, '1'):
            cb_sku['quantity'] = random.randrange(30, 666)
        product_sku = etree.XML("""<Sku>
                <SellerSku>{encrypted_sku}</SellerSku>
                <tax_class>default</tax_class>
                <quantity>{quantity}</quantity>
                <price>{price}</price>
                <special_price>{special_price}</special_price>
                <special_from_date>{special_from_date}</special_from_date>
                <special_to_date>{special_to_date}</special_to_date>
                <color_family>{color}</color_family>
                <model>RA{encrypted_sku}</model>
                <package_length>{package_length}</package_length>
                <package_height>{package_height}</package_height>
                <package_weight>{ship_weight}</package_weight>
                <package_width>{package_width}</package_width>
                <package_width>{package_width}</package_width>
                <package_content>{package_content}</package_content>
                <Images>
                </Images>
                <Image></Image>
            </Sku>""".format(**cb_sku))

        # extra SKU attrs
        extra_attr_str = get_extra_attrs(category)
        if 'size' in extra_attr_str:
            if cb_sku['size']:
                format_size = re.sub('2', 'X', cb_sku['size']).upper()
                sku_size = 'Int:'+ format_size if format_size in self.__size else "Int: One size"
            else:
                sku_size = 'Not Specified'
            extra_attr_str = extra_attr_str.format(size=sku_size)
        extra_attr_element = etree.XML(extra_attr_str)
        for eae in extra_attr_element.getchildren():
            if 'size' in eae.tag:
                product_sku.append(eae)
            else:
                product_schema.xpath("//Attributes")[0].append(eae)

        # image
        for image_src in cb_sku['original_img'][:8]:
            image_src = self.upload_image(image_src, strict=True)
            if not image_src:
                continue
            e_image_src = etree.Element("Image")
            e_image_src.text = image_src
            product_sku.find("Images").append(e_image_src)

        product_schema.xpath("//Skus")[0].append(product_sku)
        result = self._post("CreateProduct",
                            data=etree.tostring(product_schema))
        if result:
            return True

    def remove_empty_elements(self, doc):
        for element in doc.xpath('//*[not(node())]'):
            element.getparent().remove(element)

    def get_category_attributes(self, cid):
        result = self._post("GetCategoryAttributes",
                            extra_param={"PrimaryCategory": cid})
        return result

    def get_mandatory_attributes(self, cid):
        attributes = self.get_category_attributes(cid)
        attr_list = []
        for attr in attributes:
            if attr['mandatory'] == 1 and attr['name'] not in self.__attrs:
                attr_list.append([attr['name'], attr['label'], attr['inputType']])
        return attr_list

    def create_product(self):
        pass

    def add_product(self):
        return self._post("MigrateImage")

    def get_product(self, limit=100, offset=20, status='live'):
        extra_param = {}
        # extra_param['CreatedBefore'] = str(arrow.utcnow().replace(days=5).floor('hour'))
        extra_param['Filter'] = status
        extra_param['Limit'] = limit
        extra_param['Offset'] = offset
        return self._post("GetProducts", extra_param=extra_param)

    def start_update_product_desc(self):
        cb_info = self.__mongodb.cb_sku.find({"encrypted_sku":
                                              {'$regex': 'RA01-*'},
                                              "lazada_uploaded": True})
        self.update_product_desc(cb_info)

    def update_product_desc(self, list_product):
        CB = ChinaBrandResource()
        for cb_product in list_product:
            desc = {}
            lz_description = cb_product['goods_desc']
            # replace desc image to lazada
            lz_short_description = CB.get_li_feature(lz_description)
            if cb_product['color']:
                short_desc_extra = "<ul><li><strong>Its main color is %s!</strong></li>" % cb_product['color']
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
        parameters = {
            'UserID': self.__user_id,
            'Version': '1.0',
            'Action': action,
            'Format': 'JSON',
            'Timestamp': str(arrow.utcnow().floor('hour'))}
        if extra_param:
            parameters.update(extra_param)
        concatenated = urlencode(sorted(parameters.items()))
        parameters['Signature'] = HMAC(self.__api_key, concatenated.encode(),
                                       sha256).hexdigest()
        result = requests.post(url, params=parameters, data=data or {})
        result = json.loads(result.text)
        print(result)
        self.__mongodb.cb_lazada_result.insert(result)
        if result.get("SuccessResponse"):
            return result.get("SuccessResponse").get("Body")

if __name__ == "__main__":
    l = Lazada()
    # l.get_category_attributes('10200')
    # from lazada_catergory import lazada_category
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
    # import csv
    # import traceback

    # f = open('Lazada_product.csv')
    # csv_f = csv.reader(f)
    # # csv_f = [('10300','https://www.chinabrands.com/item/product206076.html'),]
    py = pymongo.MongoClient("mongodb://localhost:27017/").cb_info
    while True:
        row = py.pre_lucas_upload.find_one({'status': 0})
        if not row:
            break
        try:
            print("Start upload URL %s" % row['sku'])

            l.complete_sku(row['sku'], row['cid'])
            l.create_product_from_CB(row['cid'], row['sku'])
        except:
            with open('log.log', 'a') as f:
                # print("Error URL: %s-%s" % (row['cid'], row['sku']), file=f)
                traceback.print_exc(file=f)
                traceback.print_exc()
            print("Error URL %s" % row['sku'])
