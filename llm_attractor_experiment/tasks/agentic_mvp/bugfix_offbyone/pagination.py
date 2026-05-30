def paginate(items, page_size):
    """Split `items` into consecutive pages of at most `page_size` items.

    Returns a list of pages (each a list). The final page may be shorter
    than `page_size` if the items don't divide evenly.
    """
    pages = []
    i = 0
    # BUG: this drops the final partial page when len(items) is not a
    # multiple of page_size.
    while i < len(items) - page_size:
        pages.append(items[i:i + page_size])
        i += page_size
    return pages
