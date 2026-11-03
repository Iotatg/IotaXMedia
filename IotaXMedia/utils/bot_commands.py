# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Curated Telegram command menu for ˹𝐈ᴏᴛᴀ ✘ 𝙼ᴜꜱɪᴄ˼ ♪ 🌸.

Normal users (BotCommandScopeDefault) see only public + admin commands.
The bot owner (BotCommandScopeChat(OWNER_ID)) additionally sees the
owner/sudo-only commands, so those stay hidden from everyone else.
"""
from pyrogram.types import BotCommand


DEFAULT_COMMANDS = [
    BotCommand("start", "˹ ѕϯαʀϯ ϯнє ʙσϯ"),
    BotCommand("help", "˹ ɢєϯ нєℓρ"),
    BotCommand("settings", "˹ σρєη ѕєϯϯɪηɢѕ"),
    BotCommand("play", "˹ ρℓαγ α ѕσηɢ/νɪᴅєσ"),
    BotCommand("vplay", "˹ ρℓαγ νɪᴅєσ"),
    BotCommand("stream", "˹ ѕϯʀєαᴍ α ℓɪνє/υʀℓ"),
    BotCommand("pause", "˹ ραυѕє ϯнє ѕϯʀєαᴍ"),
    BotCommand("resume", "˹ ʀєѕυᴍє ϯнє ѕϯʀєαᴍ"),
    BotCommand("skip", "˹ ѕκɪρ ϯнє ᴄυʀʀєηϯ ϯʀαᴄκ"),
    BotCommand("end", "˹ єηᴅ ϯнє ѕϯʀєαᴍ"),
    BotCommand("queue", "˹ ѕнσω ϯнє ǫυєυє"),
    BotCommand("loop", "˹ ℓσσρ ϯнє ᴄυʀʀєηϯ ѕσηɢ"),
    BotCommand("shuffle", "˹ ѕнυғғℓє ϯнє ǫυєυє"),
    BotCommand("seek", "˹ ѕєєκ ɪη ϯнє ѕϯʀєαᴍ"),
    BotCommand("speed", "˹ ᴄнαηɢє ρℓαγʙαᴄκ ѕρєєᴅ"),
    BotCommand("playmode", "˹ ѕєϯ ϯнє ρℓαγ ᴍσᴅє"),
    BotCommand("channelplay", "˹ ρℓαγ νɪα ᴄнαηηєℓ"),
    BotCommand("auth", "˹ αυϯн α υѕєʀ"),
    BotCommand("unauth", "˹ ʀєᴍσνє αυϯн"),
    BotCommand("userbotjoin", "˹ ᴊσɪη αѕѕɪѕϯαηϯ ϯσ ᴄнαϯ"),
    BotCommand("lang", "˹ ᴄнαηɢє ℓαηɢυαɢє"),
    BotCommand("info", "˹ υѕєʀ ɪηғσ"),
    BotCommand("id", "˹ ɢєϯ ɪᴅѕ"),
    BotCommand("stats", "˹ ʙσϯ ѕϯαϯѕ"),
    BotCommand("purge", "˹ ᴅєℓєϯє ᴍѕɢѕ"),
    BotCommand("del", "˹ ᴅєℓєϯє α ᴍѕɢ"),
    BotCommand("promote", "˹ ρʀσᴍσϯє αη αᴅᴍɪη"),
    BotCommand("fullpromote", "˹ ғυℓℓ ρʀσᴍσϯє"),
    BotCommand("demote", "˹ ᴅєᴍσϯє αη αᴅᴍɪη"),
    BotCommand("ban", "˹ ʙαη α υѕєʀ"),
    BotCommand("unban", "˹ υηʙαη α υѕєʀ"),
    BotCommand("mute", "˹ ᴍυϯє α υѕєʀ"),
    BotCommand("unmute", "˹ υηᴍυϯє α υѕєʀ"),
    BotCommand("kick", "˹ κɪᴄκ α υѕєʀ"),
    BotCommand("tmute", "˹ ϯєᴍρ ᴍυϯє"),
    BotCommand("tban", "˹ ϯєᴍρ ʙαη"),
    BotCommand("pin", "˹ ρɪη α ᴍѕɢ"),
    BotCommand("unpin", "˹ υηρɪη α ᴍѕɢ"),
    BotCommand("lockall", "˹ ѕɪℓєηᴄє ϯнє ᴄнαϯ"),
    BotCommand("unlockall", "˹ ʀєѕϯσʀє ᴍєᴍʙєʀ ᴘєʀᴍѕ"),
    BotCommand("slowmode", "˹ ѕєϯ ѕʟσω-ᴍσᴅє"),
    BotCommand("setusername", "˹ ѕєϯ ɢʀσυρ υѕєʀηαᴍє"),
    BotCommand("cleanup", "˹ ᴅєℓєϯє ʙσϯ ᴍѕɢѕ"),
    BotCommand("protect", "˹ ᴘʀσϯєᴄϯ ᴄσηϯєηϯ"),
    BotCommand("unprotect", "˹ υηᴘʀσϯєᴄϯ ᴄσηϯєηϯ"),
    BotCommand("checkadmin", "˹ ᴄнєᴄκ ᴀᴅᴍɪη ʀɪɢнᴛѕ"),
    BotCommand("listbots", "˹ ℓɪѕϯ ʙσϯѕ"),
    BotCommand("channels", "˹ ℓɪѕϯ ѕєηᴅєʀ ᴄнαηηєʟѕ"),
    BotCommand("banlist", "˹ ℓɪѕϯ ʙαηηєᴅ"),
    BotCommand("setphoto", "˹ ѕєϯ ᴄнαϯ ρɪᴄ"),
    BotCommand("welcome", "˹ ϯσɢɢℓє ωєℓᴄσᴍє"),
    BotCommand("tagall", "˹ ϯαɢ αℓℓ ᴍєᴍʙєʀѕ"),
    BotCommand("github", "˹ ɢɪϯнυʙ ℓɪηκ"),
    BotCommand("repo", "˹ ɢєϯ ϯнє ѕσυʀᴄє"),
    BotCommand("link", "˹ ɢєϯ ɪηνɪϯє ℓɪηκ"),
    BotCommand("admins", "˹ ℓɪѕϯ αᴅᴍɪηѕ"),
    BotCommand("zombies", "˹ ʀєᴍσνє ʐσᴍʙɪєѕ"),
    BotCommand("vcinfo", "˹ νσɪᴄє ᴄнαϯ ɪηғσ"),
    BotCommand("volume", "˹ ѕєϯ νᴄ νσℓυᴍє"),
    BotCommand("ai", "˹ αѕκ ɪσϯα αɪ"),
]


OWNER_COMMANDS = [
    BotCommand("gban", "˹ ɢℓσʙαℓ ʙαη α υѕєʀ"),
    BotCommand("ungban", "˹ ʀєᴍσνє α ɢℓσʙαℓ ʙαη"),
    BotCommand("gbannedusers", "˹ ℓɪѕϯ ɢℓσʙαℓℓγ ʙαηηєᴅ"),
    BotCommand("sudoers", "˹ ℓɪѕϯ ѕυᴅσєʀѕ"),
    BotCommand("addsudo", "˹ αᴅᴅ α ѕυᴅσєʀ"),
    BotCommand("delsudo", "˹ ʀєᴍσνє α ѕυᴅσєʀ"),
    BotCommand("maintenance", "˹ ϯσɢɢℓє ᴍαɪηϯєηαηᴄє"),
    BotCommand("logger", "˹ ϯσɢɢℓє ℓσɢɢєʀ"),
    BotCommand("restart", "˹ ʀєѕϯαʀϯ ϯнє ʙσϯ"),
    BotCommand("update", "˹ υρᴅαϯє ϯнє ʙσϯ"),
    BotCommand("getlog", "˹ ɢєϯ ϯнє ℓσɢ ғɪℓє"),
    BotCommand("block", "˹ ɢℓσʙαℓℓγ ʙℓσᴄκ α υѕєʀ"),
    BotCommand("unblock", "˹ υηʙℓσᴄκ α υѕєʀ"),
    BotCommand("blacklistchat", "˹ ʙℓαᴄκℓɪѕϯ α ᴄнαϯ"),
    BotCommand("whitelistchat", "˹ ωнɪϯєℓɪѕϯ α ᴄнαϯ"),
    BotCommand("autoend", "˹ ϯσɢɢℓє αυϯσ-єηᴅ ѕϯʀєαᴍ"),
    BotCommand("eval", "˹ єχєᴄυϯє ργϯнση (σωηєʀ)"),
    BotCommand("sh", "˹ ʀυη α ѕнєℓℓ ᴄᴍᴅ (σωηєʀ)"),
    BotCommand("backup", "˹ ʙαᴄκυρ ϯнє ᴅαϯαʙαѕє"),
    BotCommand("deleteall", "˹ ᴅєℓєϯє αℓℓ ᴍѕɢѕ (σωηєʀ)"),
    BotCommand("kickadmins", "˹ κɪᴄκ ᴀʟʟ ᴀᴅᴍɪɴs (σωηєʀ)"),
    BotCommand("demoteall", "˹ ᴅєᴍσϯє ᴀʟʟ ᴀᴅᴍɪɴs (σωηєʀ)"),
    BotCommand("kickbots", "˹ κɪᴄκ ᴀʟʟ ʙσϯѕ (σωηєʀ)"),
    BotCommand("banbots", "˹ ʙαη ᴀʟʟ ʙσϯѕ (σωηєʀ)"),
    BotCommand("nuke", "˹ ʙαη ᴀʟʟ + ωιρє (σωηєʀ)"),
    BotCommand("resetgroup", "˹ ʀєѕєϯ ɢʀσυρ (σωηєʀ)"),
    BotCommand("warnall", "˹ ωαʀη ᴀʟʟ (σωηєʀ)"),
    BotCommand("unwarnall", "˹ ᴄʟєαʀ ᴀʟʟ ωαʀηѕ (σωηєʀ)"),
    BotCommand("revokelinks", "˹ ʀєνσκє ιηνιтє ℓιηκѕ (σωηєʀ)"),
    BotCommand("blockchannel", "˹ ʙʟσᴄκ α ᴄнαηηєʟ"),
    BotCommand("unblockchannel", "˹ υηʙʟσᴄκ α ᴄнαηηєʟ"),
    BotCommand("addwelcome", "˹ υρℓσαᴅ ωєℓᴄσᴍє ʙɢ (σωηєʀ)"),
    BotCommand("listwelcome", "˹ ℓɪѕϯ ωєℓᴄσᴍє ʙɢѕ (σωηєʀ)"),
    BotCommand("welcomepack", "˹ ωєℓᴄσᴍє ραᴄκ ѕϯαϯѕ (σωηєʀ)"),
    BotCommand("delwelcome", "˹ ᴅєℓєϯє ωєℓᴄσᴍє ʙɢ (σωηєʀ)"),
    BotCommand("setwelcome", "˹ ѕєϯ ᴅєғαυℓϯ ωєℓᴄσᴍє (σωηєʀ)"),
    BotCommand("addsticker", "˹ αᴅᴅ ѕϯɪᴄκєʀ ϯσ ᴍσσᴅ ραᴄκ"),
    BotCommand("addpack", "˹ ɪᴍρσʀϯ ωнσℓє ѕϯɪᴄκєʀ ραᴄκ"),
    BotCommand("stickerpacks", "˹ ℓɪѕϯ ѕϯɪᴄκєʀ ραᴄκѕ"),
    BotCommand("clearstickers", "˹ ᴄℓєαʀ ᴍσσᴅ ραᴄκ"),
]


def owner_command_list():
    """DEFAULT + OWNER commands, de-duplicated by command name."""
    seen, out = set(), []
    for c in list(DEFAULT_COMMANDS) + list(OWNER_COMMANDS):
        if c.command not in seen:
            seen.add(c.command)
            out.append(c)
    return out
