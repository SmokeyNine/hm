import os, logging, asyncio, io, sys, traceback
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from git import Repo
from os import environ, execle
import sys
from git.exc import GitCommandError, InvalidGitRepositoryError
from datetime import datetime
from urllib.parse import urlparse
from inspect import getfullargspec
from pyrogram import Client, filters 
from pyrogram.types import ChatPermissions
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import bot_token, sudoers, root, WELCOME_DELAY_KICK_SEC

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - [%(levelname)s] - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# --- STARTING BOT --- #
api_id = int(os.environ.get("APP_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("TOKEN")
auth_chts = set(int(x) for x in os.environ.get("AUTH_USERS", "").split())
banned_usrs = set(int(x) for x in os.environ.get("BANNED_USRS", "").split())
client = TelegramClient('client', api_id, api_hash).start(bot_token=bot_token)
app = Client(
    'bot',
    api_id=os.environ.get('APP_ID'),
    api_hash=os.environ['API_HASH'],
    bot_token=os.environ['TOKEN'])


#/start
@app.on_message(filters.command(["start"]))
async def start(_, message):
    await message.reply_text(f"Hello {message.from_user.mention}, Ok bye now go sleep you've tested enough bots for today...")

    
    # --- BAN --- #
@client.on(events.NewMessage(pattern="/ban"))
async def banE(event):
    k = await event.get_reply_message()
    banned_usrs.append(k.from_id.user_id)
# --- PINGING BOT --- #
@client.on(events.NewMessage(pattern="/ping"))
async def pingE(event):
    start = datetime.now()
    catevent = await event.respond("`!....`")
    await asyncio.sleep(0.3)
    await catevent.edit("`..!..`")
    await asyncio.sleep(0.3)
    await catevent.edit("`....!`")
    end = datetime.now()
    tms = (end - start).microseconds / 1000
    ms = round((tms - 0.6) / 3, 3)
    await catevent.edit(f"Pong!\n`{ms} ms`")
    LOGGER.info("Bot Pinging")

# --- UPDATE BOT --- #
@client.on(events.NewMessage(pattern="/gitpull"))
async def updateE(event):
    if not event.sender_id in auth_chts:
        return
    try:
     repo = Repo()
    except InvalidGitRepositoryError:
     repo = Repo.init()
     origin = repo.create_remote("upstream", "https://github.com/Solo-Dragon/Syltron")
     origin.fetch()
     repo.create_head("master", origin.refs.master)
     repo.heads.master.set_tracking_branch(origin.refs.master)
     repo.heads.master.checkout(True)
    repo.create_remote("upstream", 'https://github.com/Solo-Dragon/Syltron')
    ac_br = repo.active_branch.name
    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)
    try:
            ups_rem.pull(ac_br)
    except GitCommandError:
            repo.git.reset("--hard", "FETCH_HEAD")
    args = [sys.executable, "main.py"]
    execle(sys.executable, *args, environ)


    
# --- RESTART BOT --- #
@client.on(events.NewMessage(pattern="/arise"))
async def restartE(event):
    if not event.sender_id in auth_chts:
        return
    await event.respond("Retracing Back into Shadows.... Restaring")
    executable = sys.executable.replace(" ", "\\ ")
    args = [executable, "main.py"]
    os.execle(executable, *args, os.environ)
    sys.exit(0)
    LOGGER.info("Bot Restarting")

# --- EVAL DEF HERE --- #
async def aexec(code, smessatatus):
    message = event = smessatatus
    p = lambda _x: print(_format.yaml_format(_x))
    reply = await event.get_reply_message()
    exec(
        f"async def __aexec(message, event , reply, client, p, chat): "
        + "".join(f"\n {l}" for l in code.split("\n"))
    )
    return await locals()["__aexec"](
        message, event, reply, message.client, p, message.chat_id
    )
 
# --- EVAL EVENT HERE --- # 
@client.on(events.NewMessage(chats=auth_chts, pattern="/eval ?(.*)"))
async def evalE(event):
    if event.sender_id in banned_usrs:
        return await event.respond("You have been exemted from my authority")
    cmd = "".join(event.message.message.split(maxsplit=1)[1:])
    if not cmd:
        return
    cmd = (
        cmd.replace("send_message", "send_message")
        .replace("send_file", "send_file")
        .replace("edit_message", "edit_message")
    )
    catevent = await event.respond("`Running ...`")
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        t = asyncio.create_task(aexec(cmd, event))
        await t
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = (
        f"**•  Eval : **\n```{cmd}``` \n\n**•  Result : **\n```{evaluation}``` \n"
    )
    try:
        await catevent.edit(final_output)
    except:
        with io.open("output.txt", "w", encoding="utf-8") as k:
            k.write(str(final_output).replace("`", "").replace("*", ""))
            k.close()
        await event.client.send_file(event.chat_id, "output.txt")
        os.remove('output.txt')
        await catevent.delete()
    LOGGER.info(f"Eval: {cmd}\nExcute by: {event.sender_id}")

# --- BASH DEF HERE --- #
async def bash(cmd):

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    err = stderr.decode().strip()
    out = stdout.decode().strip()
    return out, err

  
  
@app.on_message(filters.command("info"))
async def info(_, message):
    try:
        victim = message.reply_to_message.from_user.id
        chat_id = message.chat.id
        info_user = await app.get_chat_member(chat_id, victim)
        await message.reply_text(info_user)
    except Exception as e:
        await message.reply_text(str(e))

        
@app.on_message(filters.new_chat_members & ~filters.chat("@Levelling_chat"))
async def welcome(_, message: Message):
    """Mute new member and send message with button"""
    new_members = [f"{u.mention}" for u in message.new_chat_members]
    text = (f"Welcome, {', '.join(new_members)}\n**Are you human?**\n"
            "You will be removed from this chat if you are not verified "
            f"in {WELCOME_DELAY_KICK_SEC} seconds")
    await message.chat.restrict_member(message.from_user.id, ChatPermissions())
    button_message = await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Press Here to Verify",
                        callback_data="pressed_button"
                    )
                ]
            ]
        ),
        quote=True
    )
    await message.reply_animation("CgACAgIAAx0CVsThkQABAsD8Ybs-GL3regFniHZpNzwQGe9aU3MAApgRAAJdrMFIb82stu3-1C8jBA")
    await kick_restricted_after_delay(WELCOME_DELAY_KICK_SEC, button_message)  
  
        
        
