#!/usr/bin/env python3
"""
🎬 YouTube Downloader Telegram Bot - إصدار محسن
"""

import telebot
import yt_dlp
import os
import threading
import time
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== الإعدادات ==========
BOT_TOKEN = "7973816129:AAG_yhU_WnzdI4RPoGRZ5FI732QU7pvRP5s" 
DOWNLOAD_FOLDER = "downloads"
MAX_FILE_SIZE = 2000  # 2GB

# ========== إنشاء البوت ==========
bot = telebot.TeleBot(BOT_TOKEN)

# ========== إنشاء المجلدات ==========
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    print(f"✅ تم إنشاء مجلد: {DOWNLOAD_FOLDER}")

# ========== دوال مساعدة ==========

def is_youtube_url(url):
    """التحقق من رابط يوتيوب"""
    return any(x in url for x in ["youtube.com", "youtu.be", "youtube.com/shorts"])

def get_video_info(url):
    """جلب معلومات الفيديو"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs'],
                }
            },
            'socket_timeout': 30,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'فيديو'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'formats': info.get('formats', [])
            }
    except Exception as e:
        print(f"❌ خطأ في جلب معلومات الفيديو: {e}")
        return None

def get_quality_options(formats):
    """استخراج خيارات الجودة"""
    qualities = []
    
    # فيديو مع صوت
    for f in formats:
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
            if f.get('height'):
                quality = f"{f['height']}p"
                if f.get('ext'):
                    quality += f" ({f['ext'].upper()})"
                qualities.append((quality, f['format_id']))
    
    # صوت فقط
    for f in formats:
        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
            ext = f.get('ext', 'mp3')
            qualities.append((f"🎵 MP3 ({ext.upper()})", f['format_id']))
    
    # إزالة التكرارات
    unique_qualities = []
    seen = set()
    for q in qualities:
        if q[1] not in seen:
            seen.add(q[1])
            unique_qualities.append(q)
    
    return unique_qualities[:6]

# ========== أوامر البوت ==========

@bot.message_handler(commands=['start'])
def start_cmd(message):
    """أمر البدء"""
    name = message.from_user.first_name or "صديق"
    
    text = f"""
🎬 <b>مرحباً {name}!</b>

🤖 <b>بوت تحميل اليوتيوب</b>

📌 <b>طريقة الاستخدام:</b>
1. أرسل رابط فيديو يوتيوب
2. اختر الجودة
3. انتظر التحميل

⚡ <b>المميزات:</b>
• تحميل مجاني
• جميع الجودات
• تحويل لـ MP3

👇 <b>أرسل رابط يوتيوب الآن</b>
    """
    
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    """مساعدة"""
    text = """
🆘 <b>مساعدة</b>

🔗 <b>أرسل رابط يوتيوب:</b>
• youtube.com/watch?v=...
• youtu.be/...
• youtube.com/shorts/...

🎛️ <b>الأوامر:</b>
/start - بدء البوت
/help - المساعدة

📞 <b>الدعم:</b>
@SupportChannel
    """
    bot.reply_to(message, text, parse_mode="HTML")

# ========== معالجة الروابط ==========

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """معالجة جميع الرسائل"""
    url = message.text.strip()
    
    # تحقق من رابط يوتيوب
    if not is_youtube_url(url):
        return
    
    # جلب معلومات الفيديو
    info = get_video_info(url)
    if not info:
        bot.reply_to(message, "❌ <b>تعذر جلب معلومات الفيديو!</b>\nجرب رابط آخر أو اختبر الرابط في متصفحك أولاً.")
        return
    
    # إنشاء خيارات الجودة
    qualities = get_quality_options(info['formats'])
    if not qualities:
        bot.reply_to(message, "❌ <b>لا توجد جودة متاحة!</b>")
        return
    
    # إنشاء لوحة المفاتيح
    markup = InlineKeyboardMarkup(row_width=2)
    
    for name, quality_id in qualities:
        callback_data = f"dl_{quality_id}_{url}"
        markup.add(InlineKeyboardButton(name, callback_data=callback_data))
    
    # معلومات الفيديو
    duration = info['duration']
    duration_text = f"{duration//60}:{duration%60:02d}"
    
    caption = f"""
📹 <b>{info['title'][:50]}...</b>

