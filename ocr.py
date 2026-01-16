import re
import cv2
import pytesseract
import numpy as np
import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TimedOut, NetworkError

#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
BOT_TOKEN = "8591495285:AAGg6UU7LaAjy95r-OT6s3xYx8M6ZBh7Z8I"

UPI_REGEX = re.compile(
    r'[a-zA-Z0-9._-]{3,}@[a-zA-Z0-9._\-|\\\/IlL]{2,}',
    re.IGNORECASE
)

user_photos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        " UPI ID Remover Bot\n\n Send me photos with UPI IDs\n I'll confirm each photo received\n Click 'Process All' when ready\n All processed photos sent together!"
    )

def create_progress_bar(current, total, length=10):
    filled = int(length * current / total)
    bar = "" * filled + "" * (length - filled)
    percent = int(100 * current / total)
    return f"[{bar}] {percent}% ({current}/{total})"

async def collect_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    
    if user_id not in user_photos:
        user_photos[user_id] = []
    
    user_photos[user_id].append(photo.file_id)
    
    keyboard = [[InlineKeyboardButton(" Process All Photos", callback_data="process_all")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f" Photo {len(user_photos[user_id])} received!\n\n Total photos: {len(user_photos[user_id])}\nSend more photos or click 'Process All'",
        reply_markup=reply_markup
    )

async def process_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_photos or len(user_photos[user_id]) == 0:
        await query.edit_message_text(" No photos to process!")
        return
    
    total_photos = len(user_photos[user_id])
    progress_msg = await query.edit_message_text(
        f" Starting...\n{create_progress_bar(0, total_photos)}\n\nUPI IDs found: 0"
    )
    
    total_masked = 0
    processed_files = []
    
    for idx, file_id in enumerate(user_photos[user_id], 1):
        try:
            progress_text = f" Processing photo {idx}/{total_photos}...\n{create_progress_bar(idx, total_photos)}\n\n UPI IDs found: {total_masked}"
            try:
                await progress_msg.edit_text(progress_text)
            except:
                pass
            
            file = await context.bot.get_file(file_id)
            input_file = f"input_{user_id}_{idx}.jpg"
            
            for attempt in range(3):
                try:
                    await asyncio.wait_for(file.download_to_drive(input_file), timeout=30.0)
                    break
                except (TimedOut, asyncio.TimeoutError):
                    if attempt == 2:
                        print(f"[SKIP] Photo {idx} - download timeout")
                        continue
                    await asyncio.sleep(2)
            
            img = cv2.imread(input_file)
            if img is None:
                print(f"[SKIP] Photo {idx} - failed to load")
                continue
            
            print(f"\n[OCR] Processing photo {idx}/{total_photos}...")
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Debug: Show all detected text
            all_detected = []
            for i in range(len(data["text"])):
                t = data["text"][i].strip()
                if t:
                    all_detected.append(t)
            print(f"[DEBUG] Detected text: {' | '.join(all_detected[:30])}")
            
            # Track masked regions to avoid duplicates
            masked_regions = []
            
            # Strategy 1: Check each detected text for complete UPI IDs
            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                if not text:
                    continue
                
                clean_text = text.replace(" ", "").replace("\n", "")
                
                # Match complete UPI IDs (username@provider format)
                is_complete_upi = UPI_REGEX.search(clean_text)
                
                # Must have at least 3 characters before @
                has_username = False
                if '@' in clean_text:
                    parts = clean_text.split('@')
                    if len(parts) == 2 and len(parts[0]) >= 3 and parts[1]:
                        has_username = True
                
                print(f"[CHECK] '{clean_text}' - UPI:{is_complete_upi is not None}, HasUser:{has_username}")
                
                # Mask if it's a complete valid UPI ID
                if is_complete_upi and has_username:
                    x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                    
                    # Check if already masked
                    already_masked = False
                    for mx, my, mw, mh in masked_regions:
                        if abs(x - mx) < 10 and abs(y - my) < 10:
                            already_masked = True
                            break
                    
                    if not already_masked:
                        total_masked += 1
                        pad = 3
                        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 165, 255), (203, 192, 255), (255, 144, 30), (147, 20, 255)]
                        color = random.choice(colors)
                        cv2.rectangle(img, (max(x - pad, 0), max(y - pad, 0)), (min(x + w + pad, img.shape[1]), min(y + h + pad, img.shape[0])), color, -1)
                        masked_regions.append((x, y, w, h))
                        print(f"[MASK] '{text}' with color")
            
            # Strategy 2: Try combining adjacent texts for split UPI IDs
            for i in range(len(data["text"]) - 1):
                text1 = data["text"][i].strip()
                text2 = data["text"][i+1].strip()
                if not text1 or not text2:
                    continue
                
                # Try combining if first is number-like and second starts with @
                combined = (text1 + text2).replace(" ", "").replace("\n", "")
                if '@' in combined:
                    is_upi = UPI_REGEX.search(combined)
                    parts = combined.split('@')
                    if is_upi and len(parts) == 2 and len(parts[0]) >= 3 and parts[1]:
                        x1, y1, w1, h1 = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                        x2, y2, w2, h2 = data["left"][i+1], data["top"][i+1], data["width"][i+1], data["height"][i+1]
                        
                        # Check if texts are close (same line)
                        if abs(y1 - y2) < 20:
                            # Check if not already masked
                            already_masked = False
                            for mx, my, mw, mh in masked_regions:
                                if (abs(x1 - mx) < 10 and abs(y1 - my) < 10) or (abs(x2 - mx) < 10 and abs(y2 - my) < 10):
                                    already_masked = True
                                    break
                            
                            if not already_masked:
                                total_masked += 1
                                x = min(x1, x2)
                                y = min(y1, y2)
                                w = max(x1 + w1, x2 + w2) - x
                                h = max(y1 + h1, y2 + h2) - y
                                pad = 3
                                colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 165, 255), (203, 192, 255), (255, 144, 30), (147, 20, 255)]
                                color = random.choice(colors)
                                cv2.rectangle(img, (max(x - pad, 0), max(y - pad, 0)), (min(x + w + pad, img.shape[1]), min(y + h + pad, img.shape[0])), color, -1)
                                masked_regions.append((x, y, w, h))
                                print(f"[MASK-COMBINED] '{combined}' with color")
            
            output_file = f"output_{user_id}_{idx}.jpg"
            cv2.imwrite(output_file, img)
            processed_files.append(output_file)
            
            try:
                os.remove(input_file)
            except:
                pass
                
        except Exception as e:
            print(f"[ERROR] Photo {idx}: {e}")
    
    await progress_msg.edit_text(f" Processing complete!\n{create_progress_bar(total_photos, total_photos)}\n\n Total UPI IDs masked: {total_masked}\n Sending {len(processed_files)} photos...")
    
    if processed_files:
        try:
            batch_size = 10
            for i in range(0, len(processed_files), batch_size):
                batch = processed_files[i:i+batch_size]
                media_group = []
                
                for idx, file_path in enumerate(batch):
                    with open(file_path, 'rb') as f:
                        if i == 0 and idx == 0:
                            media_group.append(InputMediaPhoto(f.read(), caption=f" Processed {len(processed_files)} photos - Masked {total_masked} UPI IDs "))
                        else:
                            media_group.append(InputMediaPhoto(f.read()))
                
                await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
            
            for file_path in processed_files:
                try:
                    os.remove(file_path)
                except:
                    pass
            
            await context.bot.send_message(chat_id=query.message.chat_id, text=f" All done! Masked {total_masked} UPI IDs with colorful blocks!")
            
        except Exception as e:
            print(f"[ERROR] Sending media: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text=f" Error sending photos: {str(e)}")
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text=" No photos were processed successfully")
    
    user_photos[user_id] = []

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).connect_timeout(30.0).read_timeout(30.0).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, collect_photo))
    app.add_handler(CallbackQueryHandler(process_all, pattern="process_all"))
    print("[OK]  UPI Remover Bot with Progress Bar Active...")
    app.run_polling()

if __name__ == "__main__":
    main()
