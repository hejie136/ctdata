import pymongo
import traceback
import os
mongo = pymongo.MongoClient("mongodb://localhost:27017/").pf_info
urls = mongo.pf_img.find()
for img in urls:
    try:
        url = img['src']
        os.system("qshell fetch %s pfhoo %s" % (url, url.split('com/')[-1]))

    except:
        with open('log.log', 'a') as f:
            traceback.print_exc(file=f)
            traceback.print_exc()
