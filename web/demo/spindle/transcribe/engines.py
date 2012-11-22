from django.conf import settings
import importlib
import logging

logger = logging.getLogger(__name__)

_ENGINE_MAP = None

def engine_map():
    global _ENGINE_MAP
    if _ENGINE_MAP: return _ENGINE_MAP

    engines=dict()
    for module_name in settings.INSTALLED_APPS:
        logger.info("Trying %s", module_name)
        try:
            module = importlib.import_module(module_name)
            engine = dict(name = module.SPINDLE_TRANSCRIBER_NAME,
                          task = module.transcribe)
            engines[module.__name__] = engine
            logger.info("Success: %s = %s!", module_name, engine['name'])
        except ImportError as e:
            logger.info("Failed: %s", e)
            pass
        except AttributeError as e:
            logger.info("Failed: %s", e)
            pass

    _ENGINE_MAP = engines
    return engines
