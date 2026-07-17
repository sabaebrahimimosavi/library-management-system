from rest_framework.pagination import PageNumberPagination


class BookPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

class LookupPagination(PageNumberPagination):
    """
    Larger pages for data used in dropdowns.
    """

    page_size = 200
    page_size_query_param = "page_size"
    max_page_size = 1000