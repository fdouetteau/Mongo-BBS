
from pymongo import Connection
from bson.objectid import ObjectId
import bson.json_util
from bottle import run, debug, static_file, request, response, Bottle
from json import dumps as json_dumps
import os

class MyJSONPlugin(object):
    "JSON Serialization Plugin for Bottle that automatically serializes MongoDB/BSON Values  "
    name = 'myjson'
    api  = 2

    def normalize_id(self, obj):
        if isinstance(obj, dict):
            if "_id" in obj: 
                obj["id"] = str(obj["_id"])
                del obj["_id"]
        if isinstance(obj, list):
            for a in obj: 
                self.normalize_id(a)

    def apply(self, callback, context):
        dumps = json_dumps
        if not dumps: return callback
        def wrapper(*a, **ka):
            rv = callback(*a, **ka)
            if isinstance(rv, dict) or isinstance(rv, list):
                #Attempt to serialize, raises exception on failure
                self.normalize_id(rv)
                json_response = dumps(rv, default=bson.json_util.default)
                #Set content type only if serialization succesful
                response.content_type = 'application/json'
                return json_response
            return rv
        return wrapper

app = Bottle(autojson=False)
app.install(MyJSONPlugin())

server_root = None
@app.route('/<filename:re:.*\.(css|js|ico|html)>')
def server_static(filename):
    global server_root 
    if not server_root: 
        server_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'public')
    return static_file(filename, root=server_root)

mongo_db = None
def get_mongo():
    "Retrieve the mongo instance from the environment"
    global mongo_db
    if mongo_db: 
        return mongo_db
    if "MONGOLAB_URI" in os.environ: 
        uri = os.environ["MONGOLAB_URI"]
    else: 
        raise Exception("MONGOLAB_URI env required")
    connection = Connection(uri)
    ## Some bug in the driver requires to reauthenticate
    for dbname,(login,p) in connection._Connection__auth_credentials.iteritems():
        db = connection[dbname]
        db.authenticate(login,p)
        return db

@app.route("/posts", method="GET")
def posts_list():
    db = get_mongo()
    return [a for a in db['posts'].find()]

@app.route("/posts", method="POST")
def posts_create(): 
    db = get_mongo()
    print request.environ
    print request.json
    return {"_id": db['posts'].insert({"text":request.json["text"]}), "text": request.json["text"]}
    
@app.route("/posts/:_id", method="PUT")
def posts_update(_id):
    db = get_mongo()
    db['posts'].update({"_id":ObjectId(request.json["id"])}, {"$set": {"text": request.json["text"] } })

@app.route("/posts/:_id", method="DELETE")
def post(_id):
    db = get_mongo()
    db['posts'].remove({_id:ObjectId(request.json["id"])})
    
if __name__ == "__main__": 
    if os.environ.get("DEV"): 
        debug(True)
        run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)
    else:
        run(app=app, host="0.0.0.0", port=os.environ.get("PORT"))
        