⏱️ المدة: {duration_text}
👇 <b>اختر الجودة:</b>
    """
    
    # إرسال
    if info['thumbnail']:
        try:
            bot.send_photo(
                message.chat.id,
                info['thumbnail'],
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except:
            bot.reply_to(message, caption, reply_markup=markup, parse_mode="HTML")
    else:
        bot.reply_to(message, caption, reply_markup=markup, parse_mode="HTML")

# ========== معالجة اختيار الجودة ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def handle_quality(call):
    """معالجة اختيار الجودة"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # استخراج البيانات
    parts = call.data.split("_", 2)
    if len(parts) != 3:
        return
    
    quality_id = parts[1]
    url = parts[2]
    
    # تحديث الرسالة
    bot.edit_message_text(
        "⏳ <b>جاري التحضير...</b>",
        chat_id,
        message_id,
        parse_mode="HTML"
    )
    
    # بدء التنزيل في خيط منفصل
    thread = threading.Thread(
        target=download_and_send,
        args=(chat_id, message_id, url, quality_id)
    )
    thread.start()
    
    bot.answer_callback_query(call.id, "بدأ التحميل!")

def download_and_send(chat_id, message_id, url, quality_id):
    """تنزيل وإرسال الفيديو"""
    try:
        bot.edit_message_text(
            "⬇️ <b>جاري التحميل...</b>\n⏳ الرجاء الانتظار...",
            chat_id,
            message_id,
            parse_mode="HTML"
        )
        
        # اسم الملف
        timestamp = int(time.time())
        filename = f"video_{timestamp}"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # إعدادات التنزيل المحسنة
        ydl_opts = {
            'format': quality_id,
            'outtmpl': filepath + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'max_filesize': MAX_FILE_SIZE * 1024 * 1024,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'socket_timeout': 120,
            'retries': 10,
            'fragment_retries': 10,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
        }
        
        # التنزيل
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = ydl.prepare_filename(info)
        
        # إرسال الملف
        bot.edit_message_text(
            "📤 <b>جاري الإرسال...</b>",
            chat_id,
            message_id,
            parse_mode="HTML"
        )
        
        with open(final_file, 'rb') as file:
            if quality_id.startswith("bestaudio") or "140" in quality_id or "audio" in quality_id.lower():
                bot.send_audio(chat_id, file, title=info.get('title', 'Audio'))
            else:
                bot.send_video(chat_id, file)
        
        # حذف الرسالة الأصلية
        bot.delete_message(chat_id, message_id)
        
        # رسالة النجاح
        bot.send_message(
            chat_id,
            "✅ <b>تم التحميل بنجاح!</b>\n\nأرسل رابط آخر للتحميل",
            parse_mode="HTML"
        )
        
        # تنظيف الملف
        try:
            os.remove(final_file)
        except:
            pass
        
    except Exception as e:
        error_msg = str(e)
        bot.edit_message_text(
            f"❌ <b>حدث خطأ:</b>\n{error_msg[:100]}",
            chat_id,
            message_id,
            parse_mode="HTML"
        )

# ========== تشغيل البوت ==========

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    print("\n" + "="*50)
    print("🎬 YouTube Downloader Telegram Bot")
    print("🚀 البوت يعمل...")
    print("="*50 + "\n")
    
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'فيديو'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', '')
            }
    except:
        return None

# ========== أوامر البوت ==========

@bot.message_handler(commands=['start'])
def start_cmd(message):
    """أمر البدء"""
    name = message.from_user.first_name or "صديق"
    
    text = f"""
🎬 <b>مرحباً {name}!</b>

🤖 <b>بوت تحميل اليوتيوب المجاني</b>

📌 <b>كيفية الاستخدام:</b>
1. أرسل رابط فيديو يوتيوب
2. اختر الجودة المفضلة
3. انتظر حتى يكتمل التحميل

⚡ <b>المميزات:</b>
• تحميل مجاني وغير محدود
• جميع الجودات متاحة
• تحويل لـ MP3
• سريع وسهل

👇 <b>أرسل رابط يوتيوب الآن</b>
    """
    
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    """مساعدة"""
    text = """
🆘 <b>مساعدة</b>

🔗 <b>أرسل أي رابط يوتيوب:</b>
• youtube.com/watch?v=...
• youtu.be/...
• youtube.com/shorts/...

🎛️ <b>الأوامر:</b>
/start - بدء البوت
/help - هذه الرسالة

🚫 <b>ملاحظة:</b>
• البوت مجاني بالكامل
• لا يوجد اشتراك مطلوب
• لا يوجد حدود للتحميل
    """
    bot.reply_to(message, text, parse_mode="HTML")

