from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    Promise
    )

from webhelpers import paginate

@view_config(route_name='promises', renderer='promises.html', request_method='GET')
def promises(request):
    current_page = request.GET.get('page', 1)
    query = DBSession.query(Promise)
    page_url = paginate.PageURL_WebOb(request)
    promises = paginate.Page(query, current_page, url=page_url)
    return {'promises': promises}