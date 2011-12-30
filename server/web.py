
from bottle import run, debug, static_file, request, response, Bottle
from json import dumps as json_dumps
import os

## MongoPlugin
from bottle import PluginError
from pymongo import Connection
from bson.objectid import ObjectId
import bson.json_util
from bottle import JSONPlugin
import inspect

class MongoPlugin(object):
    """
    Mongo Plugin for Bottle
    Creates a mongo database 
    app = bottle.Bottle()
    plugin = bottle.ext.mongo.MongoPlugin(uri="...", json_mongo=True)
    app.install(plugin)

    @app.route('/show/:item')
    def show(item, mongodb):
        doc = mongodb['items'].find({item:"item")})
        return doc
    """
    api  = 2

    def __init__(self, uri, keyword='mongodb', json_mongo=False):
        self.uri = uri
        self.keyword = keyword
        self.json_mongo = json_mongo
        
    def normalize_object(self, obj):
        "Normalize mongo object for json serialization"
        if isinstance(obj, dict):
            if "_id" in obj: 
                obj["id"] = str(obj["_id"])
                del obj["_id"]
        if isinstance(obj, list):
            for a in obj: 
                self.normalize_id(a)

    def setup(self,app):
        for other in app.plugins:
            if not isinstance(other,MongoPlugin): continue
            if other.keyword == self.keyword:
                raise PluginError("Found another redis plugin with "\
                        "conflicting settings (non-unique keyword).")
                        
        # Remove builtin JSON Plugin
        if self.json_mongo:
            for other in app.plugins:
                if isinstance(other, JSONPlugin): 
                    app.uninstall(other)
                    return                         

    def apply(self, callback, context):
        dumps = json_dumps
        if not dumps: return callback
        
        args = inspect.getargspec(context['callback'])[0]        
        
        def wrapper(*a, **ka):
            if self.keyword in args:
                ka[self.keyword] = get_mongo()
            rv = callback(*a, **ka)
            if self.json_mongo:  # Override builtin bottle JSON->String serializer  
                if isinstance(rv, dict) or isinstance(rv, list):
                    self.normalize_object(rv)
                    json_response = dumps(rv, default=bson.json_util.default)
                    response.content_type = 'application/json'
                    return json_response
            return rv
        return wrapper

app = Bottle(autojson=False)
app.install(MongoPlugin(uri=os.environ["MONGOLAB_URI"]))

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
def posts_list(mongodb):
    return [a for a in mongodb['posts'].find()]

@app.route("/posts", method="POST")
def posts_create(mongodb): 
    print request.environ
    print request.json
    return {"_id": mongodb['posts'].insert({"text":request.json["text"]}), "text": request.json["text"]}
    
@app.route("/posts/:_id", method="PUT")
def posts_update(_id, mongodb):
    mongodb['posts'].update({"_id":ObjectId(request.json["id"])}, {"$set": {"text": request.json["text"] } })

@app.route("/posts/:_id", method="DELETE")
def post(_id, mongodb):
    mongodb['posts'].remove({_id:ObjectId(request.json["id"])})
    
if __name__ == "__main__": 
    if os.environ.get("DEV"): 
        debug(True)
        run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)
    else:
        run(app=app, host="0.0.0.0", port=os.environ.get("PORT"))
        