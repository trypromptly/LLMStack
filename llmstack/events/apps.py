import importlib

from django.apps import AppConfig


class EventsConfig(AppConfig):
    name = "llmstack.events"
    label = "events"

    def ready(self) -> None:
        from django.conf import settings

        # Ensure Event topic mapping is correctly configured in settings, if not make it empty
        if not hasattr(settings, "EVENT_TOPIC_MAPPING"):
            setattr(settings, "EVENT_TOPIC_MAPPING", {})

        for topic in settings.EVENT_TOPIC_MAPPING:
            if not isinstance(settings.EVENT_TOPIC_MAPPING[topic], list):
                raise ValueError(f"EVENT_TOPIC_MAPPING[{topic}] must be a list of processor functions")
            for processor_fn_name in settings.EVENT_TOPIC_MAPPING[topic]:
                try:
                    module_name = ".".join(processor_fn_name.split(".")[:-1])
                    fn_name = processor_fn_name.split(".")[-1]
                    module = importlib.import_module(module_name)
                    if not callable(getattr(module, fn_name)):
                        raise ValueError(
                            f"EVENT_TOPIC_MAPPING[{topic}] contains an invalid processor function: {processor_fn_name}"
                        )
                except ImportError:
                    raise ValueError(
                        f"EVENT_TOPIC_MAPPING[{topic}] contains an invalid processor function: {processor_fn_name}"
                    )

        return super().ready()
