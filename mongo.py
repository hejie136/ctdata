import pymongo
mongo = pymongo.MongoClient("mongodb://localhost:27017/").cb_info

for cb_sku in mongo.all_cb_sku.find()[10400:]:
   # print(cb_sku['sku'], cb_sku.get("package_size"))
   clean_sp = {}
   try:
       psize = cb_sku.get("package_size").split('cm')[0].split('x')
       clean_sp['package_height'] = psize[0].strip()
       clean_sp['package_width'] = psize[1].strip()
       clean_sp['package_length'] = psize[2].strip()
   except:
       clean_sp['package_height'] = 1
       clean_sp['package_width'] = 1
       clean_sp['package_length'] = 1
   mongo.all_cb_sku.update({"sku": cb_sku['sku']}, {"$set":clean_sp})
   # print(clean_sp)
   # print(mongo.all_cb_sku.find_one({"sku": cb_sku['sku']}))

