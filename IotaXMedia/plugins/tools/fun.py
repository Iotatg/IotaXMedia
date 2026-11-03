# Authored By Iota Coders (fun & random commands)
# SPDX-License-Identifier: MIT
import httpx
from pyrogram import filters

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.decorators.language import language


async def _get(url: str, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()


@app.on_message(filters.command("joke"))
@language
async def joke(client, message, _):
    msg = await message.reply_text("😄 Fetching a joke...")
    try:
        data = await _get("https://v2.jokeapi.dev/joke/Any?safe-mode")
        if data.get("type") == "single":
            text = data.get("joke", "No joke found.")
        else:
            text = f"{data.get('setup', '')}\n\n**{data.get('delivery', '')}**"
        await msg.edit_text(f"😂 {text}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("fact"))
@language
async def fact(client, message, _):
    msg = await message.reply_text("🤔 Fetching a fact...")
    try:
        data = await _get("https://catfact.ninja/fact")
        await msg.edit_text(f"🐱 **Random Fact**\n\n{data.get('fact', 'N/A')}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("advice"))
@language
async def advice(client, message, _):
    msg = await message.reply_text("💭 Fetching advice...")
    try:
        data = await _get("https://api.adviceslip.com/advice")
        slip = data.get("slip", {})
        await msg.edit_text(f"💡 **Advice**\n\n{slip.get('advice', 'N/A')}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("excuse"))
@language
async def excuse(client, message, _):
    msg = await message.reply_text("🙄 Fetching an excuse...")
    try:
        data = await _get("https://excuser-three.vercel.app/v1/excuse")
        if isinstance(data, list) and data:
            data = data[0]
        await msg.edit_text(f"🙃 **Excuse**\n\n{data.get('excuse', 'N/A')}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("randomuser"))
@language
async def random_user(client, message, _):
    msg = await message.reply_text("👤 Generating random user...")
    try:
        data = await _get("https://randomuser.me/api/")
        user = data.get("results", [{}])[0]
        name = user.get("name", {})
        loc = user.get("location", {})
        dob = user.get("dob", {})
        text = (
            f"👤 **Random User**\n\n"
            f"🧑 Name: {name.get('title','')} {name.get('first','')} {name.get('last','')}\n"
            f"🚻 Gender: {user.get('gender', 'N/A')}\n"
            f"📧 Email: {user.get('email', 'N/A')}\n"
            f"📞 Phone: {user.get('phone', 'N/A')}\n"
            f"📍 City: {loc.get('city', 'N/A')}, {loc.get('country', 'N/A')}\n"
            f"🎂 Age: {dob.get('age', 'N/A')}"
        )
        pic = user.get("picture", {}).get("large")
        if pic:
            await msg.delete()
            await message.reply_photo(pic, caption=text)
        else:
            await msg.edit_text(text)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("name"))
@language
async def name_analysis(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /name <firstname>")
    name = message.command[1]
    msg = await message.reply_text("🔮 Analyzing name...")
    try:
        g = await _get(f"https://api.genderize.io/?name={name}")
        a = await _get(f"https://api.agify.io/?name={name}")
        n = await _get(f"https://api.nationalize.io/?name={name}")
        gender = g.get("gender")
        gender = f"{gender} ({g.get('probability', 0)*100:.1f}%)" if gender else "N/A"
        countries = n.get("country", [])
        country = ", ".join(
            f"{c['country_id']} ({c['probability']*100:.0f}%)" for c in countries[:3]
        ) or "N/A"
        await msg.edit_text(
            f"🔮 **Name Analysis** — {name}\n\n"
            f"🚻 Gender: {gender}\n"
            f"🎂 Avg Age: {a.get('age', 'N/A')}\n"
            f"🌍 Likely Country: {country}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("pokemon"))
@language
async def pokemon_info(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /pokemon <name>")
    name = message.command[1].lower()
    msg = await message.reply_text("🔍 Looking up Pokémon...")
    try:
        data = await _get(f"https://pokeapi.co/api/v2/pokemon/{name}")
        species = await _get(f"https://pokeapi.co/api/v2/pokemon-species/{name}")
        name_f = (data.get("species", {}).get("name", name)).capitalize()
        types = ", ".join(t["type"]["name"].capitalize() for t in data.get("types", []))
        abilities = ", ".join(
            a["ability"]["name"].replace("-", " ").capitalize()
            for a in data.get("abilities", [])[:2]
        )
        stats = {
            s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])
        }
        text = (
            f"⚡ **{name_f}** (#{data.get('id', '?')})\n\n"
            f"🎨 Type: {types}\n"
            f"✨ Abilities: {abilities}\n"
            f"⚖️ Height: {data.get('height', 0)/10:.1f} m\n"
            f"🏋️ Weight: {data.get('weight', 0)/10:.1f} kg\n"
            f"❤️ HP: {stats.get('hp', '?')}\n"
            f"⚔️ Attack: {stats.get('attack', '?')}\n"
            f"🛡 Defense: {stats.get('defense', '?')}"
        )
        sprite = data.get("sprites", {}).get("front_default")
        if sprite:
            await msg.delete()
            await message.reply_photo(sprite, caption=text)
        else:
            await msg.edit_text(text)
    except Exception as e:
        await msg.edit_text(f"❌ Pokémon not found or error: {e}")


@app.on_message(filters.command("trivia"))
@language
async def trivia(client, message, _):
    msg = await message.reply_text("🎯 Fetching a question...")
    try:
        data = await _get("https://opentdb.com/api.php?amount=1&type=multiple")
        results = data.get("results", [])
        if not results:
            return await msg.edit_text("❌ No question found.")
        q = results[0]
        import html as htmlmod

        question = htmlmod.unescape(q.get("question", "?"))
        category = q.get("category", "General")
        difficulty = q.get("difficulty", "medium").capitalize()
        correct = htmlmod.unescape(q.get("correct_answer", "?"))
        await msg.edit_text(
            f"🎯 **Trivia Question** ({category} — {difficulty})\n\n"
            f"❓ {question}\n\n"
            f"<tg-spoiler>✅ Answer: {correct}</tg-spoiler>"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("fortune"))
@language
async def fortune(client, message, _):
    msg = await message.reply_text("🔮 Reading your fortune...")
    try:
        data = await _get("https://fortuneapi.vercel.app/api/fortune")
        if isinstance(data, dict):
            text = data.get("fortune") or data.get("message") or "N/A"
        else:
            text = str(data)
        await msg.edit_text(f"🔮 **Fortune**\n\n{text}")
    except Exception:
        try:
            data = await _get("https://api.fortunecookieapi.com/v1/cookie")
            if isinstance(data, list) and data:
                item = data[0]
                fortune_txt = item.get("fortune", {}).get("message", "N/A")
                await msg.edit_text(f"🔮 **Fortune Cookie**\n\n{fortune_txt}")
            else:
                await msg.edit_text("❌ Could not fetch fortune.")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {e}")
