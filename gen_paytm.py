import csv
from lazada_category import lazada_category
from temp_script import ChinaBrandResource
import traceback
from bs4 import BeautifulSoup
import html2text
import pymongo
import re
import functools


@functools.lru_cache()
def get_category_name(cid):
    cid = int(cid)                                                           
    lc = dict(lazada_category)                                               
    return lc.get(cid, "")


def get_clean_title(cb_sku, spec, cid):
        re.sub("%s |%s " % (cb_sku.get('goods_brand'), spec.get('model')), 
                "", cb_sku['title'], flags=re.I)
        clean_title = cb_sku['title']
        cname = get_category_name(cid)
        if cname:
            cname = cname.replace("&", ' ')
            cname = cname.split(" / ")
            clean_title = cname[0].strip() + " " \
                + cname[-1].strip().replace('?', '') + " " + clean_title
        clean_title = re.sub(' +', ' ', clean_title)
        return clean_title.strip().lower().title()


def get_clean_desc(desc):
    text = BeautifulSoup(desc, "lxml")
    [x.extract() for x in text.findAll('img')]
    return html2text.html2text(str(text)).replace("**", "")


def save_to_paytm(sku_info):
    CB = ChinaBrandResource()
    try:
        category = int(sku_info.get('lazada_cid', 99999))
    except:
        category = 99999
    lz_sku_spec = CB.get_sku_specification(sku_info['goods_desc'])
    p_sku = "CM01-" + sku_info['sku']
    p_name = get_clean_title(sku_info, lz_sku_spec, category)
    p_weight = float(sku_info['ship_weight'])
    p_price = round(177.3 * float(sku_info['price']) + 118.2+675.4 * p_weight 
                    + 101.3*int((p_weight/0.5)+0.5), 2)
    p_mrp = round(p_price/0.3)
    p_color = sku_info['color']
    p_size = sku_info['size']
    p_psku = p_sku[:-2]
    p_imgs = ",".join([img.replace("https://glodimg.chinabrands.com", "http://cbimg.chaotiinfo.com") for img in sku_info['original_img']])
    p_desc = get_clean_desc(sku_info['goods_desc'])
    p_rpi = '34'
    p_mdt = '12'
    # p_gender = "Women"

    return [p_sku, p_name, p_mrp, p_price, p_color, p_size, p_psku, 
            p_weight*1000, p_imgs, p_desc, p_rpi, p_mdt]
    

if __name__ == "__main__":
    py = pymongo.MongoClient("mongodb://mongo.server:55088/").cb_info
    category = "Automobiles & Motorcycles"
    while True:
        sku_info = py.all_cb_sku.find_and_modify({'paytm': None, "cat_id.0.0": category, 'status': 1, 
            "quantity_new": {"$ne": -5}}, {"$set": {"paytm":1}})
        # sku_info = py.all_cb_sku.find_one({"sku":"195963604"})
        if not sku_info: 
            break
        if float(sku_info['price']) > 50:
            print("price too hight stop")
            continue
        sku = sku_info.get('sku')
        try:
            print("Start upload URL %s" % str(sku))
            with open("CTDATA_paytm_product_%s.csv" % category, 'a') as f:
                spamwriter = csv.writer(f)
                p_info = save_to_paytm(sku_info)
                if p_info:
                    spamwriter.writerow(p_info)
            print(save_to_paytm(sku_info))
        except:
            with open('pay_tm_log.log', 'a') as f:
                # print("Error URL: %s-%s" % (row['cid'], row['sku']), file=f)
                traceback.print_exc(file=f)
                traceback.print_exc()
            print("Error URL %s" % str(sku))
            break
