from lazada import Lazada
import pymongo
import traceback
import arrow

class LazadaProduct(Lazada):
    def remove_all_product(self):
        db = pymongo.MongoClient().lazada
        rm_sku = db.all_lazada_sku.find_and_modify({"lazada_on": 110}, {"$set": {"lazada_on":-1}})
        skus = [s['SellerSku'] for s in rm_sku['Skus']]
        # split to sub list one inlucde n element
        print(skus)
        self.remove_product(skus)


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
        "api_key": 'i50qSobssxxZEl1vyjE2dbKzd5XQ4xfE_9MvJLl_Vuvm8URak4CoHH6z',
        "user_id": "ct@lazada.ph",
        "url": "https://api.sellercenter.%s/" % "lazada.com.ph",
        "accountId": "PH10KNV"},
    {
        "api_key": 'TrwkupHsatgLSJ29-v0GyQm_XFif-nzQ6o9K1HqU5M5RQGq4ZPTjdG7m',
        "user_id": "ct@lazada.sg",
        "url": "https://api.sellercenter.%s/" % "lazada.sg",
        "accountId": "SG10K9L"
    }, {
        "api_key": 'faiiWFTyeNygj32Yv5e1YKWhASk4ce1Y9PyWsSPEpd4s5z_NgUzwwmdr',
        "user_id": "ct@lazada.th",
        "url": "https://api.sellercenter.%s/" % "lazada.co.th",
        "accountId": "TH10XO0"
    }, {
        "api_key": 'g7km1MXol8AtXMwRBNikP0fa8VROYWR_h6FNp_PZxFpyVzHfWYcfgv_D',
        "user_id": "ct@lazada.id",
        "url": "https://api.sellercenter.%s/" % "lazada.co.id",
        "accountId": "ID11MKJ"
    }, {"api_key": 'U_Oobajpv6G6B4wIgrq349_ARwJ6Z9lFSHZqm705nEiDv6fP-fLSgkV2',
        "user_id": "citi@ctdata.my",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "name": "citimall",
        "accountId": "MY112E5"
    }, {
        "api_key": 'QGz5Smumqy3bxUZzoWf-OIjTH_eo_q_qbpOT6Cjer2TLdVm-ARViZD3g',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.com.ph",
        "accountId": "PH10OU4"},
    {
        "api_key": 'N5bfnEcFk6GCgiZRIPJi38jlqHSxYbocHgWKFcMM-04bhg5TXQADsADF',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.sg",
        "accountId": "SG10OCO"
    }, {
        "api_key": '54oyaJGpM2Z8CIUsu4JTvm3OLETUjRMQbZ_JOy-bxkOQKl0h5Rn1CPBy',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.co.th",
        "accountId": "TH1157F"
    }, {
        "api_key": 'EzIAOY-49evRsMxzP71d-2yAWkCcp1c0m7t75DGF0FV1iWxqzh4OR-2o',
        "user_id": "billaeon@qq.com",
        "url": "https://api.sellercenter.%s/" % "lazada.co.id",
        "accountId": "ID120DF"
    }]
    # START REMOVE RPODUCT#
    site = site_info[int(args.site)]
    l = LazadaProduct(**site)
    db = pymongo.MongoClient().lazada
    offset = 0
    pre_info = None
    while True:
        # 注意这里，是删除其它产品时用的。
        l.remove_all_product()
    #    try:
    #        #jupdate_before = arrow.Arrow(2017, 8, 27).floor('hour')
    #        # 注意这里，是删除其它产品时用的。
    #         l.remove_all_product()
    #        # continue
    #         ##  STOP ####
    #         print(site)
    #         update_before = arrow.now().floor('hour')
    #         product = l.get_product(offset=offset, limit=100,
    #                                 update_before=update_before,
    #                                 status='all',
    #                                 # OrderBy='sku',
    #                                 # CreatedAfter = "2017-07-01T10:00:00+08:00"
    #                                 # CreatedBefore = "2017-04-22T10:00:00+08:00"
    #                                 )
    #         product_info = product['Products']
    #         # db.all_lazada_sku.insert_many(product_info, ordered=False)
    #         for pi in product_info:
    #             if not pi['Skus']:
    #                 continue
    #             db.all_lazada_sku.update_one({'Skus.SellerSku': pi['Skus'][0]['SellerSku']}, {'$set': pi}, upsert=True)
    #         if pre_info and product_info and pre_info[0] == product_info[0]:
    #             print(offset, pre_info)
    #             break
    #         pre_info = product_info

    #         # continue
    #         # l.update_product(product_info, pre_remove, remove=True)
    #         # l.adjust_price_quantity(product_info)
    #         # l.update_title(product_info)
    #         if len(product_info) <30 and offset == 0:
    #             break
    #         if len(product_info) < 20 and offset > 0:
    #             offset = 0
    #             continue

    #         offset += 100
    #     except:
    #         with open('%s.log' % site['accountId'], 'a') as f:
    #             traceback.print_exc(file=f)
    #             traceback.print_exc()
    #         break
    # print('done !!')
