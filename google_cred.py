import gdata
import gdata.photos.service
import gdata.media
import gdata.geo
import gdata.gauth
import webbrowser
import httplib2
from datetime import datetime, timedelta
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage

def OAuth2Login(secrets, store, email):
    scope = 'https://picasaweb.google.com/data/'
    user_agent = 'picasawebuploader'

    storage = Storage(store)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        flow = flow_from_clientsecrets(secrets, scope=scope, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        uri = flow.step1_get_authorize_url()
        webbrowser.open(uri)
        code = raw_input('Provide the Auth code: ').strip()
        credentials = flow.step2_exchange(code)

    if (credentials.token_expiry - datetime.utcnow()) < timedelta(minutes=5):
        http = credentials.authorize(httplib2.Http())
        credentials.refresh(http)

    storage.put(credentials)
    picasa_client = gdata.photos.service.PhotosService(source = user_agent,email = email,additional_headers = {'Authorization' : 'Bearer %s' % credentials.access_token})

    return picasa_client

