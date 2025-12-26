# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from typing import Any


class BaseDefaultApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseDefaultApi.subclasses = BaseDefaultApi.subclasses + (cls,)
    async def root_get(
        self,
    ) -> object:
        """Root endpoint"""
        ...


    async def health_check_health_get(
        self,
    ) -> object:
        """Health check endpoint"""
        ...


    async def get_plans_plans_get(
        self,
    ) -> object:
        """Get available subscription plans"""
        ...
