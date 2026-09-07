# Copyright (C) 2022-present kastaid
# https://github.com/kastaid/getter
# AGPL-3.0 License

import asyncio
import random
from typing import TYPE_CHECKING

from telethon.tl import functions as fun, types as typ

from getter import __version__
from getter.config import Var
from getter.logger import LOG

from .db import (
    dgvar,
    gvar,
    sgvar,
)
from .helper import get_botlogs
from .property import _c
from .utils import humanbool

if TYPE_CHECKING:
    from .kasta import KastaClient

_about = """GETTER BOTLOGS

Chat ID: {}
Your ID: {}

⚠️  DO NOT DELETE THIS GROUP  ⚠️

Our Channel: @kastaid
"""
_warn = """<b>⚠️ DO NOT LEAVE OR,
⚠️ DO NOT DELETE OR,
⚠️ DO NOT CHANGE THE SETTINGS OF THIS GROUP!</b>


<b><u>IF IGNORED THIS MESSAGE THE BOT WILL NOT WORK</u></b>


<b>Chat ID</b>: <code>{}</code>
<b>Your ID</b>: <code>{}</code>

<b>Our Channel</b>: @kastaid
"""
_restart_text = """
**#Getter** **is back and alive!**
├  **Sudo**: `{}`
├  **PM-Guard**: `{}`
├  **PM-Logs**: `{}`
├  **PM-Block**: `{}`
├  **Anti-PM**: `{}`
└  **Version**: `{}`
"""
_reboot_text = """
**#Getter** **is rebooted and applied!**
├  **Sudo**: `{}`
├  **PM-Guard**: `{}`
├  **PM-Logs**: `{}`
├  **PM-Block**: `{}`
├  **Anti-PM**: `{}`
└  **Version**: `{}`
"""


async def autopilot(client: KastaClient) -> None:
    if Var.BOTLOGS or await gvar("BOTLOGS"):
        return
    LOG.info("> Auto-Pilot...")
    photo = None
    try:
        photo = await client.upload_file("assets/getter.png")
        await asyncio.sleep(random.uniform(3.5, 6.5))
    except Exception:
        pass
    LOG.info("Creating a group for BOTLOGS...")
    _, chat_id = await client.create_group(
        title="GETTER BOTLOGS",
        about="",
        users=["@MissRose_bot"],
        photo=photo,
    )
    if not chat_id:
        LOG.warning("Something happened while creating a group for BOTLOGS, please report this one to our developers!")
        return
    await sgvar("BOTLOGS", chat_id)
    try:
        await asyncio.sleep(random.uniform(3.5, 6.5))
        await client(
            fun.messages.EditChatAboutRequest(
                chat_id,
                about=_about.format(chat_id, client.uid),
            )
        )
    except Exception:
        pass
    try:
        msg = await client.send_message(chat_id, _warn.format(chat_id, client.uid), parse_mode="html")
        await asyncio.sleep(random.uniform(3.5, 6.5))
        await msg.pin(notify=True)
    except Exception:
        pass
    LOG.success("Successfully to created a group for BOTLOGS.")
    await asyncio.sleep(1)
    print(f"\nBOTLOGS = {chat_id}\n")
    await asyncio.sleep(1)
    LOG.info("Save the BOTLOGS ID above, might be useful for the future :)")


async def verify(client: KastaClient) -> None:
    BOTLOGS = await get_botlogs()
    if not BOTLOGS:
        return
    ls = None
    try:
        ls = await client.get_entity(BOTLOGS)
    except Exception:
        pass
    if not ls:
        return
    if not (isinstance(ls, typ.User) and ls.creator) and ls.default_banned_rights.send_messages:
        LOG.critical(
            "Your account doesn't have permission to send messages in the BOTLOGS group. Please re-check that ID is correct or change the group permissions to send messages and send media!"
        )


async def autous(client: KastaClient) -> None:
    try:
        entity = await client.get_input_entity(_c)
    except Exception:
        return
    try:
        await asyncio.sleep(random.uniform(3.5, 6.5))
        await client(fun.channels.JoinChannelRequest(entity))
    except Exception:
        pass
    try:
        await asyncio.sleep(random.uniform(1.5, 2.5))
        msgs = await client(
            fun.messages.GetHistoryRequest(
                peer=entity,
                offset_id=0,
                offset_date=0,
                add_offset=0,
                limit=1,
                max_id=0,
                min_id=0,
                hash=0,
            )
        )
        if not msgs.messages:
            return
        message_id = msgs.messages[0].id
        await client(
            fun.channels.ReadHistoryRequest(
                channel=entity,
                max_id=message_id,
            )
        )
        await asyncio.sleep(random.uniform(1.5, 2.5))
        await client(
            fun.messages.GetMessagesViewsRequest(
                peer=entity,
                id=[message_id],
                increment=True,
            )
        )
    except Exception:
        pass


async def finishing(client: KastaClient, text: str) -> None:
    BOTLOGS = await get_botlogs()
    is_restart, is_reboot = False, False
    try:
        restart = (await gvar("_restart")).split("|")
        is_restart = True
    except Exception:
        pass
    try:
        reboot = (await gvar("_reboot")).split("|")
        is_reboot = True
    except Exception:
        pass
    if is_restart:
        try:
            chat_id, msg_id = int(restart[0]), int(restart[1])
            async with asyncio.timeout(5):
                await client.edit_message(
                    chat_id,
                    message=msg_id,
                    text=_restart_text.format(
                        humanbool(await gvar("_sudo"), toggle=True),
                        humanbool(await gvar("_pmguard"), toggle=True),
                        humanbool(await gvar("_pmlog"), toggle=True),
                        humanbool(await gvar("_pmblock"), toggle=True),
                        humanbool(await gvar("_antipm"), toggle=True),
                        __version__,
                    ),
                    link_preview=False,
                )
            await asyncio.sleep(random.uniform(3.5, 6.5))
        except Exception:
            pass
        await dgvar("_restart")
    if is_reboot:
        try:
            chat_id, msg_id = int(reboot[0]), int(reboot[1])
            async with asyncio.timeout(5):
                await client.edit_message(
                    chat_id,
                    message=msg_id,
                    text=_reboot_text.format(
                        humanbool(await gvar("_sudo"), toggle=True),
                        humanbool(await gvar("_pmguard"), toggle=True),
                        humanbool(await gvar("_pmlog"), toggle=True),
                        humanbool(await gvar("_pmblock"), toggle=True),
                        humanbool(await gvar("_antipm"), toggle=True),
                        __version__,
                    ),
                    link_preview=False,
                )
        except Exception:
            pass
        await dgvar("_reboot")
    if BOTLOGS:
        try:
            text += "\n(c) @kastaid #getter #launch"
            await client.send_message(
                BOTLOGS,
                text,
                parse_mode="html",
                link_preview=False,
                silent=True,
            )
        except Exception:
            pass
