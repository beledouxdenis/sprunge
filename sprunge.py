import datetime
import os
import random
import sys
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext import db

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pygments.lexers
from pygments import highlight
from pygments.formatters import HtmlFormatter


class Sprunge(db.Model):
    name = db.StringProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)


class Index(webapp.RequestHandler):

    u = 'http://pastesha.re'
    r = 'sprunge'

    def help(self, u, r):
        f = 'data:text/html,<form action="%s" method="POST"><textarea name="%s" cols="80" rows="24"></textarea><br><button type="submit">%s</button></form>' % (u, r, r)
        return """
<style> a { text-decoration: none } </style>
<pre>
sprunge(1)                          SPRUNGE                          sprunge(1)

NAME
    sprunge: command line pastebin.

SYNOPSIS
    &lt;command&gt; | curl -F '%s=&lt;-' %s

DESCRIPTION
    add <a href='http://pygments.org/docs/lexers/'>?&lt;lang&gt;</a> to resulting url for line numbers and syntax highlighting
    use <a href='%s'>this form</a> to paste from a browser

EXAMPLES
    ~$ cat bin/ching | curl -F '%s=&lt;-' %s
       %s/VZiY
    ~$ firefox %s/VZiY?py#n-7

SEE ALSO
    http://github.com/rupa/sprunge

</pre>""" % (r, u, f, r, u, u, u)

    def new_id(self):
        nid = ''
        symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        while len(nid) < 4:
            n = random.randint(0, 35)
            nid = nid + symbols[n:n + 1]
        return nid

    def get(self, got):
        if not got:
            self.response.out.write(self.help(self.u, self.r))
            if self.request.query_string == 'purge':
                a_month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                for record in Sprunge.gql('WHERE date < DATETIME(:1)', a_month_ago).run():
                    record.delete()
            return

        c = Sprunge.gql('WHERE name = :1', got).get()
        if not c:
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            self.response.out.write(got + ' not found')
            return

        syntax = self.request.query_string
        if not syntax:
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            self.response.out.write(c.content + '\n')
            return
        try:
            lexer = pygments.lexers.get_lexer_by_name(syntax)
        except:
            lexer = pygments.lexers.TextLexer()
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.out.write(highlight(c.content,
                                          lexer,
                                          HtmlFormatter(full=True,
                                                        style='borland',
                                                        lineanchors='n',
                                                        linenos='inline',
                                                        encoding='utf-8')))

    def post(self, got):
        self.response.headers['Content-Type'] = 'text/plain'
        if self.request.get(self.r):
            nid = self.new_id()
            while Sprunge.gql('WHERE name = :1', nid).get():
                nid = self.new_id()
            s = Sprunge()
            s.content = self.request.get(self.r)
            s.name = nid

            try:
                s.put()
            except Exception as ex:
                self.response.out.write('{0}\n'.format(ex))
                return

            self.response.out.write('{0}/{1}\n'.format(self.u, nid))


def main():
    application = webapp.WSGIApplication([(r'/(.*)', Index)], debug=False)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
