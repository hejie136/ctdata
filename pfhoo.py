import pymongo
import requests
import json
from lazada import Lazada
from difflib import SequenceMatcher
import random
import re
from bs4 import BeautifulSoup
import collections
import html
from lxml import etree
from lazada_fee import get_sale_price, get_special_price
from lazada_category_attrs import get_extra_attrs
import arrow
import traceback

mongo = pymongo.MongoClient("mongodb://mongo.server:27017/").pf_info


class PfhooLazada(Lazada):
    def __init__(self, **kwargs):
        self.mongo = pymongo.MongoClient("mongodb://mongo.server:27017/").pf_info
        super(PfhooLazada, self).__init__(**kwargs)

    def upload_pfh(self):
        pfh_info = self.mongo.pf_sku.find_one({"lazada": {"$ne": 1}})
        print('start from here sku %s' % pfh_info['SKU'])
        pfh_infos = self.mongo.pf_sku.find({"SPU": pfh_info['SPU']})
        pfh_infos = [self.process_pfh_info(pfh) for pfh in pfh_infos]
        # defaultdict
        d = collections.defaultdict(list)
        for cb in pfh_infos:
            if cb:
                print(cb['SKU'])
                self.complete_sku(cb['SKU'])
                d[cb.get('color', '')].append(cb)

        for color, lcb in d.items():
            for cb_sku in lcb:
                cb_sku['associateSku'] = lcb[0]['encrypted_sku']
                cb_sku['lazada'] = self.pfh_sku_adpter(cb_sku) or False
                # if have been upload to lazada save it.
                cb_sku.pop('_id', None)
                self.mongo.lazada_sku.update({'sku': cb_sku['sku']},
                                                  cb_sku, True, True)
        return True

    def complete_sku(self, sku):
        self.mongo.pf_sku.update({'SKU': sku}, {'$set': {'lazada': 1}},
                                 multi=True)

    def clean_title_1(self):
        pfh_info = self.pfh_info
        string1 = pfh_info['CnProductName']
        string2 = pfh_info['ProductName']
        match = SequenceMatcher(None, string1, string2).find_longest_match(0, len(string1), 0, len(string2))
        name = string2.replace(string2[match.b:match.b+match.size], " ").strip()
        name = name.replace('Nickle', ' Nickle')
        name = name.replace('Earrings', ' Earrings')
        name = name.replace('New', ' New')
        name = name.replace('18K', ' 18K')
        cname = self.mongo.category.find_one({"ID": pfh_info['CategoryID']}).get('EnName')
        pfh_info['category_name'] = cname
        clean_title = " ".join([self.get_promotion_word(),
                               cname, name])
        clean_title = clean_title.replace('  ', ' ')
        return clean_title.lower().title()

    def get_trans_name(self, name, target="zh_CN"):
        url = "https://translation.googleapis.com/language/translate/v2?key=AIzaSyBgivFlsgQIUTSC2Q8-YF1yVqdRZYCdZsw"
        data = {'format': 'text',
                 'q': name,
                 'source': 'zh_CN',
                 'format': 'html',
                 'target': target}

        c = requests.post(url, data=data)
        cnr = json.loads(c.text)
        try:
            name = cnr['data']['translations'][0]['translatedText']
        except:
            pass
        return name

    def get_clean_title(self):
        pfh_info = self.pfh_info
        clean_title = pfh_info['ProductName'].split(" ")
        clean_title = clean_title[0] if len(clean_title[-1]) <= len(clean_title[0]) else clean_title[-1]
        clean_title = self.get_trans_name(clean_title, "en")
     
        cname = self.get_category_name(cid)
        if cname:
            cname = cname.replace("&", ' ')
            cname = cname.split(" / ")
            clean_title = cname[0].strip() + " " \
                + cname[-1].strip().replace('?', '') + " " + clean_title
            clean_title = re.sub(' +', ' ', clean_title).lower().title() 
        return clean_title.replace("&", " ")[:255]


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

        return random.choice(words)

    def get_short_desc(self):
        pfh_info = self.pfh_info
        sdesc = "<ul><li><strong>Its main color is %s!</strong></li><li>" \
            % pfh_info['color']

        sdesc += re.sub("<li>$", "", '</li><li>'.join(
            pfh_info['ProductSpecification'].split(';')))

        sdesc += '</ul>'
        return sdesc

    def get_color_size(self):
        sku_spec = self.pfh_info['SKUSpecification'].lower()
        sku_spec_list = sku_spec.split(";")
        pre_color = ""

        color, size = self.adapt_color('Multicolor'), None

        if 'metal color' in sku_spec:
            pre_color = 'metal color'
        else:
            pre_color = 'color'

        for spec in sku_spec_list:

            if pre_color in spec:
                color = self.adapt_color(spec.split(":")[-1])

            if 'size' in spec:
                size = spec.split(":")[-1]
        return color, size

    def get_desc(self):
        pfh_info = self.pfh_info
        desc = '<p><img src="http://s.chaotiinfo.com/lazada_MY112E5.gif"><strong>Features:</strong></p>'
        desc += pfh_info['short_description']
        # bs = BeautifulSoup(pfh_info.get('ProductDescription', ''), "lxml")
        # for img in bs.find_all('img'):
        #     img['src'] = 'http://omuczm3im.bkt.gdipper.com/%s' % img['src'].split('com/')[-1]
        #     img['src'] = self.upload_image(img['src'])
        #     desc += str(img)
        return desc

    def get_parent_cid(self, cid):
        cids = self.mongo.category.find({"ID": cid})
        for ids in cids:
            return ids.get('ParentID', 0)

    def get_category_id(self):
        pfh_info = self.pfh_info
        cmap = {"232-men": "8706",
                "232-women": "8700",
                "232-men-women": "8700",
                "263-men-women": "8709",
                "242-men": "11364",
                "242-women": "11317",
                "242-men-women": "11317",
                "245-boy": "8637",
                "245-girl": "8636",
                "245-men": "8633",
                "245-women": "8630",
                "245-men-women": "8630",
                "210-women": "8651",
                "210-men-women": "8651",
                "201-men": "8687",
                "201-women": "8663",
                "201-men-women": "8663",
                "205-men": "8684",
                "205-women": "8656",
                "205-men-women": "8656",
                "251-men-women": "8633",
                "204-women": "8665",
                "204-men-women": "8665",
                "211-women": "8653",
                "211-men-women": "8653",
                "248-men-women": "8633",
                "202-men": "8686",
                "202-men-women": "8686",
                "212-women": "8652",
                "212-men-women": "8652",
                "213-women": "8654",
                "213-men-women": "8654",
                "207-men": "8685",
                "207-women": "8642",
                "207-men-women": "8642",
                "208-women": "8643",
                "208-men-women": "8643",
                "241-men-women": "1830",
                "249-men-women": "3899",
                "220-women": "8670",
                "220-men-women": "8670",
                "216-men-women": "8656",
                "217-men-women": "8658",
                "218-men-women": "8656",
                "219-men-women": "8657",
                "301-men-women": "8709",
                "250-men-women": "4152",
                "243-men-women": "1830"}

        key1 = pfh_info['CategoryID']
        key2 = "men-women"
        check_string = pfh_info['ProductSpecification']
        if re.findall(r"wom[ae]n", check_string, re.I):
            key2 = 'women'
        elif re.findall(r"m[ae]n", check_string, re.I):
            key2 = 'men'
        elif re.findall(r"boy", check_string, re.I):
            key2 = 'boy'
        elif re.findall(r"girl", check_string, re.I):
            key2 = 'girl'

        key = "%s-%s" % (key1, key2)
        if not cmap.get(key):
            key = "%s-men-women" % key1

        if not cmap.get(key):
            key1 = self.get_parent_cid(key1)
            key = "%s-%s" % (key1, key2)
        return cmap.get(key)

    def process_pfh_info(self, pfh_info):
        self.pfh_info = pfh_info
        pfh_info['encrypted_sku'] = 'CM02-%s' % pfh_info['SKU']
        pfh_info['sku'] = pfh_info['SKU']
        pfh_info['category'] = self.get_category_id()
        if not pfh_info['category']:
            return
        pfh_info['color'], pfh_info['size'] = self.get_color_size()
        pfh_info['name'] = html.escape(self.clean_title())
        pfh_info['title'] = pfh_info['name']
        pfh_info['short_description'] = self.get_short_desc()
        pfh_info['description'] = html.escape(self.get_desc())
        pfh_info['brand'] = 'OEM'
        pfh_info['package_length'] = '15'
        pfh_info['package_height'] = '10'
        pfh_info['package_width'] = '10'
        pfh_info['package_content'] = '1 x %s' % pfh_info['category_name'].replace('&', 'and')
        pfh_info['price'] = round((float(pfh_info['CostPrice']) + 5)/7)
        pfh_info['ship_weight'] = round((float(pfh_info['Weight']) + 10)/1000,
                                        2)
        pfh_info['quantity'] = int(pfh_info['Stock']) or 66
        return pfh_info

    def pfh_sku_adpter(self, pfh_sku):
        pfh_sku["short_description"] = html.escape(pfh_sku['short_description'])
        product_schema = etree.XML("""<Request>
            <Product>
                <PrimaryCategory>{category}</PrimaryCategory>
                <SPUId></SPUId>
                <AssociatedSku>{associateSku}</AssociatedSku>
                <Attributes>
                    <name>{name}</name>
                    <name_ms>{name}</name_ms>
                    <color_family>{color}</color_family>
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
        """.format(**pfh_sku))
        # sku add
        # package content
        pfh_sku['special_price'] = get_special_price(pfh_sku['price'],
                                                    pfh_sku['ship_weight'], 9, level='pfh')
        pfh_sku['price'] = get_sale_price(pfh_sku['special_price'])
        start_date = arrow.now()
        pfh_sku['special_from_date'] = start_date.strftime("%Y-%m-%d")
        pfh_sku['special_to_date'] = start_date.replace(days=+365
                                                       ).strftime("%Y-%m-%d")
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
            </Sku>""".format(**pfh_sku))

        # extra SKU attrs
        extra_attr_str = get_extra_attrs(pfh_sku['category'])
        if 'ring_size' in extra_attr_str:
            if pfh_sku['size'] and pfh_sku['size'].isdigit():
                sku_size = pfh_sku['size']
            else:
                sku_size = 'Not Specified'
                # do not associated product if no size
                self.remove_elements_by_tag(product_schema, "AssociatedSku")

            extra_attr_str = extra_attr_str.format(size=sku_size)

        elif 'size' in extra_attr_str:
            if pfh_sku['size']:
                format_size = re.sub('2', 'X', pfh_sku['size']).upper()

                if format_size in self.get_size():
                    sku_size = 'Int:'+ format_size
                else:
                    pfh_sku['title'] = pfh_sku['title'] + "(Size:%s)" % pfh_sku['size'].replace("&", "and")
                    product_schema.xpath("//name")[0].text = pfh_sku['title']
                    sku_size = "Int: One size"
                    # do not associated product if no size
                    self.remove_elements_by_tag(product_schema, "AssociatedSku")

            else:
                sku_size = 'Not Specified'
                self.remove_elements_by_tag(product_schema, "AssociatedSku")

            extra_attr_str = extra_attr_str.format(size=sku_size)

        extra_attr_element = etree.XML(extra_attr_str)
        for eae in extra_attr_element.getchildren():
            if 'size' in eae.tag:
                product_sku.append(eae)
            else:
                product_schema.xpath("//Attributes")[0].append(eae)

        # image
        image_srcs = list(set(pfh_sku['SKUImages'].split(';')[:8]))
        for image_src in image_srcs[1:]:
            # image_src = 'http://omuczm3im.bkt.gdipper.com/%s' % image_src.split('com/')[-1]
            image_src = image_src.replace('/img', '/cdnimg')
            print(image_src)
            print(requests.get(image_src))
            image_src = self.upload_image(image_src, strict=True)
            if not image_src:
                continue
            e_image_src = etree.Element("Image")
            e_image_src.text = image_src
            product_sku.find("Images").append(e_image_src)
        product_schema.xpath("//Skus")[0].append(product_sku)
        print(etree.tostring(product_schema))
        result = self._post("CreateProduct",
                            data=etree.tostring(product_schema))
        if result:
            return True
        raise("Something need adjust")

    def get_pfh_product(self):
        i = 377
        j = 377
        while i <= j:
            url = "http://apiv2.pfhoo.com/productlist/?page=%s" % i
            print("start to get url: %s" % url)
            p = requests.get(url)
            pinfo = json.loads(p.text)
            j = int(pinfo['PageCount'])
            print(len(pinfo['Products']))
            mongo.pf_sku_new.insert_many(pinfo["Products"])
            i += 1


if __name__ == '__main__':
    site = {
        "api_key": b'U_Oobajpv6G6B4wIgrq349_ARwJ6Z9lFSHZqm705nEiDv6fP-fLSgkV2',
        "user_id": "citi@lazada.my",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "accountId": "MY112E5"}

    p = PfhooLazada(**site)
    while True:
        try:
            p.upload_pfh()
        except:
            with open('%s.log' % site['accountId'], 'a') as f:
                traceback.print_exc(file=f)
                traceback.print_exc()
