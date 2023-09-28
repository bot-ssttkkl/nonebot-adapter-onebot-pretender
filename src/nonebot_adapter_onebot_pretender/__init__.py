from .v11 import create_ob11_adapter_pretender
from .v11.impl import init_ob11_pretender_impl
from .patch_handle_event import init_patch_handle_event


def init_onebot_pretender():
    init_patch_handle_event()
    init_ob11_pretender_impl()


__all__ = ("init_onebot_pretender", "create_ob11_adapter_pretender")
