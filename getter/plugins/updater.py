# Copyright (C) 2022-present kastaid
# https://github.com/kastaid/getter
# AGPL-3.0 License

import asyncio
import os
import random
import shutil
import sys
from datetime import UTC, datetime

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from . import (
    DOWNLOAD_DIR,
    MAX_MESSAGE_LEN,
    Root,
    Runner,
    Var,
    __layer__,
    __pyversion__,
    __tlversion__,
    __version__,
    formatx_send,
    gvar,
    humanbool,
    kasta_cmd,
    plugins_help,
    sgvar,
    strip_format,
)

_UPDATE_LOCK = asyncio.Lock()

UPSTREAM_REPO = "https://github.com/kastaid/getter.git"
UPSTREAM_BRANCH = "main"

help_text = f"""
❯ `{Var.PREFIX}update [now/pull]`
Temporarily update as locally.

❯ `{Var.PREFIX}update force`
Force temporarily update as locally.
"""
test_text = """
├  <b>User</b>: <code>{}</code>
├  <b>ID</b>: <code>{}</code>
├  <b>Getter Version</b>: <code>{}</code>
├  <b>Python Version</b>: <code>{}</code>
├  <b>Telethon Version</b>: <code>{}</code>
├  <b>Telegram Layer</b>: <code>{}</code>
├  <b>Handler</b>: {}
├  <b>Sudo</b>: <code>{}</code>
├  <b>PM-Guard</b>: <code>{}</code>
├  <b>PM-Logs</b>: <code>{}</code>
├  <b>PM-Block</b>: <code>{}</code>
├  <b>Anti-PM</b>: <code>{}</code>
├  <b>Uptime</b>: <code>{}</code>
├  <b>UTC Now</b>: <code>{}</code>
└  <b>Local Now</b>: <code>{}</code>
"""


@kasta_cmd(
    pattern="update(?: |$)(force|now|pull)?(?: |$)(.*)",
)
@kasta_cmd(
    pattern="getterup(?: |$)(force|now|pull)?(?: |$)(.*)",
    edited=True,
    dev=True,
)
async def _(kst):
    if not kst.is_dev and _UPDATE_LOCK.locked():
        return await kst.eor("`Please wait until previous •update• finished...`", time=5, silent=True)
    async with _UPDATE_LOCK:
        group = kst.pattern_match.group
        mode, opt, is_force, is_now, state = group(1), group(2), False, False, ""
        if not Var.DEV_MODE and mode == "force":
            is_force = True
            state = "[FORCE] "
        elif mode in {"now", "pull"}:
            is_now = True
            state = "[NOW] "
        else:
            state = "[CHECK] "
        if kst.is_dev and opt:
            user_id = version = None
            try:
                user_id = int(opt)
            except ValueError:
                version = opt
            if not version and user_id != kst.client.uid:
                return
            if not user_id and version == __version__:
                return
        if kst.is_dev:
            await asyncio.sleep(random.choice((5, 7, 9)))
        yy = await kst.eor(f"`{state}Fetching...`", silent=True)
        try:
            repo = Repo()
        except NoSuchPathError as err:
            return await yy.eor(f"`{state}Directory not found : {err}`")
        except GitCommandError as err:
            return await yy.eor(f"`{state}Early failure : {err}`")
        except InvalidGitRepositoryError:
            repo = Repo.init()
            origin = repo.create_remote("origin", UPSTREAM_REPO)
            origin.fetch()
            repo.create_head("main", origin.refs.main)
            repo.heads.main.set_tracking_branch(origin.refs.main)
            repo.heads.main.checkout(True)
        await Runner(f"git fetch origin {UPSTREAM_BRANCH}")
        try:
            verif = verify(repo, f"HEAD..origin/{UPSTREAM_BRANCH}")
        except Exception:
            verif = None
        if not (verif or is_force):
            return await yy.eor(f"**#Getter** `v{__version__} up-to-date as {UPSTREAM_BRANCH}`")
        if not (mode or is_force):
            changelog = generate_changelog(repo, f"HEAD..origin/{UPSTREAM_BRANCH}")
            return await show_changelog(yy, changelog)
        if is_force:
            await asyncio.sleep(3)
        if is_now or is_force:
            await yy.eor(f"`{state}Updating ~ Please Wait...`")
            await Pulling(yy, state)
        return


@kasta_cmd(
    pattern="repo$",
)
async def _(kst):
    await kst.eor(
        "https://github.com/kastaid/getter",
        link_preview=True,
    )


