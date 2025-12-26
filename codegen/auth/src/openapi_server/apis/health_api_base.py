# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from typing import Any


class BaseHealthApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseHealthApi.subclasses = BaseHealthApi.subclasses + (cls,)
    async def health_check_health_get(
        self,
    ) -> object:
        """Health check endpoint.  Returns service status and version."""
        ...
