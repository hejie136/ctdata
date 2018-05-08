from flask import Flask, jsonify
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper
import time
import pymongo


from lazada_other_site import LazadaOtherSite

app = Flask(__name__)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/lucas')
@crossdomain(origin='*')
def root():
    sku = request.args.get('sku')
    cu = request.args.get('cu')
    l = LazadaOtherSite()
    try:
        sku_info = l.get_price_quantity(sku, cucode=cu, ajax=True)
    except:
        sku_info = None

    if sku_info:
        keys = ['encrypted_sku', 'special_price', 'price', 'quantity']
        sku_info = {k: sku_info.get(k) for k in keys}
        res = {'status': 0, 'data': sku_info}
    else:
        res = {'status': -1, 'data': {}}
    time.sleep(3)
    return jsonify(res)

@app.route('/sleep')
@crossdomain(origin='*')
def fsleep():
    time.sleep(3)
    res = {"status": 0}
    return jsonify(res)


@app.route('/get_sku')
@crossdomain(origin='*')
def get_sku():
    sku = request.args.get('sku')
    if "RA01" in sku:
        py = pymongo.MongoClient("mongodb://localhost:55088/").cb_info
        result = py.all_cb_sku.find_one({"sku": sku.split("-")[-1]})
        return "<h1>{sku}-<a target='_blank' href='{url}'>{title}</a></h1><ul><li>价格: {price}</li><li>尺寸: {size}</li><li>价格: {price}</li><li>重量：{ship_weight}</li></ul><image src='{original_img[0]}'/>".format(**result)
    else:
        opy = pymongo.MongoClient("mongodb://139.162.33.33/").cb_info
        result = opy.lazada.find_one({"associateSku":{"$regex":"%s*" % sku}})
        return "<h1>{associateSku}-<a target='_blank' href='{origin_url}'>{name}</a></h1><ul><li>规格: {skus}</li><li>重量：{ship_weight}</li></ul><image src='{images[0]}'/>".format(**result)

@app.route('/orders')
@crossdomain(origin='*')
def orders():
    py = pymongo.MongoClient("mongodb://localhost:27017/").cb_info
    result = py.order_result.find({"status":0})
    r = []
    for i in result:
        i.pop("_id", None)
        r.append(i)
    return jsonify(r)

@app.route('/wish/', methods=['POST'])
@crossdomain(origin='*')
def update_tags():
    py = pymongo.MongoClient("mongodb://localhost:27017/").cb_info
    json_data = request.get_json(force=True)
    print(json_data['data']['contest']['name'])
    py.ctags.insert(json_data)
    time.sleep(2)
    return jsonify({"status":True})


if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0', port=8188) #, ssl_context='adhoc')
