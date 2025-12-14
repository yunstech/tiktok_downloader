# 🍪 How to Get Your TikTok Cookie (Step-by-Step with Visual Guide)

## ⚠️ Why You NEED a Cookie

TikTok uses aggressive bot detection. **Without a valid logged-in session cookie, you will get 0 videos** even though profiles load fine.

**Your logs show:**
```
✅ Profile: Casey Kaspol - 7,400,000 followers, 2221 videos  
❌ Videos found: 0
```

This means TikTok is blocking video access because there's **no valid authentication cookie**.

---

## 🎯 Quick Start (Chrome - Recommended)

### Step 1: Open TikTok and Log In

1. Open Chrome browser
2. Go to **https://www.tiktok.com**
3. **Click "Log in"** (top right)
4. Log in with your account (any account works - doesn't need to be the one you're scraping)

**⚠️ CRITICAL:** You MUST be logged in! Videos won't work with cookies from logged-out sessions.

---

### Step 2: Open Developer Tools

Press **F12** on your keyboard

OR

Right-click anywhere > **Inspect**

OR

Click the **⋮** menu (top right) > More tools > **Developer tools**

---

### Step 3: Navigate to Cookies

1. In DevTools, click the **"Application"** tab (at the top)
   - If you don't see it, click the **>>** arrows to find it

2. In the left sidebar, expand **"Cookies"**

3. Click on **"https://www.tiktok.com"**

You should see a list of cookies like:
```
Name                    Value
----------------------------------------------
sessionid              7a8b9c0d1e2f3g4h5i6j7k...
sessionid_ss           similar_value...
msToken                another_value...
tt_chain_token         yet_another...
```

---

### Step 4: Copy the Cookie

1. **Find the cookie named:** `sessionid` (preferred) or `sessionid_ss`

2. **Double-click on the "Value" column** for that cookie

3. The entire value will be selected (looks like a long random string)

4. **Press Ctrl+C** (Windows/Linux) or **Cmd+C** (Mac) to copy

**Example cookie value:**
```
7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9
```

**⚠️ Copy the ENTIRE value** - it should be 60-80 characters long!

---

### Step 5: Add to Your .env File

1. Open your `.env` file in the project root

2. Find the line: `TIKTOK_COOKIE=`

3. Paste your cookie value after the `=`:
   ```bash
   TIKTOK_COOKIE=7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9
   ```

4. **Save the file**

5. **Restart your containers:**
   ```bash
   docker compose down
   docker compose up -d
   ```

---

## 🔍 Verifying Your Cookie

After adding the cookie, test it:

```bash
# Run diagnostic tool
docker compose exec worker python diagnose_tiktok.py itsceceh

# Or test with your cookie directly
docker compose exec worker python diagnose_tiktok.py itsceceh your_cookie_here
```

### Good Output:
```
✅ Found 30 videos at: webapp.user-detail.itemList
✅ API RETURNED VIDEOS!
```

### Bad Output:
```
❌ NO VIDEOS FOUND IN HTML
❌ API RETURNED 0 VIDEOS
```

If you see bad output, your cookie is **expired or invalid**. Get a fresh one!

---

## 🦊 Firefox Users

### Steps:

1. Open **https://www.tiktok.com** and **log in**

2. Press **F12** to open Developer Tools

3. Click the **"Storage"** tab (not "Application" like Chrome)

4. In left sidebar: **Cookies** > **https://www.tiktok.com**

5. Find `sessionid` and copy its value

6. Add to `.env` file

---

## 🔐 Safari Users

### Steps:

1. Enable Developer Menu:
   - Safari > Preferences > Advanced
   - Check ✅ **"Show Develop menu in menu bar"**

2. Open **https://www.tiktok.com** and **log in**

3. Click **Develop** menu > **Show Web Inspector**

4. Click **Storage** tab

5. Find **Cookies** > **tiktok.com**

6. Copy `sessionid` value

7. Add to `.env` file

---

## 🛠️ Alternative: Using Cookie Export Extension

If you find the manual method difficult:

### Chrome/Edge:

1. Install **"Cookie-Editor"** extension from Chrome Web Store
   - https://chrome.google.com/webstore

2. Go to **https://www.tiktok.com** and **log in**

3. Click the Cookie-Editor icon (top right)

4. Find `sessionid` and click the **copy icon**

5. Paste into `.env` file

