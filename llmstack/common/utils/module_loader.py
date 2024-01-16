import importlib
import inspect
import logging
import pkgutil

logger = logging.getLogger(__name__)


def get_all_sub_classes(module_name, clas_obj):
    classes = []
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        logger.exception(e)
        return classes

    for _, class_name, is_pkg in pkgutil.iter_modules(module.__path__):
        if is_pkg:
            classes.extend(
                get_all_sub_classes(
                    f"{module_name}.{class_name}",
                    clas_obj,
                ),
            )

        try:
            class_module = importlib.import_module(
                f"{module_name}.{class_name}",
            )
            module_classes = [
                obj
                for name, obj in inspect.getmembers(
                    class_module,
                )
                if inspect.isclass(obj) and issubclass(obj, clas_obj)
            ]
            classes.extend(module_classes)
        except ImportError as e:
            logger.exception(e)
            pass

    # Filter out the Parent class (clas_obj)
    return list(filter(lambda x: x != clas_obj, classes))
