

class DoesNotExist(object):pass


def traverse_object(obj, dot_notation):
    '''
    will traverse the object based on dot notation. callable attributes will be
    called.
    e.g 'someattr.otherattr.callable.more' would result in 
    `object.someattr.otherattr.callable().more` being called
    '''
    attribute_chain = dot_notation.split('.')
    if '' in attribute_chain: attribute_chain.remove('')
    if len(attribute_chain)>0:
        current_object = obj
        for attr in attribute_chain:
            current_object = getattr(current_object, attr, DoesNotExist)
            if current_object is DoesNotExist:
                # something is wrong or the targeted field does not 
                # contain any data
                return None # should we raise an error here?
            if callable(current_object):
                current_object = current_object()
        return current_object
    return obj