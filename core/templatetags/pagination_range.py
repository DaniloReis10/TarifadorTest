from django import template

register = template.Library()


@register.filter
def pagination_range(page_range, page=1, limit=5):
    num_pages = len(page_range)

    if page == 1:
        page_range = [i for i in range(page, limit + 2) if i <= num_pages]
    elif page == num_pages:
        page_range = [i for i in range(page - limit, page + 1) if 1 <= i]
    else:
        limit += limit & 1
        limit //= 2
        page_range = [i for i in range(page - limit, page + limit + 1) if 1 <= i and i <= num_pages]

    return page_range
