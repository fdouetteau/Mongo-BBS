Spine = require('spine')

class Post extends Spine.Model
  @configure 'Post', 'text'
  
  @extend Spine.Model.Ajax
  
module.exports = Post