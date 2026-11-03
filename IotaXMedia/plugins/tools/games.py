# Authored By Iota Coders (games commands)
# SPDX-License-Identifier: MIT
import random

from pyrogram import filters

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.decorators.language import language


@app.on_message(filters.command("8ball") & (SUDOERS | filters.group))
@language
async def eight_ball(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /8ball <question>")
    question = " ".join(message.command[1:])
    answers = [
        "🎱 It is certain.",
        "🎱 It is decidedly so.",
        "🎱 Without a doubt.",
        "🎱 Yes — definitely.",
        "🎱 You may rely on it.",
        "🎱 As I see it, yes.",
        "🎱 Most likely.",
        "🎱 Outlook good.",
        "🎱 Yes.",
        "🎱 Signs point to yes.",
        "🎱 Reply hazy, try again.",
        "🎱 Ask again later.",
        "🎱 Better not tell you now.",
        "🎱 Cannot predict now.",
        "🎱 Concentrate and ask again.",
        "🎱 Don't count on it.",
        "🎱 My reply is no.",
        "🎱 My sources say no.",
        "🎱 Outlook not so good.",
        "🎱 Very doubtful.",
    ]
    await message.reply_text(f"🎱 **Magic 8-Ball**\n\n❓ {question}\n\n{random.choice(answers)}")


@app.on_message(filters.command("slots") & (SUDOERS | filters.group))
@language
async def slots(client, message, _):
    emojis = ["🍒", "🍋", "🍉", "🍇", "🔔", "⭐", "💎", "7️⃣"]
    roll = [random.choice(emojis) for _ in range(3)]
    if roll[0] == roll[1] == roll[2]:
        result = "🎉 JACKPOT! You win!"
    elif len(set(roll)) == 2:
        result = "✅ Two of a kind! Small win!"
    else:
        result = "❌ No match. Try again!"
    await message.reply_text(
        f"🎰 **Slot Machine**\n\n"
        f"` {roll[0]} | {roll[1]} | {roll[2]} `\n\n"
        f"{result}"
    )


@app.on_message(filters.command("flip") & (SUDOERS | filters.group))
@language
async def flip(client, message, _):
    result = random.choice(["Heads", "Tails"])
    await message.reply_text(f"🪙 **Coin Flip**\n\n🔄 You got: **{result}**")


@app.on_message(filters.command("roast") & (SUDOERS | filters.group))
@language
async def roast(client, message, _):
    roasts = [
        "You're not stupid; you just have bad luck thinking.",
        "If I had a dollar for every time you were right, I'd be broke.",
        "You're the reason they put instructions on shampoo bottles.",
        "Your brain is like the internet — full of useless information.",
        "You bring everyone so much joy when you leave the room.",
        "You're proof that evolution can go in reverse.",
        "I'd agree with you, but then we'd both be wrong.",
        "You're not a rocket scientist, but you sure can launch things.",
        "Somewhere out there, a tree is giving its life for your stupidity.",
        "You have the perfect face for radio.",
        "Your secrets are always safe with me. I never even listen when you tell me.",
        "If laughter is the best medicine, your face must be curing the world.",
    ]
    target = message.reply_to_message.from_user.first_name if message.reply_to_message and message.reply_to_message.from_user else "you"
    await message.reply_text(f"🔥 {target}, {random.choice(roasts)}")
