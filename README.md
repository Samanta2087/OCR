# UPI ID Remover Bot 🤖

Telegram bot that automatically detects and masks UPI IDs from payment screenshots using OCR technology.

## Features ✨

- 📸 **Photo Collection System** - Send multiple photos, process all at once
- 🔍 **Universal UPI Detection** - Detects any UPI ID format (any bank/provider)
- 🎨 **Colorful Masking** - Masks UPI IDs with random colored rectangles
- 📊 **Progress Tracking** - Real-time animated progress bar during processing
- 🚀 **Batch Processing** - Sends all processed photos back as media albums
- ✅ **Photo Confirmations** - Shows confirmation for each received photo
- 🔧 **OCR Error Handling** - Handles character confusions (l/I/1, pipe symbols, etc.)

## Installation 🛠️

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR**
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - CentOS/RHEL: `sudo yum install tesseract`
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Samanta2087/OCR.git
cd OCR
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Update Tesseract path in `ocr.py` (line 11):
```python
# For Linux/VPS:
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# For Windows:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

4. Add your Telegram bot token in `ocr.py` (line 12):
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

5. Run the bot:
```bash
python ocr.py
```

## Usage 📱

1. Start the bot with `/start`
2. Send payment screenshot images (one or multiple)
3. Each photo will be confirmed
4. Click **"Process All Photos"** button
5. Watch the progress bar in real-time
6. Receive all processed photos with UPI IDs masked

## Technical Details 🔧

- **OCR Engine**: Tesseract 5.3+
- **Image Processing**: OpenCV (cv2)
- **Telegram Framework**: python-telegram-bot 22.5
- **Detection Method**: Universal regex pattern matching
- **Masking**: Colored rectangles with 3px padding
- **Supported Formats**: Any UPI ID format (word@word pattern)

## Supported UPI Handles 🏦

The bot uses **universal detection** and supports ALL UPI handles including:
- @ybl, @ibl, @axl (PhonePe, ICICI, Axis)
- @oksbi, @okaxis, @okhdfc
- @paytm, @pthdfc, @ptsbi
- @naviaxis, @apl, @fam
- And **any other** UPI handle format

## Success Rate 📈

- **94-100%** detection rate on clear images
- Handles OCR character confusions (l/I/1, pipe symbols)
- Supports split text detection (when OCR separates number and handle)

## License 📄

MIT License - Feel free to use and modify!

## Author 👨‍💻

Created by Samanta2087

## Support 💬

For issues or questions, open an issue on GitHub.
