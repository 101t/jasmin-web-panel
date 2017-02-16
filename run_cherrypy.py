#!/usr/bin/env python

from main.wsgi import application

from django.conf import settings

import cherrypy

cherrypy.tree.graft(application, "/")

cherrypy.tree.mount(None, settings.STATIC_URL, {'/': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': settings.STATIC_ROOT,
        'tools.expires.on': True,
        'tools.expires.secs': 86400
    }
})

server = cherrypy._cpserver.Server()

server.socket_host = "0.0.0.0"
server.socket_port = 8000
server.thread_pool = 10

server.subscribe()

cherrypy.engine.start()
cherrypy.engine.block()