@kasta_cmd(
    pattern="test$",
)
@kasta_cmd(
    pattern="test$",
    sudo=True,
)
@kasta_cmd(
    pattern="gtest(?: |$)(.*)",
    edited=True,
    dev=True,
)
async def _(kst):
    ga = kst.client
    clean = False
    if kst.is_dev:
        opt = kst.pattern_match.group(1)
        if opt:
            user_id = version = None
            try:
                user_id = int(opt)
            except ValueError:
                version = opt
            if not version and user_id != ga.uid:
                return
            if not user_id and version == __version__:
                return
            clean = True
        if not clean:
            await asyncio.sleep(random.choice((4, 6, 8)))
    if kst.is_sudo:
        await asyncio.sleep(random.choice((4, 6, 8)))
    utc_now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    local_now = datetime.now(Var.TZ).strftime("%Y-%m-%d %H:%M:%S")
    yy = await kst.eor("`Processing...`", silent=True, force_reply=True)
    await yy.eor(
        test_text.format(
            ga.full_name,
            ga.uid,
            __version__,
            __pyversion__,
            __tlversion__,
            __layer__,
            Var.PREFIX or "No Handler",
            humanbool(await gvar("_sudo", use_cache=True), toggle=True),
            humanbool(await gvar("_pmguard", use_cache=True), toggle=True),
            humanbool(await gvar("_pmlog", use_cache=True), toggle=True),
            humanbool(await gvar("_pmblock", use_cache=True), toggle=True),
            humanbool(await gvar("_antipm", use_cache=True), toggle=True),
            ga.uptime,
            utc_now,
            local_now,
        ),
        parse_mode="html",
        time=20 if clean else 0,
    )


async def update_packages() -> None:
    reqs = str(Root / "requirements.txt")
    if shutil.which("uv"):
        await Runner(f"uv pip install -r {reqs}")
    else:
        await Runner(
            f"{sys.executable} -m pip install --prefer-binary --disable-pip-version-check --default-timeout=100 -r {reqs}"
        )


async def force_pull() -> None:
    await Runner(f"git pull --force && git reset --hard origin/{UPSTREAM_BRANCH}")


def verify(repo, diff) -> bool:
    v = ""
    for c in repo.iter_commits(diff):
        v = str(c.count())
    return bool(v)


def generate_changelog(repo, diff) -> str:
    chlog = ""
    rep = UPSTREAM_REPO.replace(".git", "")
    ch = f"<b>#Getter</b> <b>v{__version__} New UPDATE available for <a href={rep}/tree/{UPSTREAM_BRANCH}>[{UPSTREAM_BRANCH}]</a></b>:"
    date = "%Y-%m-%d %H:%M:%S"
    for _ in repo.iter_commits(diff):
        chlog += f"\n\n<b>#{_.count()}</b> [<code>{_.committed_datetime.strftime(date)}</code>]\n<code>{_.hexsha}</code>\n<b><a href={rep.rstrip('/')}/commit/{_}>[{_.summary}]</a></b> ~ <code>{_.author}</code>"
    if chlog:
        return str(ch + chlog)
    return chlog


async def show_changelog(kst, changelog) -> None:
    if len(changelog) > MAX_MESSAGE_LEN:
        changelog = strip_format(changelog)
        file = DOWNLOAD_DIR / "changelog.txt"
        await asyncio.to_thread(file.write_text, changelog, encoding="utf-8")
        try:
            chlog = await kst.eor(
                "**#Getter** View this file to see changelog.",
                file=file,
                force_document=True,
            )
        except Exception as err:
            chlog = await kst.eor(formatx_send(err), parse_mode="html")
        await asyncio.to_thread(file.unlink, missing_ok=True)
    else:
        chlog = await kst.eor(changelog, parse_mode="html")
    await chlog.reply(help_text, silent=True)


async def Pulling(kst, state) -> None:
    if not Var.DEV_MODE:
        await force_pull()
        await update_packages()
    up = f"""**#Getter** `{state}Updated Successfully...`
Wait for a few seconds, then run `{Var.PREFIX}ping` command."""
    yy = await kst.eor(up)
    try:
        chat_id = yy.chat_id or yy.from_id
        await sgvar("_restart", f"{chat_id}|{yy.id}")
    except Exception:
        pass
    os.execl(sys.executable, sys.executable, "-m", "getter")


plugins_help["updater"] = {
    "{pfx}update": "Checks for updates, also displaying the changelog.",
    "{pfx}update [now/pull]": "Temporarily update as locally.",
    "{pfx}update force": "Force temporarily update as locally.",
    "{pfx}repo": "Get repo link.",
    "{pfx}test": "Check the details.",
}
