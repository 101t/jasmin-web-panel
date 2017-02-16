mport os
import sys
import site

site.addsitedir('/var/www/html/env/lib/python2.7/site-packages')

sys.path.append('/var/www/html')
sys.path.append('/var/www/html/main')

os.environ['PYTHON_EGG_CACHE'] = '/var/www/html/egg_cache'
os.environ['DJANGO_SETTINGS_MODULE'] = 'main.settings'

# for Django <= 1.6
# import django.core.handlers.wsgi
# application = django.core.handlers.wsgi.WSGIHandler()

# for Django 1.8 and 1.7
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
