
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginator(queryset, limit=10, page=1):
    '''This function is responsible to paginate querysets and return paginated data along with total_count, total_pages, limit and page'''

    paginator = Paginator(queryset,limit)
    total_count = paginator.count
    total_pages = paginator.num_pages

    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = []

    return {
        'queryset': queryset,
        'total_count': total_count,
        'total_pages': total_pages,
        'limit': int(limit),
        'page' : int(page)
    }