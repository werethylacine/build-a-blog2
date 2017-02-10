#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def get_posts(limit, offset):
    entries_to_show = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC LIMIT {} OFFSET {}".format(limit, limit * offset))
    return entries_to_show

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Entry(db.Model):
    title = db.StringProperty(required = True)
    entry = db.TextProperty(required = True)
    author = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class BlogEntries(Handler):
    def render_front(self, page, title="", entry="", author="", error=""):
        if page <= 1:
            page = 1
        past_entries = get_posts(5, page - 1)
        need_next_link = True
        #need to fix this for edge case of 10, 15, 20 entries
        if len(list(past_entries)) < 5:
            need_next_link = False
        self.render("blog.html", page=page, need_next_link=need_next_link, title=title, entry=entry, error=error, past_entries=past_entries)

    def get(self):
        page = self.request.get("page")
        if page == '':
            page = 1
        self.render_front(int(page))

class NewPost(Handler):
    def render_front(self, title="", entry="", author="", error=""):
        #past_entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC LIMIT 5") #OFFSET
        self.render("form.html", title=title, entry=entry, author=author, error=error)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        entry = self.request.get("entry")
        author = self.request.get("author")

        if title and entry and author:
            e = Entry(title = title, entry = entry, author = author)
            e.put()
            self.redirect("/blog/" + str(e.key().id()))
        else:
            error = "we need a title, entry, and author!"
            self.render_front(title, entry, author, error)

class ViewPostHandler(Handler):
    def get(self, id):
        if id:
            this_entry = Entry.get_by_id(int(id))
            self.render("single_post.html", title=this_entry.title, entry=this_entry.entry, author=this_entry.author)
        else:
            self.redirect("/blog")

app = webapp2.WSGIApplication([
    ('/', BlogEntries),
    ('/blog', BlogEntries),
    ('/newpost', NewPost),
    webapp2.Route('/blog/<id:\d+>', ViewPostHandler),

], debug=True)
