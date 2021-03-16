import inspect


def object_is_subclass(obj, parent_class, verbose=False):
    if verbose:
        print(f'{obj} inherits from {type(obj).__bases__}')
    for base in type(obj).__bases__:
        if base.__name__ == parent_class.__name__:
            return True
    return False


def type_error_message(obj, *args):
    msg = f'Unable to call {obj.__qualname__}().\nCalled with signature:\n\t('
    for i, arg in enumerate(inspect.signature(obj).parameters.keys()):
        msg += f'{arg}: {type(args[i])} {args[i]}'
        if args[i] != args[-1]:
            msg += ', '
    msg += f')\nSignature must be:\n\t{inspect.signature(obj)}'
    return msg
