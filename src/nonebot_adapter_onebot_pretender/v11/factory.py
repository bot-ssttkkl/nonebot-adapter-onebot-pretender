from typing import Type, Callable, Dict, Any

from nonebot import Adapter as BaseAdapter, Driver
from nonebot.adapters.onebot.v11 import Adapter as OB11Adapter

from .adapter import Adapter as OB11PretenderAdapter
from .pretender import OB11Pretender

_pretenders: Dict[str, Type[OB11Pretender]] = {}


def register_ob11_pretender(adapter: Type[BaseAdapter]) -> Callable[[Type[OB11Pretender]], Type[OB11Pretender]]:
    def decorator(pretender: Type[OB11Pretender]) -> Type[OB11Pretender]:
        _pretenders[adapter.get_name()] = pretender

        return pretender

    return decorator


def create_ob11_adapter_pretender(*adapter: Type[BaseAdapter]) -> Type[OB11PretenderAdapter]:
    pretender_adapters = []

    for actual_adapter in adapter:
        pretender = _pretenders.get(actual_adapter.get_name())
        if pretender is None:
            raise RuntimeError(f"未找到 {actual_adapter.get_name()} 的 Pretender 实现")

        class Adapter(OB11PretenderAdapter):
            @classmethod
            def get_pretender_type(cls):
                return pretender

        Adapter.__module__ = OB11Adapter.__module__
        Adapter.__qualname__ = OB11Adapter.__qualname__

        pretender_adapters.append(Adapter)

    class Adapter(OB11Adapter):
        def __init__(self, driver: Driver, **kwargs: Any):
            self.pretender_adapters = []
            for adp in pretender_adapters:
                self.pretender_adapters.append(adp(driver, **kwargs))

    Adapter.__module__ = OB11Adapter.__module__
    Adapter.__qualname__ = OB11Adapter.__qualname__

    return Adapter


__all__ = ("create_ob11_adapter_pretender",)
