
from bottle import run, debug, static_file, request, Bottle
import os
import bottle_mongo
from bson import ObjectId

app = Bottle(autojson=False)
app.install(bottle_mongo.MongoPlugin(uri=os.environ["MONGOLAB_URI"]))

server_root = None
@app.route('/<filename:re:.*\.(css|js|ico|html)>')
def server_static(filename):
    global server_root 
    if not server_root: 
        server_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'public')
    return static_file(filename, root=server_root)

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
        