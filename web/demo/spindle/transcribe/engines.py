
from django.conf import settings
import importlib

def _list_engines():
    engines=dict()
    for module_name in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(module_name)
            engine = dict(name = module.SPINDLE_TRANSCRIBER_NAME,
                          task = module.transcribe)
            engines[module.__name__] = engine
        except ImportError as e:
            pass
        except AttributeError as e:
            pass

    return engines

engine_map = _list_engines()
