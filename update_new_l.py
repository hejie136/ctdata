from lazada_other_site import LazadaOtherSite
import arrow
site = {"api_key": b'U_Oobajpv6G6B4wIgrq349_ARwJ6Z9lFSHZqm705nEiDv6fP-fLSgkV2',
        "user_id": "citi@lazada.my",
        "url": "https://api.sellercenter.%s/" % "lazada.com.my",
        "accountId": "MY112E5"}

l = LazadaOtherSite(**site)

update_before = arrow.Arrow(2017, 3, 16).floor('hour')
# update_before = arrow.now().floor('hour')
product = l.get_product(offset=90, limit=100,
                        update_before=update_before,
                        status='all')
product_info = product['Products']

skus = [s['Skus'] for s in product_info]
for sk in skus:
    for d in sk:
        l.adjust_price_quantity(d['SellerSku'])
