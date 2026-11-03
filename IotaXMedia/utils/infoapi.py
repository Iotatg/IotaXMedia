# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT


import aiohttp

_UA = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

_DNS_TYPES = {
    1: "A",
    2: "NS",
    5: "CNAME",
    6: "SOA",
    15: "MX",
    16: "TXT",
    28: "AAAA",
    33: "SRV",
    257: "CAA",
}


async def _get(url: str, timeout: int = 45):
    to = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=to, headers=_UA) as s:
        async with s.get(url) as r:
            if r.status != 200:
                raise RuntimeError(f"API HTTP {r.status}")
            return await r.json(content_type=None)


def _fmt_addr(d: dict) -> str:
    return (
        f"**ʙᴀɴᴋ:** {d.get('BANK', '—')}\n"
        f"**ʙʀᴀɴᴄʜ:** {d.get('BRANCH', '—')}\n"
        f"**ɪꜰꜱᴄ:** `{d.get('IFSC', '—')}`\n"
        f"**ᴀᴅᴅʀᴇꜱꜱ:** {d.get('ADDRESS', '—')}\n"
        f"**ᴄɪᴛʏ:** {d.get('CITY', '—')} | **ᴅɪꜱᴛ:** {d.get('DISTRICT', '—')}\n"
        f"**ꜱᴛᴀᴛᴇ:** {d.get('STATE', '—')} | **ᴄᴏɴᴛᴀᴄᴛ:** {d.get('CONTACT') or '—'}\n"
        f"**ᴜᴘɪ:** {'ʏᴇꜱ' if d.get('UPI') else 'ɴᴏ'} | "
        f"**ɴᴇꜰᴛ:** {'ʏᴇꜱ' if d.get('NEFT') else 'ɴᴏ'} | "
        f"**ʀᴛɢꜱ:** {'ʏᴇꜱ' if d.get('RTGS') else 'ɴᴏ'} | "
        f"**ɪᴍᴘꜱ:** {'ʏᴇꜱ' if d.get('IMPS') else 'ɴᴏ'}\n"
        f"**ᴍɪᴄʀ:** {d.get('MICR') or '—'} | **ꜱᴡɪꜰᴛ:** {d.get('SWIFT') or '—'}"
    )


async def ifsc_info(code: str) -> str:
    code = code.strip().upper()
    j = await _get(f"https://vercei-kappa.vercel.app/ifsc?code={code}")
    if not j.get("success"):
        raise RuntimeError("IFSC not found")
    return _fmt_addr(j["data"])


async def pincode_info(code: str) -> str:
    j = await _get(f"https://rack-pincodeapi.vercel.app/api?search={code.strip()}")
    recs = j.get("records") or []
    if j.get("status") != "success" or not recs:
        raise RuntimeError("Pincode not found")
    st = recs[0].get("state", "—")
    dt = recs[0].get("district", "—")
    lines = [f"**ǫ:** `{j.get('pincode', code)}` | **ꜱᴛᴀᴛᴇ:** {st} | **ᴅɪꜱᴛ:** {dt}"]
    lines.append(f"**ᴏꜰꜰɪᴄᴇꜱ ({len(recs)}):**")
    for r in recs[:12]:
        lines.append(
            f"• {r.get('office_name', '—')} — {r.get('branch_type', '')}"
            f" [{r.get('block') or r.get('region', '')}]"
        )
    if len(recs) > 12:
        lines.append(f"… ᴀɴᴅ {len(recs) - 12} ᴍᴏʀᴇ")
    return "\n".join(lines)


async def ip_info(ip: str) -> str:
    j = await _get(f"https://ip-dwy8.onrender.com/api/rackipapi?ip={ip.strip()}")
    res = j.get("results", {})
    best = {}
    for key in ("source_4_ipwhois", "source_1_ipapi_com", "source_3_ip_guide"):
        v = res.get(key)
        if isinstance(v, dict) and v.get("city"):
            best.update({k: v[k] for k in v if v.get(k)})
            break
    if not best:
        raise RuntimeError("No IP data available")
    return (
        f"**ɪᴘ:** `{j.get('ip', ip)}`\n"
        f"**ᴄɪᴛʏ:** {best.get('city', '—')}\n"
        f"**ʀᴇɢɪᴏɴ:** {best.get('region', '—')}\n"
        f"**ᴄᴏᴜɴᴛʀʏ:** {best.get('country', '—')}\n"
        f"**ᴢɪᴘ:** {best.get('zip', best.get('postal', '—'))}\n"
        f"**ɪꜱᴘ:** {best.get('isp', '—')}"
        + (f"\n**ᴀꜱɴ:** {best['asn']}" if best.get("asn") else "")
    )


async def dns_lookup(domain: str) -> str:
    domain = domain.strip().replace("https://", "").replace("http://", "").rstrip("/")
    j = await _get(f"https://rack-72au.onrender.com/dns-lookup?q={domain}")
    if not j.get("success") or j.get("data", {}).get("Status") != 0:
        raise RuntimeError("DNS lookup failed")
    ans = j["data"].get("Answer") or []
    if not ans:
        raise RuntimeError("No DNS records found")
    groups = {}
    for a in ans[:60]:
        t = _DNS_TYPES.get(a.get("type"), str(a.get("type")))
        groups.setdefault(t, []).append(a.get("data", ""))
    order = ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "CAA", "SRV"]
    lines = [f"**ᴅᴏᴍᴀɪɴ:** `{domain}`"]
    for t in order + [k for k in groups if k not in order]:
        if t not in groups:
            continue
        vals = groups[t][:6]
        shown = ", ".join(f"`{v}`" for v in vals)
        extra = f" (+{len(groups[t]) - 6})" if len(groups[t]) > 6 else ""
        lines.append(f"**{t}:** {shown}{extra}")
    return "\n".join(lines)


