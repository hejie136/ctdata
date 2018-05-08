import requests
import json
import xlsxwriter
import arrow


class AiYouPost():
    def __init__(self):
        self.login_data = {"userName": "18665848761",
                           "password": "ctdata@520post",
                           "remember": "on",
                           "slideCode": ""}
        self.base_url = "http://www.520post.com"
        self.rq = requests.Session()
        self.login()

    def login(self):
        url = self.base_url + "/cust/login"
        self.rq.post(url, self.login_data)

    def product_list(self):
        url = self.base_url + "/commodity/commodityListData"
        data = {"sortName": "col1",
                "sortType": "DESC",
                "_search": "false",
                "nd": "1493188229531",
                "rows": 20,
                "page": 1,
                "sidx": "",
                "sord": "asc"}
        result = self.rq.post(url, data)
        rdata = json.loads(result.text)
        return rdata

    def get_cn_name(self, name):
        url = "https://translation.googleapis.com/language/translate/v2?key=AIzaSyDsuP9pFBzCFt3feSzO2KNs4tD9wsViB_U"
        data = {'format': 'text',
                 'q': name,
                 'source': 'en',
                 'target': 'zh_CN'}

        c = requests.post(url, data=data)

        cnr = json.loads(c.text)
        try:
            return cnr['data']['translations'][0]['translatedText']
        except:
            return name

    def save_product_to_xlsx(self, skus):
        keys = ['*自定义商品编码',
                '*商品中文名称',
                '*商品分类',
                '*包装方式',
                '*成本',
                '重量（g)',
                '长（cm)',
                '宽(cm）',
                '高（cm）',
                '*敏感属性',
                '*质检级别',
                '商品虚拟编码（多个使用英文;区分）',
                '质检要求',
                '*商品图片URL']
        workbook = xlsxwriter.Workbook('product.xlsx')
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0
        for k in keys:
            worksheet.write(row, col, k)
            col += 1

        for sku in skus:
            col = 0
            row += 1
            row_info = [sku['Sku'], self.get_cn_name(sku['Name']), '其他',
                        '气泡袋', int(sku['PaidPrice'] * 1.5),
                        '', '', '', '', '无', '5%',
                        sku['Sku'], '',
                        sku['productMainImage'].replace('-catalog.', '.')]

            for r in row_info:
                worksheet.write(row, col, r)
                col += 1
        workbook.close()

    def upload_product(self):
        url = self.base_url + "/commodity/importExcel"
        files = {'upfile': ('product.xlsx', open('product.xlsx', 'rb'),
                          'application/vnd.ms-excel', {'Expires': '0'})}
        result = self.rq.post(url=url, files=files)
        print(result.text)
        if json.loads(result.text).get("return_code") == 0:
            return True
        else:
            return False

    def back_orders(self):
        url = self.base_url + "/deliveryorder/getOrderList"
        data = {"custId": 7276,
                "startDate": "",
                "endDate": "",
                "condition": "",
                "orderStatus": 1,
                "type": "exception",
                "rows": 100,
                "page": 1,
                "sidx": "",
                "sord": "asc"}
        c = self.rq.post(url, data=data)
        orders = json.loads(c.text)
        for sn in orders['resultList']:
            c=self.rq.post(url="http://www.520post.com/deliveryorder/deliverAgainGoods",
                           data={"orderCode":sn['orderCode']})
            print(arrow.get(sn['createdDate']/1000))
            print(c.text)

    def get_all_skus_from_order(self, lazada):
        createAfter = str(arrow.now().replace(hours=-1).floor('hour'))
        orders = lazada.get_pending_orders(status="pending", createAfter=createAfter)
        all_orders = []
        for o in orders:
            oitems = lazada.get_order_items(o['OrderId'])
            oitems = oitems['OrderItems']
            all_orders.extend(oitems)

        if not all_orders:
            print("no need add product")
            return

        self.save_product_to_xlsx(all_orders)
        self.upload_product()
        return all_orders


if __name__ == "__main__":
    from lazada import Lazada

    site = {"api_key": b'U_Oobajpv6G6B4wIgrq349_ARwJ6Z9lFSHZqm705nEiDv6fP-fLSgkV2',
            "user_id": "citi@ctdata.my",
            "url": "https://api.sellercenter.%s/" % "lazada.com.my",
            "name": "citimall",
            "accountId": "MY112E5"
          }

    l = Lazada(**site)
    a = AiYouPost()
    a.get_all_skus_from_order(l)
    # a.upload_product()
