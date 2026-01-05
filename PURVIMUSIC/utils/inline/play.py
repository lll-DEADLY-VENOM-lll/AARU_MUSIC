import math
from pyrogram.types import InlineKeyboardButton
from PURVIMUSIC.utils.formatters import time_to_seconds

def track_markup(_, videoid, user_id, channel, fplay):
    # Translation keys check karein ki config mein P_B_1/P_B_2 hain ya nahi
    btn_audio = _["P_B_1"] if "P_B_1" in _ else "🎵 Audio"
    btn_video = _["P_B_2"] if "P_B_2" in _ else "🎥 Video"
    
    buttons = [
        [
            InlineKeyboardButton(
                text=btn_audio,
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=btn_video,
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="✨ Playlist", 
                callback_data=f"add_playlist {videoid}",
            ),
            InlineKeyboardButton(
                text="🗑 Close",
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons

def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    
    # Progress Bar Fix
    bar_length = 10
    if duration_sec > 0:
        percentage = (played_sec / duration_sec) * bar_length
    else:
        percentage = 0
    
    umm = math.floor(percentage)
    if umm > bar_length: umm = bar_length
    
    # Bar drawing logic fix
    bar = "━" * umm + "🔘" + "━" * (bar_length - umm)
    
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(text="▷ Resume", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II Pause", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="⏭ Skip", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢ Stop", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="✨ Playlist", callback_data=f"add_playlist {chat_id}"),
            InlineKeyboardButton(text="🗑 Close", callback_data="close")
        ],
    ]
    return buttons

def stream_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷ Resume", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II Pause", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="⏭ Skip", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢ Stop", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [InlineKeyboardButton(text="🗑 Close", callback_data="close")],
    ]
    return buttons

def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    # Callback data 64 byte limit cross na kare isliye query ko chhota rakha hai
    short_query = f"{query[:15]}" 
    
    btn_audio = _["P_B_1"] if "P_B_1" in _ else "🎵 Audio"
    btn_video = _["P_B_2"] if "P_B_2" in _ else "🎥 Video"

    buttons = [
        [
            InlineKeyboardButton(
                text=btn_audio,
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=btn_video,
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❮",
                callback_data=f"slider B|{query_type}|{short_query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text="🗑 Close",
                callback_data=f"forceclose {short_query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="❯",
                callback_data=f"slider F|{query_type}|{short_query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons 
