from temp_script import ChinaBrandResource
import arrow
import collections
import pymongo
from lazada import Lazada


db = pymongo.MongoClient("mongodb://localhost:55088/").cb_info


def get_stock_info():
    cb = ChinaBrandResource()
    # update per 12 hours
    now_time = arrow.now().timestamp
    check_time = now_time - 60*60*24*5
    all_info = db.all_cb_sku.find({"update_time": {"$lt": check_time}}).limit(50)
    # all_info = db.all_cb_sku.find({"update_time": None}).limit(50)
    skus = [p["sku"] for p in all_info]
    # skus = ['197541105', '206386701', '178890601', '206425105']
    if not skus:
        return False
    # update datatime
    db.all_cb_sku.update_many({"sku": {"$in": skus}},
                              {"$set": {"update_time": now_time}})
    new_stock = cb.get_stock_info(skus)
    print(new_stock)
    if not new_stock:
        return {sku: 0 for sku in skus}
    pre_stock = collections.defaultdict(int)
    for s in new_stock:
        pre_stock[s['goods_sn']] += int(s.get('goods_number', -5))
    all_stock = {sku: pre_stock.get(sku, -5) for sku in skus}
    # update datatime
    for su, sn in all_stock.items():
        db.all_cb_sku.update({"sku": su},
                             {"$set": {"quantity_new": sn, "update_time": now_time}})
    return all_stock


def update_lazada(lzd, pre, stock):
    for sku, sn in stock.items():
        # status if sn != 0 else "false"
        print("\n------------%s----------\n" % sku)
        if sn == -5:
           lzd.remove_product([pre+sku])
       # lzd.change_status(pre+sku, status)
        # db.all_cb_sku.update_many({"sku":sku}, {"$set":{lzd.get_account_id():0}})

def remove_lazada(lzd, pre, stock):
    sku = list(stock.keys())
    print("\n------------%s----------\n" % sku)
    lzd.remove_product([pre+s for s in sku])
    # db.all_cb_sku.update_many({"sku":{"$in":sku}}, {"$set":{"ph":1}})
        # lzd.change_status(pre+sku, status)
        # db.all_cb_sku.update_many({"sku":sku}, {"$set":{lzd.get_account_id():0}})


def get_sku_info(site):
    """
     stock status
     sstatus: -1 库存不足
     sstatus: -2 l下架
     sstatus: 1 库存正常
     sstatus: 2 yiuhjx
    """
    # all_info = db.all_cb_sku.find({"cid": "1348", "lazada_forbid":None}).limit(10)
    all_info = db.all_cb_sku.find({"quantity_new": -5}).limit(10)
    return {s['sku']: s.get('quantity_new', 0) for s in all_info}

def batch_update_status(sites, status=0):
    while True:
        # try:
            stock = get_sku_info(sites[0])
            if not stock:
                print("finish update, stop!!!")
                return
            for site in sites:
                print(site)
                l = Lazada(**site)
                # update_lazada(l, site.get("pre", "RA01-"), stock)
                remove_lazada(l, site.get("pre", "RA01-"), stock)
            db.all_cb_sku.update_many({"sku": {"$in": list(stock.keys())}},
                              {"$set": {"quantity_new": -10}})

       #  except:
       #      print("Something wrong!!!!\n\n")
       #      continue

def init_index(sites):
    for site in sites:
        print(db.all_cb_sku.update_many({}, {"$set":{site.get("accountId"):1}}, True))
        db.all_cb_sku.create_index([("sku", 1), (site.get("accountId"), 1)])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    #-db DATABSE -u USERNAME -p PASSWORD -size 20
    parser.add_argument("-s", "--site", help="lazada site number")

    args = parser.parse_args()

    print( "now process site:{}\n\n ".format(args.site))
    site_info = [{
        "api_key": b'6946b89c23d2cabbf3be1b5f63b1d41a3de990da',
        "user_id": "zchv@msn.com",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "accountId": "MY10WA4"
    }, {
        "api_key": b'i50qSobssxxZEl1vyjE2dbKzd5XQ4xfE_9MvJLl_Vuvm8URak4CoHH6z',
        "user_id": "ct@lazada.ph",
        "url": "https://api.sellercenter.%s/" % "lazada.com.ph",
        "pre": "RA01-",
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
    }, {"api_key": b'U_Oobajpv6G6B4wIgrq349_ARwJ6Z9lFSHZqm705nEiDv6fP-fLSgkV2',
        "user_id": "citi@ctdata.my",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "name": "citimall",
        "pre" : "CM01-",
        "accountId": "MY112E5"
    }, {
        "api_key": b'QGz5Smumqy3bxUZzoWf-OIjTH_eo_q_qbpOT6Cjer2TLdVm-ARViZD3g',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.com.ph",
        "pre" : "CM01-",
        "accountId": "PH10OU4"},
    {
        "api_key": b'N5bfnEcFk6GCgiZRIPJi38jlqHSxYbocHgWKFcMM-04bhg5TXQADsADF',
        "user_id": "billaeon@qq.com",
        "pre" : "CM01-",
        "url": "https://api.sellercenter.%s/" % "lazada.sg",
        "accountId": "SG10OCO"
    }, {
        "api_key": b'54oyaJGpM2Z8CIUsu4JTvm3OLETUjRMQbZ_JOy-bxkOQKl0h5Rn1CPBy',
        "user_id": "billaeon@qq.com",
        "pre" : "CM01-",
        "url": "https://api.sellercenter.%s/" % "lazada.co.th",
        "accountId": "TH1157F"
    }, {
        "api_key": b'EzIAOY-49evRsMxzP71d-2yAWkCcp1c0m7t75DGF0FV1iWxqzh4OR-2o',
        "user_id": "billaeon@qq.com",
        "pre" : "CM01-",
        "url": "https://api.sellercenter.%s/" % "lazada.co.id",
        "accountId": "ID120DF"
    }]
    # init_index(site_info)
    # batch_update_status(site_info)
    while get_stock_info():
        print("run normal")
