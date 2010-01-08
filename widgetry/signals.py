import django.dispatch

search_request = django.dispatch.Signal(providing_args=["request",])
wrapper_registration = django.dispatch.Signal(providing_args=["klass","wrapper"])
get_wrapper = django.dispatch.Signal(providing_args=["model",])