### Firefox:

1. Install **"Cookie Quick Manager"** from Firefox Add-ons

2. Same steps as Chrome

---

## ⏰ Cookie Expiry

### How long do cookies last?

- **~30 days** of inactivity
- Expires when you **log out** from TikTok
- Expires if TikTok detects suspicious activity

### Signs your cookie expired:

```
❌ API RETURNED 0 VIDEOS
❌ Bot detection error
```

### Solution:

1. Go to TikTok.com and log in again
2. Get a fresh cookie
3. Update `.env` file
4. Restart containers

---

## 🚨 Common Mistakes

### ❌ Mistake 1: Not Logged In

**DON'T:**
- Open TikTok
- Get cookie immediately
- Close browser

**DO:**
- Open TikTok
- **Click "Log in"**
- Enter credentials
- **THEN** get cookie

### ❌ Mistake 2: Wrong Cookie

**DON'T** copy:
- `msToken` (too short, not a session cookie)
- `ttwid` (device ID, not session)
- `tt_csrf_token` (security token)

**DO** copy:
- `sessionid` ✅ (best)
- `sessionid_ss` ✅ (also works)

### ❌ Mistake 3: Incomplete Cookie

Cookie should look like:
```
✅ GOOD (60-80 chars):
7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9

❌ BAD (too short):
7a8b9c0d

❌ BAD (wrong format):
sessionid=7a8b9c0d...
```

Don't include the cookie name, just the value!

### ❌ Mistake 4: Spaces or Quotes

**DON'T:**
```bash
TIKTOK_COOKIE="your_cookie_here"   # ❌ No quotes!
TIKTOK_COOKIE= your_cookie          # ❌ No space after =!
```

**DO:**
```bash
TIKTOK_COOKIE=your_cookie_here     # ✅ Clean value
```

---

## 🧪 Testing Your Setup

### Test 1: Diagnostic Tool

```bash
docker compose exec worker python diagnose_tiktok.py tiktok
```

Should show:
```
✅ Found XX videos at: webapp.user-detail.itemList
✅ API RETURNED VIDEOS!
```

### Test 2: Quick Scrape Test

```bash
docker compose exec worker python test_scraper.py --username tiktok --max-videos 5
```

Should show:
```
✅ Profile retrieved!
✅ Scraped 5 videos!
```

### Test 3: Full Bot Test

Send a message to your Telegram bot:
```
tiktok
```

Should receive 5 videos within a minute!

---

## ❓ Still Not Working?

### Check These:

1. **Is the cookie recent?**
   - Get a fresh cookie (within last hour)

2. **Are you logged in?**
   - Open TikTok.com in your browser
   - Should see your profile in top right
   - If you see "Log in" button, you're NOT logged in!

3. **Is the value complete?**
   - Should be 60-80 characters
   - No spaces, quotes, or special formatting

4. **Did you restart containers?**
   ```bash
   docker compose down
   docker compose up -d
   ```

5. **Check the logs:**
   ```bash
   docker compose logs -f worker | grep cookie
   ```
   
   Should see:
   ```
   ✅ Using TikTok session cookie
   ```

6. **Try a different account**
   - Some accounts might be region-locked
   - Try with a US-based TikTok account

---

## 🎯 Expected Behavior

### With Valid Cookie:

```
✅ Profile: Casey Kaspol - 7.4M followers
✅ Found 30 videos
✅ Scraped 30 videos successfully
```

### Without Valid Cookie (Your Current Issue):

```
✅ Profile: Casey Kaspol - 7.4M followers  
❌ Found 0 videos                          ← THE PROBLEM!
❌ API returned 0 videos
```

---

## 📚 Related Files

- `diagnose_tiktok.py` - Test cookie validity
- `test_scraper.py` - Test full scraper
- `TIKTOK_SETUP.md` - Complete setup guide
- `.env.example` - Configuration template

---

## 💡 Pro Tips

1. **Keep cookies fresh**: Update monthly
2. **Use a dedicated account**: Create a TikTok account just for scraping
3. **Don't log out**: Keep the account logged in
4. **Use residential proxy**: Combine with cookie for best results
5. **Set headless=false**: If still having issues

---

## 🆘 Need Help?

Run the diagnostic tool and share the output:

```bash
docker compose exec worker python diagnose_tiktok.py itsceceh
```

This will show exactly what's wrong and suggest fixes!
