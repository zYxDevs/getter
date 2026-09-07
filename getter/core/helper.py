# Copyright (C) 2022-present kastaid
# https://github.com/kastaid/getter
# AGPL-3.0 License

import html
from collections import UserDict
from typing import Any

import cachebox

from getter.config import Var

from .db import get_col, gvar
from .utils import get_full_class_name


class PluginsHelp(UserDict):
    def append(self, obj: dict) -> None:
        plug = next(iter(obj.keys()))
        cmds = {}
        for i in obj[plug]:
            name = next(iter(i.keys()))
            desc = i[name]
            cmds[name] = desc
        self[plug] = cmds

    @property
    def count(self) -> int:
        return len(self)

    @property
    def total(self) -> int:
        return sum(len(i) for i in self.values())


class JSONData:
    def __init__(self) -> None:
        self.CACHE_DATA = cachebox.LRUCache(maxsize=0)

    async def sudos(self) -> dict[str, Any]:
        return getattr(await get_col("sudos"), "json", {})

    async def pmwarns(self) -> dict[str, int]:
        return getattr(await get_col("pmwarns"), "json", {})

    async def pmlasts(self) -> dict[str, int]:
        return getattr(await get_col("pmwarns"), "njson", {})

    async def gblack(self) -> dict[str, Any]:
        return getattr(await get_col("gblack"), "json", {})

    async def gblacklist(self) -> set[int]:
        result = await self.gblack()
        return {int(i) for i in result}

    async def sudo_users(self) -> list[int]:
        if "sudo" in self.CACHE_DATA:
            return self.CACHE_DATA.get("sudo", [])
        result = await self.sudos()
        users = [int(i) for i in result]
        if "sudo" not in self.CACHE_DATA:
            self.CACHE_DATA["sudo"] = users
        return users


async def get_botlogs() -> int:
    if hasattr(get_botlogs, "cache"):
        return get_botlogs.cache
    botlogs = await gvar("BOTLOGS", use_cache=True)
    get_botlogs.cache = int(Var.BOTLOGS or botlogs or 0)
    return get_botlogs.cache


def formatx_send(err: Exception) -> str:
    text = "<b>#Getter_Error</b>"
    text += f"\n<pre>{get_full_class_name(err)}: {html.escape(str(err))}</pre>"
    return text


plugins_help = PluginsHelp()
jdata = JSONData()