# ========== معالجة الروابط ==========

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """معالجة جميع الرسائل"""
    url = message.text.strip()
    
    # تحقق من رابط يوتيوب
    if not is_youtube_url(url):
        return
    
    # جلب معلومات الفيديو
    info = get_video_info(url)
    if not info:
        bot.reply_to(message, "❌ <b>تعذر جلب معلومات الفيديو!</b>")
        return
    
    # لوحة اختيار الجودة
    markup = InlineKeyboardMarkup(row_width=2)
    
    # خيارات الجودة
    qualities = [
        ("🎬 1080p", "137+140"),
        ("🎬 720p", "22"),
        ("🎬 480p", "135"),
        ("🎬 360p", "18"),
        ("🎵 MP3 عالي", "bestaudio[ext=m4a]"),
        ("🎵 MP3 متوسط", "140")
    ]
    
    # إضافة الأزرار
    for text, quality_id in qualities:
        callback_data = f"dl_{quality_id}_{url}"
        markup.add(InlineKeyboardButton(text, callback_data=callback_data))
    
    # معلومات الفيديو
    duration = info['duration']
    duration_text = f"{duration//60}:{duration%60:02d}"
    
    caption = f"""
📹 <b>{info['title'][:50]}...</b>

⏱️ المدة: {duration_text}
👇 <b>اختر الجودة:</b>
    """
    
    # إرسال
    if info['thumbnail']:
        try:
            bot.send_photo(
                message.chat.id,
                info['thumbnail'],
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except:
            bot.reply_to(message, caption, reply_markup=markup, parse_mode="HTML")
    else:
        bot.reply_to(message, caption, reply_markup=markup, parse_mode="HTML")

# ========== معالجة اختيار الجودة ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def handle_quality(call):
    """معالجة اختيار الجودة"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # استخراج البيانات
    parts = call.data.split("_", 2)
    if len(parts) != 3:
        return
    
    quality_id = parts[1]
    url = parts[2]
    
    # تحديث الرسالة
    bot.edit_message_text(
        "⏳ <b>جاري التحضير للتحميل...</b>",
        chat_id,
        message_id,
        parse_mode="HTML"
    )
    
    # بدء التنزيل في خيط منفصل
    thread = threading.Thread(
        target=download_and_send,
        args=(chat_id, message_id, url, quality_id)
    )
    thread.start()
    
    bot.answer_callback_query(call.id, "بدأ التحميل!")

def download_and_send(chat_id, message_id, url, quality_id):
    """تنزيل وإرسال الفيديو"""
    try:
        # تحديث حالة التنزيل
        bot.edit_message_text(
            "⬇️ <b>جاري تحميل الفيديو...</b>\n⏳ الرجاء الانتظار...",
            chat_id,
            message_id,
            parse_mode="HTML"
        )
        
        # اسم الملف
        timestamp = int(time.time())
        filename = f"video_{timestamp}"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # إعدادات التنزيل
        ydl_opts = {
            'format': quality_id,
            'outtmpl': filepath + '.%(ext)s',
            'quiet': True,
            'max_filesize': MAX_FILE_SIZE * 1024 * 1024,
        }
        
        # التنزيل
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = ydl.prepare_filename(info)
        
        # إرسال الملف
        bot.edit_message_text(
            "📤 <b>جاري إرسال الفيديو إليك...</b>",
            chat_id,
            message_id,
            parse_mode="HTML"
        )
        
        with open(final_file, 'rb') as file:
            if quality_id.startswith("bestaudio") or "140" in quality_id:
                bot.send_audio(chat_id, file)
            else:
                bot.send_video(chat_id, file)
        
        # حذف الرسالة الأصلية
        bot.delete_message(chat_id, message_id)
        
        # رسالة النجاح
        bot.send_message(
            chat_id,
            "✅ <b>تم التحميل بنجاح!</b>\n\nأرسل رابط آخر للتحميل",
            parse_mode="HTML"
        )
        
        # تنظيف الملف
        try:
            os.remove(final_file)
        except:
            pass
        
    except Exception as e:
        error_msg = str(e)
        bot.edit_message_text(
            f"❌ <b>حدث خطأ أثناء التحميل:</b>\n{error_msg[:100]}",
            chat_id,
            message_id,
            parse_mode="HTML"
        )

# ========== تشغيل البوت ==========

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    print("\n" + "="*50)
    print("🎬 YouTube Downloader Telegram Bot")
    print("📱 إصدار مبسط بدون اشتراك")
    print("="*50)
    print("⚡ المميزات:")
    print("• تحميل مجاني وغير محدود")
    print("• جميع الجودات متاحة")
    print("• تحويل لـ MP3")
    print("="*50)
    print("🚀 البوت يعمل... (اضغط Ctrl+C لإيقاف)")
    print("="*50 + "\n")
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت")
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()
