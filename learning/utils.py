from math import ceil


def batch_queryset(queryset, batch_size):
    total_objects = queryset.count()
    total_batches = ceil(total_objects / batch_size)
    for i in range(total_batches):
        start = i * batch_size
        end = start + batch_size
        yield queryset[start:end]
