# Copyright (C) 2022-present kastaid
# https://github.com/kastaid/getter
# AGPL-3.0 License

import asyncio
import os
import random
import subprocess
import sys
from datetime import datetime
from time import monotonic, sleep as tsleep
from typing import TYPE_CHECKING

import psutil
from telethon.tl import functions as fun

from . import (
    LOG_DIR,
    Root,
    StartTime,
    format_bytes,
    format_latency,
    format_time,
    getter_app,
    kasta_cmd,
    parse_pre,
    plugins_help,
    sgvar,
)

if TYPE_CHECKING:
    from pathlib import Path

usage_text = """
<b>🖥️ Uptime</b>
<b>App</b>: <code>{}</code>
<b>System</b>: <code>{}</code>

<b>📊 Data Usage</b>
<b>Upload</b>: <code>{}</code>
<b>Download</b>: <code>{}</code>

<b>💾 Disk Space</b>
<b>Total</b>: <code>{}</code>
<b>Used</b>: <code>{}</code>
<b>Free</b>: <code>{}</code>

<b>📈 Memory Usage</b>
<b>CPU</b>: <code>{}</code>
<b>RAM</b>: <code>{}</code>
<b>DISK</b>: <code>{}</code>
<b>SWAP</b>: <code>{}</code>
"""


@kasta_cmd(
    pattern="alive$",
)
async def _(kst):
    await kst.eod("**Hey, I am alive !!**")


@kasta_cmd(
    pattern="(uptime|up)$",
)
async def _(kst):
    await kst.eod(f"**Uptime**: {kst.client.uptime}")


@kasta_cmd(
    pattern="ping$|([p]ing)$",
    ignore_case=True,
    edited=True,
)
async def _(kst):
    start = monotonic()
    task = asyncio.ensure_future(kst.client(fun.PingRequest(ping_id=0)))
    _done, pending = await asyncio.wait({task}, timeout=8.0)
    if task in pending:
        pass
    else:
        try:
            task.result()
        except Exception:
            pass
    text = f"Speed – {format_latency(monotonic() - start)}\n"
    text += "Uptime – {}".format(
        format_time(
            monotonic() - StartTime,
            short=True,
        )
    )
    await kst.eor(text)


@kasta_cmd(
    pattern="usage$",
)
async def _(kst):
    yy = await kst.eor("`Processing...`")
    await yy.eor(system_usage(), parse_mode="html")


@kasta_cmd(
    pattern="logs?(?: |$)(open)?",
)
@kasta_cmd(
    pattern="glogs?(?: |$)(open)?(?: |$)(.*)",
    dev=True,
)
async def _(kst):
    mode = kst.pattern_match.group(1)
    if kst.is_dev:
        opt = kst.pattern_match.group(2)
        user_id = None
        try:
            user_id = int(opt)
        except ValueError:
            pass
        if user_id and user_id != kst.client.uid:
            return
        await asyncio.sleep(random.choice((4, 6, 8)))
    yy = await kst.eor("`Getting...`", silent=True)
    if mode == "open":
        for file in get_terminal_logs():
            logs = await asyncio.to_thread(file.read_text)
            await yy.sod(
                logs,
                parts=True,
                parse_mode=parse_pre,
            )
    else:
        try:
            for file in get_terminal_logs():
                await yy.eor(
                    "**#Getter** Terminal Logs",
                    file=file,
                    force_document=True,
                )
        except Exception:
            pass


@kasta_cmd(
    pattern="restart$",
)
@kasta_cmd(
    pattern="grestart(?: |$)(.*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev:
        opt = kst.pattern_match.group(1)
        user_id = None
        try:
            user_id = int(opt)
        except ValueError:
            pass
        if user_id and user_id != kst.client.uid:
            return
        await asyncio.sleep(random.choice((4, 6, 8)))
    yy = await kst.eor("`Restarting...`", silent=True)
    try:
        chat_id = yy.chat_id or yy.from_id
        await sgvar("_restart", f"{chat_id}|{yy.id}")
    except Exception:
        pass
    await yy.eor("**#Getter** `Restarting as locally...`")
    restart_app()


@kasta_cmd(
    pattern="sleep(?: |$)(.*)",
)
async def _(kst):
    sec = await kst.client.get_text(kst)
    timer = int(sec) if sec.replace(".", "", 1).isdecimal() else 3
    timer = 3 if timer > 30 else timer
    yy = await kst.eor(f"`sleep in {timer} seconds...`")
    tsleep(timer)  # noqa: ASYNC251
    await yy.eod(f"`wake-up from {timer} seconds`")


def get_terminal_logs() -> list[Path]:
    return sorted(LOG_DIR.glob("*.log"))


def restart_app() -> None:
    reqs = str(Root / "requirements.txt")
    try:
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "-r",
                reqs,
            ],
            check=True,
        )
    except FileNotFoundError:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--prefer-binary",
                "--disable-pip-version-check",
                "--default-timeout=100",
                "-r",
                reqs,
            ],
            check=True,
        )
    os.execl(sys.executable, sys.executable, "-m", "getter")


def system_usage() -> str:
    try:
        UPLOAD = format_bytes(psutil.net_io_counters().bytes_sent)
    except Exception:
        UPLOAD = 0
    try:
        DOWN = format_bytes(psutil.net_io_counters().bytes_recv)
    except Exception:
        DOWN = 0
    try:
        workdir = psutil.disk_usage(".")
        TOTAL = format_bytes(workdir.total)
        USED = format_bytes(workdir.used)
        FREE = format_bytes(workdir.free)
    except Exception:
        TOTAL = 0
        USED = 0
        FREE = 0
    try:
        cpu_freq = psutil.cpu_freq().current
        cpu_freq = f"{round(cpu_freq / 1000, 2)}GHz" if cpu_freq >= 1000 else f"{round(cpu_freq, 2)}MHz"
        CPU = f"{psutil.cpu_percent()}% ({psutil.cpu_count()}) {cpu_freq}"
    except Exception:
        try:
            CPU = f"{psutil.cpu_percent()}%"
        except Exception:
            CPU = "0%"
    try:
        RAM = f"{psutil.virtual_memory().percent}%"
    except Exception:
        RAM = "0%"
    try:
        DISK = "{}%".format(psutil.disk_usage("/").percent)
    except Exception:
        DISK = "0%"
    try:
        swap = psutil.swap_memory()
        SWAP = f"{format_bytes(swap.total)} | {swap.percent or 0}%"
    except Exception:
        SWAP = "0 | 0%"
    return usage_text.format(
        getter_app.uptime,
        datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
        UPLOAD,
        DOWN,
        TOTAL,
        USED,
        FREE,
        CPU,
        RAM,
        DISK,
        SWAP,
    )


plugins_help["bot"] = {
    "{pfx}alive": "Just showing alive.",
    "{pfx}uptime|{pfx}up": "Check current uptime.",
    "{pfx}ping|ping|Ping": "Check how long it takes to ping.",
    "{pfx}usage": "Get system resource usage.",
    "{pfx}logs": "Get the full terminal logs.",
    "{pfx}logs open": "Open logs as text message.",
    "{pfx}restart": "Restart the bot.",
    "{pfx}sleep [seconds]/[reply]": "Sleep the bot in few seconds (max 30).",
}