async def weather(city: str) -> str:
    j = await _get(
        "https://rack-weather.vercel.app/api/weather/"
        + city.strip().replace(" ", "%20"),
        timeout=30,
    )
    if not j.get("success"):
        raise RuntimeError("City not found")
    c, cur = j["data"]["city"], j["data"]["current"]
    t, atm, w = cur["temperature"], cur["atmosphere"], cur["wind"]
    uv = cur.get("uv", {})
    fc = j["data"].get("forecast", {}).get("hourly_next_24h") or []
    nxt = ""
    if len(fc) >= 9:
        pick = fc[8]
        nxt = (
            f"\n\n**+9ʜ:** {pick['temperature_2m']}°ᴄ,"
            f" {pick['weather']['description']},"
            f" ☔ {pick.get('precipitation_probability', 0)}%"
        )
    return (
        f"**{c['name']}, {c.get('country', '')}**\n"
        f"{cur['weather']['description']} | {cur.get('time', '')}\n\n"
        f"**ᴛᴇᴍᴘ:** {t['actual_c']}°ᴄ (ꜰᴇᴇʟꜱ {t['feels_like_c']}°ᴄ)\n"
        f"**ʜᴜᴍɪᴅɪᴛʏ:** {atm['humidity_percent']}% ({atm.get('humidity_level', '')})\n"
        f"**ᴡɪɴᴅ:** {w['speed_kmh']} ᴋᴍ/ʜ {w.get('direction_label', '')}"
        f" (ɢᴜꜱᴛꜱ {w.get('gusts_kmh', '—')})\n"
        f"**ᴠɪꜱɪʙɪʟɪᴛʏ:** {round(atm['visibility_m'] / 1000, 1)} ᴋᴍ"
        f" ({atm.get('visibility_level', '')})\n"
        f"**ᴘʀᴇꜱꜱᴜʀᴇ:** {atm['pressure_msl_hpa']} ʜᴘᴀ\n"
        f"**ᴜᴠ:** {uv.get('uv_index', '—')} ({uv.get('risk_level', '—')})"
        + nxt
    )


async def aqi_info(city: str) -> str:
    j = await _get(
        "https://rack-aqiinfos.vercel.app/api/aqi/" + city.strip().replace(" ", "%20"),
        timeout=30,
    )
    if not j.get("success"):
        raise RuntimeError("City not found")
    d = j["data"]
    a = d.get("us_aqi") or {}
    br = a.get("breakdown", {}) or {}
    city_name = (d.get("city") or {}).get("name", city)
    return (
        f"**ᴀǫɪ — {city_name}**\n"
        f"**ᴜꜱ ᴀǫɪ:** {a.get('value', '—')} ({a.get('level', '—')})\n\n"
        f"**ᴘᴍ2.5:** {br.get('pm2_5', '—')} | **ᴘᴍ10:** {br.get('pm10', '—')}\n"
        f"**ᴏᴢᴏɴᴇ:** {br.get('ozone', '—')} | **ɴᴏ2:** {br.get('nitrogen_dioxide', '—')}\n"
        f"**ꜱᴏ2:** {br.get('sulphur_dioxide', '—')} | **ᴄᴏ:** {br.get('carbon_monoxide', '—')}\n\n"
        f"**ᴀᴅᴠɪᴄᴇ:** {a.get('health_advice', '—')}"
    )


async def git_info(username: str) -> str:
    u = username.strip().lstrip("@")
    to = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=to, headers=_UA) as s:
        async with s.get(f"https://api.github.com/users/{u}") as r:
            if r.status == 404:
                raise RuntimeError("User not found")
            if r.status != 200:
                raise RuntimeError(f"GitHub HTTP {r.status}")
            d = await r.json()
        async with s.get(d.get("repos_url", ""), params={"sort": "updated", "per_page": 5}) as r:
            repos = (await r.json()) if r.status == 200 else []
    lines = [
        f"**ɢɪᴛʜᴜʙ — {d.get('login', u)}**",
        d.get("bio") or "",
        "",
        f"**ɴᴀᴍᴇ:** {d.get('name') or '—'} | **ʟᴏᴄ:** {d.get('location') or '—'}",
        f"**ʀᴇᴘᴏꜱ:** {d.get('public_repos', 0)} | "
        f"**ɢɪꜱᴛꜱ:** {d.get('public_gists', 0)} | "
        f"**ꜰᴏʟʟᴏᴡᴇʀꜱ:** {d.get('followers', 0)} | "
        f"**ꜰᴏʟʟᴏᴡɪɴɢ:** {d.get('following', 0)}",
        f"**ᴊᴏɪɴᴇᴅ:** {str(d.get('created_at', ''))[:10]}",
        f"**ᴜʀʟ:** https://github.com/{d.get('login', u)}",
    ]
    if repos and isinstance(repos, list):
        lines.append("")
        lines.append("**ʀᴇᴄᴇɴᴛ ʀᴇᴘᴏꜱ:**")
        for rp in repos[:5]:
            star = rp.get("stargazers_count", 0)
            desc = (rp.get("description") or "")[:40]
            lines.append(f"• [{rp.get('name', '?')}]({rp.get('html_url', '')}) ⭐{star} {desc}")
    return "\n".join(x for x in lines if x != "" or True)


def usage(cmd: str, example: str) -> str:
    return (
        f"**ᴜꜱᴀɢᴇ:** `/{cmd} {example.split()[0]}`\n"
        f"**ᴇx:** `/{cmd} {example}`"
    )
