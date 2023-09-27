from typing import Type, Callable, Dict

from nonebot import Adapter as BaseAdapter

from .adapter import Adapter as OB11PretenderAdapter
from .pretender import OB11Pretender

_pretenders: Dict[str, Type[OB11Pretender]] = {}


def register_ob11_pretender(adapter: Type[BaseAdapter]) -> Callable[[Type[OB11Pretender]], Type[OB11Pretender]]:
    def decorator(pretender: Type[OB11Pretender]) -> Type[OB11Pretender]:
        _pretenders[adapter.get_name()] = pretender

        return pretender

    return decorator


def create_ob11_adapter_pretender(adapter: Type[BaseAdapter]) -> Type[OB11PretenderAdapter]:
    PretenderImpl = _pretenders.get(adapter.get_name())
    if PretenderImpl is None:
        raise RuntimeError(f"未找到 {adapter.get_name()} 的 Pretender 实现")

    class Adapter(OB11PretenderAdapter):
        @classmethod
        def get_pretender_type(cls) -> Type[OB11Pretender]:
            return PretenderImpl

    return Adapter


__all__ = ("create_ob11_adapter_pretender",)
