from chinabrand_resource.lazada import Lazada
from chinabrand_resource.temp_script import ChinaBrandResource
site_info = [{
        "api_key": b'EKbjyyHIuV6ZC4sM5fKVLQSj17h1OT9jj7BA77FtW4DV6eMNWWPkqyyO',
        "user_id": "service@rolandarts.com",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "accountId": "MY10WA4"},
    {
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
    }]

for site in site_info:
    l = Lazada(**site)
    CB = ChinaBrandResource()
    country = site['accountId'][:2]
    ship_method = {'SG': 'SGGLS3', 'MY': 'MYGLSM', 'ID': 'IDGLSE',
                   'TH': 'THGLS', 'PH': 'PHGLSE'}.get(country, 'MYGLSM')
    print(country, ship_method)
    result = l.ready_to_ship(CB, country=country, ship_method = ship_method)
    if not result:
        print("no order till now")
        continue
    order_sn = [k['order_sn'] for k in result.values()]
    if len(order_sn) == 1:
        order_sn = order_sn[0]
    print(CB.pay_order(order_sn))
