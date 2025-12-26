# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from typing import Any


class BaseRootApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseRootApi.subclasses = BaseRootApi.subclasses + (cls,)
    async def root_get(
        self,
    ) -> object:
        """Root endpoint.  Returns service information."""
        ...
