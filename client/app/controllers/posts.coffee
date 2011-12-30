Spine = require('spine')

Post = require("models/post")

class Posts extends Spine.Controller
    events: 
        "submit form": "create"
    elements:
        "form input" : "input" 
        ".list" : "postlist"
        
    constructor: ->
      super
      Post.bind 'refresh change', @render
      Post.fetch()

    render: =>
        items = Post.all()
        @postlist.empty()
        @postlist.append(require('views/posts')(item)) for item in items
        
    create: (e) ->
        e.preventDefault()
        Post.create(text: @input.val())
        @input.val("")
    
module.exports = Posts