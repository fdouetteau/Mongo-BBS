require('lib/setup')

Spine = require('spine')
Posts = require('controllers/posts')

class App extends Spine.Controller
  elements:
      ".test": "test"
      ".posts" : "posts"
  
  constructor: ->
    super
    @test.append(" Test test 5$")
    posts = new Posts(el:@posts)
    @test.append("After append")

module.exports = App
    
    
    
    
    
    
    
    
    
    
    
    
    
    