@app.on_callback_query(filters.regex("pressed_button"))
async def callback_query_welcome_button(_, callback_query):
    """After the new member presses the button, set his permissions to
    chat permissions, delete button message and join message
    """
    button_message = callback_query.message
    join_message = button_message.reply_to_message
    pending_user = join_message.from_user
    pending_user_id = pending_user.id
    pressed_user_id = callback_query.from_user.id
    if pending_user_id == pressed_user_id:
        await callback_query.answer("Congrats, captcha passed!")
        await button_message.chat.unban_member(pending_user_id)
        await button_message.delete()
    else:
        await callback_query.answer("This is not for you")
        
async def kick_restricted_after_delay(delay, button_message: Message):
    """If the new member is still restricted after the delay, delete
    button message and join message and then kick him
    """
    await asyncio.sleep(delay)
    join_message = button_message.reply_to_message
    group_chat = button_message.chat
    user_id = join_message.from_user.id
    await join_message.delete()
    await button_message.delete()
    await _ban_restricted_user_until_date(group_chat, user_id, duration=delay)


@app.on_message(filters.left_chat_member)
async def left_chat_member(_, message: Message):
    """When a restricted member left the chat, ban him for a while"""
    group_chat = message.chat
    user_id = message.left_chat_member.id
    await _ban_restricted_user_until_date(group_chat, user_id,
                                          duration=WELCOME_DELAY_KICK_SEC)


async def _ban_restricted_user_until_date(group_chat,
                                          user_id: int,
                                          duration: int):
    try:
        member = await group_chat.get_member(user_id)
        if member.status == "restricted":
            until_date = int(datetime.utcnow().timestamp() + duration)
            await group_chat.kick_member(user_id, until_date=until_date)
    except UserNotParticipant:
        pass

# eval
async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {a}" for a in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)




async def edit_or_reply(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})
                
# --- BASH EVENT HERE --- #
@client.on(events.NewMessage(chats=auth_chts, pattern="/bash ?(.*)"))
async def bashE(event):
    if event.sender_id in banned_usrs:
        return await event.respond("You are Banned!")
    cmd = "".join(event.message.message.split(maxsplit=1)[1:])
    oldmsg = await event.respond("`Running...`")
    out, err = await bash(cmd)
    LOGGER.info(f"Bash: {cmd}\nExcute by: {event.sender_id}")
    if not out:
        out = None
    elif not err:
        err = None
    try:
        await oldmsg.edit(f'**CMD:** `{cmd}`\n**ERROR:**\n `{err}`\n**OUTPUT:**\n `{out}`')
    except:
        with io.open("output.txt", "w", encoding="utf-8") as k:
            k.write(f'CMD: {cmd}\nERROR:\n {err}\nOUTPUT:\n {out}')
            k.close()
        await event.client.send_file(event.chat_id, "output.txt", reply_to=event)
        os.remove('output.txt')
        await oldmsg.delete()

print("Arise")
print("The Shadow are awaiting your orders")
client.send_message(1023483367, "Here master")
os.system("python -V")

def main () :
  client.run_until_disconnected()
  app.run()

if __name__ == "__main__":
  main()    
    
