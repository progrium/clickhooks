#!/usr/bin/env python


import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import urlfetch
import time, urllib

def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"): 
    return ((num == 0) and  "0" ) or (baseN(num // b, b).lstrip("0") + numerals[num % b])

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            logout_url = users.create_logout_url("/")
            hooks = ClickHook.all().filter('user =', user)
        else:
            login_url = users.create_login_url('/')
        self.response.out.write(template.render('templates/main.html', locals()))
    
    def post(self):
        if self.request.POST.get('name', None):
            h = ClickHook.all().filter('name =', self.request.POST['name']).get()
            h.delete()
        else:
            h = ClickHook(hook_url=self.request.POST['hook_url'],redirect_url=self.request.POST['redirect_url'])
            h.put()
        self.redirect('/')

class RedirectHandler(webapp.RequestHandler):
    def get(self):
        if self.request.path[-1] == '/':
            self.redirect(self.request.path[:-1])
        name = self.request.path.replace('/', '')
        hook = ClickHook.all().filter('name =', name).get()
        params = {'url': hook.redirect_url, '_url': hook.hook_url}
        urlfetch.fetch(url='http://hookah.webhooks.org', payload=urllib.urlencode(params), method='POST')
        self.redirect(hook.redirect_url)

class ClickHook(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    hook_url = db.StringProperty(required=True)
    redirect_url = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
    def __init__(self, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', baseN(abs(hash(time.time())), 36))
        super(ClickHook, self).__init__(*args, **kwargs)
    
    def __str__(self):
        return "http://www.clickhooks.com/%s" % self.name

def main():
  application = webapp.WSGIApplication([('/', MainHandler), ('/.*', RedirectHandler)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
