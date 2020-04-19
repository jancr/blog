## Inspiration

This is a simple blog adapted from
[How to make a Flask blog in one hour or less](https://charlesleifer.com/blog/how-to-make-a-flask-blog-in-one-hour-or-less/)

## For this to work

make a file in blog/secret.py and set `SECRET_KEY` to a long string

```
SECRET_KEY = 'shhh, secret!'
```

TODO: better security!

## Check that it works
<!-- TODO: make virtual enviroment -->


1. clone and go to the blog folder
  * `git clone https://github.com/jancr/blog blog`
  * `cd blog/blog`
  <!-- *  TODO: activate virtual environment -->
  *  TODO: install dependencies
2. Run the development server 
  * `python app.py --devel`
3. Add the test posts to the development database
  * `python blog-post.py --deploy --devel`
  <!-- * `python blog-post.py 1 --devel` -->
  <!-- * `python blog-post.py 2 --devel` -->

## Run as real blog
1. clone the repo
  * `git clone https://github.com/jancr/blog blog`
2. clone the posts 
  * `cd blog/blog/static`
  * TODO does this work?: `git clone https://github.com/jancr/blog-posts blog-posts`


## Other TODO:
no particular order

* `requirements.txt`
* create first blog post!
* `about.html`
* chronological listing of posts
