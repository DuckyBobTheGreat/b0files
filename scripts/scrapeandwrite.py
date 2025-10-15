"""
civitai_scrape.py
Scrape CivitAI model pages for metadata and save to JSON + download thumbnails.

INPUT: a JSON file LINKS = { "filename": "https://civitai.com/models/..." }
OUTPUT:
- civitai_models.json (schema per request)
- thumbnails/<ID>.jpg (downloaded image)
"""

import os
import re
import json
import time
import random
import hashlib
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# -----------------------------
# USER CONFIG
# -----------------------------

OUTPUT_JSON = r"E:\GitHubRepos\golden-key\scraped_data\models.json"
LINKS = r"E:\GitHubRepos\golden-key\link.json"   # JSON input
THUMB_DIR   = r"E:\GitHubRepos\golden-key\scraped_data\thumbnails"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
TIMEOUT_S   = 15         # default per-request timeout (seconds)
RETRIES     = 3          # how many times to retry a failed GET
SLEEP_RANGE = (0.8, 1.8) # polite randomized backoff between retries

HTML_TIMEOUT = 15
THUMB_TIMEOUT = 8
MAX_MODEL_DURATION = 60  # hard cap per model in seconds

# -----------------------------
# DEV TESTING CONTROL
# -----------------------------
TEST_LIMIT = 0   # set to None or 0 to disable limit


# -----------------------------
# HELPERS
# -----------------------------

def rand_sleep():
    time.sleep(random.uniform(*SLEEP_RANGE))

def get(url, timeout=None):
    """GET with separate timeouts and retry/backoff protection."""
    timeout = timeout or TIMEOUT_S
    last_exc = None
    for _ in range(RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                print("  🚦 Rate limited (429). Pausing 30s...")
                time.sleep(30)
            else:
                print(f"  ⚠️ HTTP {resp.status_code} for {url}")
            rand_sleep()
        except requests.Timeout:
            print(f"  ⚠️ Timeout after {timeout}s on {url}")
            rand_sleep()
        except Exception as e:
            last_exc = e
            print(f"  ⚠️ Network error: {e}")
            rand_sleep()
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Failed to GET {url}")


def text_or_none(el):
    return el.get_text(" ", strip=True) if el else ""

def html_or_none(el):
    return str(el) if el else ""

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]+', "_", name)

# -----------------------------
# ID generation (sequential)
# -----------------------------
_id_counter = 0

def gen_id_from(filename, url):
    """Sequential model ID generator: A0001, A0002, ..."""
    global _id_counter
    _id_counter += 1
    return f"A{_id_counter:04d}"


def join_abs(base, maybe_rel):
    if not maybe_rel:
        return ""
    if bool(urlparse(maybe_rel).scheme):
        return maybe_rel
    return urljoin(base, maybe_rel)

def download_thumbnail(thumbnail_url, out_id, timeout=THUMB_TIMEOUT):
    """
    Download image or video thumbnail to THUMB_DIR/<ID>.<ext>.
    Detects MIME type and saves accordingly.
    Returns (remote_url, local_path_or_empty).
    """
    if not thumbnail_url:
        return "", ""
    ensure_dir(THUMB_DIR)

    # Guess file extension from URL or Content-Type
    ext = os.path.splitext(urlparse(thumbnail_url).path)[1].lower()
    local_path = ""
    try:
        r = requests.get(thumbnail_url, headers=HEADERS, timeout=timeout, stream=True)
        if r.status_code != 200:
            print(f"  ⚠️ Thumbnail HTTP {r.status_code} — {thumbnail_url}")
            return thumbnail_url, ""

        # Detect MIME type from headers
        content_type = r.headers.get("Content-Type", "").lower()
        if "image" in content_type:
            if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                ext = ".jpg"
        elif "video" in content_type:
            if not ext or ext not in [".mp4", ".webm"]:
                ext = ".mp4"
        elif not ext:
            # Default fallback
            ext = ".dat"

        local_path = os.path.join(THUMB_DIR, f"{out_id}{ext}")

        # Write stream to disk
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

        print(f"  🖼 Saved thumbnail → {os.path.basename(local_path)}")
        return thumbnail_url, local_path

    except Exception as e:
        print(f"  ⚠️ Thumbnail download failed: {e}")
        return thumbnail_url, ""



# -----------------------------
# LINK LOADER
# -----------------------------

def load_links(file_path):
    """
    Load a JSON file containing "model": "link" pairs.
    Handles multiple comma-separated links, arrays, empty fields, and comments.
    Returns a list of (filename, url) tuples.
    """
    pairs = []

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Link file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON format in {file_path}: {e}")

    for model_name, value in data.items():
        model_name = (model_name or "").strip()
        if not value:
            continue

        if isinstance(value, str):
            urls = [v.strip() for v in value.split(",") if v.strip()]
        elif isinstance(value, list):
            urls = [str(v).strip() for v in value if str(v).strip()]
        else:
            urls = []

        if not urls or all(u.startswith("#") or "http" not in u for u in urls):
            continue

        if not model_name:
            for url in urls:
                parsed = urlparse(url)
                filename = parsed.path.strip("/").split("/")[-1] or "unnamed"
                pairs.append((filename, url))
            continue

        for url in urls:
            pairs.append((model_name, url))

    return pairs

# -----------------------------
# SCRAPING LOGIC
# -----------------------------
def find_table_type(soup, label="Type"):
    """
    Find the <tr> whose first <td><p> exactly matches 'Type'
    and return the text from the next <td>'s <p>.
    """
    for tr in soup.find_all("tr"):
        # find all <td> in this row
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        # first cell's <p> must exist and match exactly
        left_p = tds[0].find("p")
        if left_p and left_p.get_text(strip=True) == label:
            right_p = tds[1].find("p")
            if right_p:
                return right_p.get_text(strip=True)
            # if no <p>, fallback to any text in the right cell
            return tds[1].get_text(strip=True)

    return ""

def find_table_base_model(soup, label="Base Model"):
    """
    Find the <tr> whose first <td><p> text contains 'Base Model'
    and return the visible text from the next <td>'s <p>.
    """
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        # Left cell <p> text
        left_p = tds[0].find("p")
        if not left_p:
            continue

        left_text = left_p.get_text(" ", strip=True)
        # Match even if there are invisible comments or spaces
        if re.search(r"\bBase\s*Model\b", left_text, re.I):
            right_td = tds[1]

            # The main visible name is inside the <p> tag in the right cell
            right_p = right_td.find("p")
            if right_p:
                val = right_p.get_text(" ", strip=True)
                return val.strip()

            # Fallback: any plain text in the right cell
            val = text_or_none(right_td).strip()
            if val:
                return val

    return ""



def find_table_file_size(soup, label="File Size"):
    """
    Find the <tr> whose first <td><p> exactly matches 'File Size'
    and return the text from the next <td>'s <p>.
    """
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        left_p = tds[0].find("p")
        if left_p and left_p.get_text(strip=True) == label:
            right_p = tds[1].find("p")
            if right_p:
                return right_p.get_text(strip=True)
            return tds[1].get_text(strip=True)
    return ""

def find_table_trigger_words(soup, label="Trigger Words"):
    """
    Find the <tr> whose first <td><p> exactly matches 'Trigger Words'
    and collect all badge or code texts from the next <td>.
    Returns a comma-separated string of unique trigger words.
    """
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        left_p = tds[0].find("p")
        if left_p and left_p.get_text(strip=True) == label:
            right_td = tds[1]
            words = []

            # collect from Mantine badges
            for badge in right_td.find_all("div", class_=re.compile(r"Badge-root")):
                txt = text_or_none(badge)
                txt = re.sub(r"\s+", " ", txt).strip()
                if txt and len(txt) < 40:
                    words.append(txt)

            # collect from <code> or <kbd> tags (fallback)
            for code in right_td.find_all(["code", "kbd"]):
                txt = code.get_text(strip=True)
                if txt and len(txt) < 40:
                    words.append(txt)

            # deduplicate while preserving order
            seen = set()
            uniq = []
            for w in words:
                if w not in seen:
                    uniq.append(w)
                    seen.add(w)

            return ", ".join(uniq)
    return ""


def find_table_trigger_words_by_position(soup):
    """
    Locate trigger words row positioned between 'Base Model' and 'Hash' rows.
    Extract all badge labels or short text tokens.
    """
    all_rows = soup.find_all("tr")
    for i, tr in enumerate(all_rows):
        # detect the "Base Model" row
        first_td = tr.find("td")
        if first_td and "Base Model" in first_td.get_text(strip=True):
            # look ahead to next row
            if i + 1 < len(all_rows):
                next_tr = all_rows[i + 1]
                next_tds = next_tr.find_all("td")
                if len(next_tds) >= 2:
                    right_td = next_tds[1]
                    # ensure first td is empty or very short (no <p> text)
                    left_txt = text_or_none(next_tds[0]).strip()
                    if not left_txt:
                        # now collect trigger words
                        words = []
                        for badge in right_td.find_all("div", class_=re.compile(r"Badge-root")):
                            txt = text_or_none(badge)
                            txt = re.sub(r"\s+", " ", txt).strip()
                            if txt and len(txt) < 40:
                                words.append(txt)
                        # fallback: <code> tags inside
                        for code in right_td.find_all(["code", "kbd"]):
                            txt = code.get_text(strip=True)
                            if txt and len(txt) < 40:
                                words.append(txt)
                        # deduplicate
                        seen = set()
                        uniq = []
                        for w in words:
                            if w not in seen:
                                uniq.append(w)
                                seen.add(w)
                        return ", ".join(uniq)
    return ""


def parse_civitai_page(base_url, html):
    """Modern CivitAI parser (NextJS-compatible)."""
    soup = BeautifulSoup(html, "html.parser")

#####################################################################################################################
    # --- TITLE ---
#####################################################################################################################

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = text_or_none(h1)
    if not title:
        meta_title = soup.find("meta", {"property": "og:title"})
        if meta_title and meta_title.get("content"):
            title = meta_title["content"].strip()

#####################################################################################################################
    # --- JSON BLOCKS ---
#####################################################################################################################

    ld_json, next_json = {}, {}
    ld_script = soup.find("script", {"type": "application/ld+json"})
    if ld_script:
        try: ld_json = json.loads(ld_script.text)
        except Exception: pass

    next_script = soup.find("script", {"id": "__NEXT_DATA__"})
    if next_script:
        try: next_json = json.loads(next_script.text)
        except Exception: pass

#####################################################################################################################
    # --- TYPE ---
#####################################################################################################################

    model_type = ""

    # 1️⃣ JSON fallback (some models still provide it)
    try:
        model_type = next_json["props"]["pageProps"]["modelVersion"]["baseModelType"]
    except Exception:
        pass

    # 2️⃣ Strict HTML match for table row labeled "Type"
    if not model_type:
        model_type = find_table_type(soup, "Type")

    # 3️⃣ Normalize
    if model_type:
        model_type = model_type.strip()
        if model_type.lower() in ["lora", "loras"]:
            model_type = "lora"
        elif model_type.lower() in ["checkpoint", "checkpoints"]:
            model_type = "checkpoint"

#####################################################################################################################
    # --- BASE MODEL ---
#####################################################################################################################


    base_model = ""

    # 1️⃣ JSON (if present)
    try:
        base_model = next_json["props"]["pageProps"]["modelVersion"]["baseModel"]
    except Exception:
        pass

    # 2️⃣ Strict HTML <tr> fallback
    if not base_model:
        base_model = find_table_base_model(soup, "Base Model")

    # 3️⃣ Clean and normalize spacing
    if base_model:
        base_model = re.sub(r"\s+", " ", base_model.strip())


#####################################################################################################################
    # --- DATE ---
#####################################################################################################################

    published_on = ""
    if "datePublished" in ld_json:
        published_on = ld_json["datePublished"].split("T")[0]
    else:
        abbr = soup.find("abbr", {"title": re.compile(r"\d{4}-\d{2}-\d{2}")})
        if abbr:
            published_on = abbr["title"].split("T")[0]

#####################################################################################################################
 # --- VERSION ---
#####################################################################################################################

    version = ""

    # 1️⃣ Try JSON first
    try:
        version = next_json["props"]["pageProps"]["modelVersion"]["name"]
    except Exception:
        pass

    # 2️⃣ HTML fallback: find the *active* version button (blue or with mantine-active class)
    if not version:
        active_btn = soup.find(
            "button",
            class_=re.compile(r"mantine-(active|Button-root)"),
            attrs={"data-variant": "filled"}
        )
        if active_btn:
            # Extract visible text, which might be inside nested spans/divs
            txt = text_or_none(active_btn)
            # Clean up icons, whitespace, etc.
            txt = re.sub(r"\s+", " ", txt).strip()
            # Sometimes the version name is the last part after an icon label
            if txt:
                version = txt.split()[-1] if len(txt.split()) <= 3 else txt

    # 3️⃣ Final fallback: simple pattern from title
    if not version:
        match = re.search(r"\bv[\d\.]+|v\d+", title or "", re.I)
        if match:
            version = match.group(0)

    # Normalize
    if version:
        version = version.strip()

#####################################################################################################################
    # --- DESCRIPTION (main model description) ---
#####################################################################################################################

    description_html = ""

    # 1️⃣ Prefer JSON if it contains proper HTML or plain text
    desc_candidates = []
    try:
        mv = next_json.get("props", {}).get("pageProps", {}).get("modelVersion", {})
        model = next_json.get("props", {}).get("pageProps", {}).get("model", {})
        for source in (mv, model, ld_json):
            if isinstance(source, dict):
                for key in ("descriptionHtml", "description", "details"):
                    val = source.get(key)
                    if isinstance(val, str) and len(val.strip()) > 50:
                        desc_candidates.append(val.strip())
    except Exception:
        pass

    if desc_candidates:
        # Prefer HTML-looking candidates
        html_like = [d for d in desc_candidates if "<" in d and ">" in d]
        description_html = html_like[0] if html_like else desc_candidates[0]

    # 2️⃣ HTML fallback: Mantine Spoiler content (RenderHtml_htmlRenderer)
    if not description_html:
        spoiler = soup.find("div", class_=re.compile(r"mantine-Spoiler-content"))
        if spoiler:
            # Capture full HTML inside the spoiler block
            inner = spoiler.find("div", class_=re.compile(r"RenderHtml_htmlRenderer"))
            if inner:
                description_html = str(inner)
            else:
                description_html = str(spoiler)

    # 3️⃣ Final fallback: legacy <div data-testid="model-description">
    if not description_html:
        desc_div = soup.find("div", {"data-testid": "model-description"})
        if desc_div:
            description_html = str(desc_div)

    # 4️⃣ Clean minor artifacts
    if description_html:
        description_html = description_html.strip()

#####################################################################################################################
    # --- ABOUT VERSION ---
#####################################################################################################################

    about_version_html = ""

    # 1️⃣ Try JSON first (some pages expose it under modelVersion.description or notes)
    try:
        mv = next_json["props"]["pageProps"]["modelVersion"]
        for key in ("description", "descriptionHtml", "notes", "changelog"):
            val = mv.get(key)
            if isinstance(val, str) and val.strip():
                about_version_html = val.strip()
                break
    except Exception:
        pass

    # 2️⃣ HTML fallback: Mantine accordion "About this version"
    if not about_version_html:
        # find the button/label that says "About this version"
        about_label = soup.find(string=re.compile(r"About\s+this\s+version", re.I))
        if about_label:
            button = about_label.find_parent("button")
            if button:
                # the accordion panel is usually the next sibling div
                panel = button.find_next_sibling("div", class_=re.compile("Accordion-panel"))
                if panel:
                    # find the spoiler content inside it if exists
                    spoiler = panel.find("div", class_=re.compile("Spoiler-content"))
                    if spoiler:
                        about_version_html = str(spoiler)
                    else:
                        about_version_html = str(panel)

    # 3️⃣ Fallback: older Mantine class variant
    if not about_version_html:
        panel = soup.find("div", class_=re.compile("Accordion-panel"))
        if panel:
            about_version_html = str(panel)

    # Final cleanup
    if about_version_html:
        # strip excessive whitespace and redundant newlines
        about_version_html = re.sub(r"\n\s+", "\n", about_version_html.strip())

#####################################################################################################################
    # --- TRIGGER WORDS ---
#####################################################################################################################

    trigger_words = ""

    # 1️⃣ JSON trainedWords
    try:
        trained = next_json["props"]["pageProps"]["modelVersion"]["trainedWords"]
        if isinstance(trained, list) and trained:
            trigger_words = ", ".join([str(w).strip() for w in trained if str(w).strip()])
    except Exception:
        pass

    # 2️⃣ Fallback: try explicit labeled row
    if not trigger_words:
        trigger_words = find_table_trigger_words(soup, "Trigger Words")

    # 3️⃣ Fallback: try positional row between Base Model and Hash
    if not trigger_words:
        trigger_words = find_table_trigger_words_by_position(soup)

    # 4️⃣ Cleanup
    if trigger_words:
        trigger_words = re.sub(r"\s*,\s*", ", ", trigger_words.strip())


#####################################################################################################################
    # --- SIZE ---
#####################################################################################################################

    size = ""

    # 1️⃣ Try JSON (files[0].sizeKB)
    try:
        size_kb = next_json["props"]["pageProps"]["modelVersion"]["files"][0]["sizeKB"]
        if size_kb:
            if size_kb >= 1024 * 1024:
                size = f"{round(size_kb / 1024 / 1024, 2)} GB"
            elif size_kb >= 1024:
                size = f"{round(size_kb / 1024, 2)} MB"
            else:
                size = f"{int(size_kb)} KB"
    except Exception:
        pass

    # 2️⃣ Strict HTML <tr> fallback
    if not size:
        size = find_table_file_size(soup, "File Size")

    # 3️⃣ Final cleanup
    if size:
        size = size.replace("  ", " ").strip()


#####################################################################################################################
    # --- THUMBNAIL ---
#####################################################################################################################

    thumbnail_url = ""
    video_url = ""

    # 1️⃣ Try <meta property="og:image"> first (often same as poster)
    ogimg = soup.find("meta", {"property": "og:image"})
    if ogimg and ogimg.get("content"):
        thumbnail_url = join_abs(base_url, ogimg["content"].strip())

    # 2️⃣ Prefer the first EdgeMedia container (covers both img and video)
    if not thumbnail_url or not thumbnail_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        media_container = soup.find("div", class_=re.compile(r"EdgeMedia_container|mantine-AspectRatio-root"))
        if media_container:
            # Try <img> first
            img = media_container.find("img", class_=re.compile(r"EdgeImage_image"))
            if img and img.get("src"):
                thumbnail_url = join_abs(base_url, img["src"].strip())

            # Try <video> if no <img> or also collect video source
            if not thumbnail_url:
                video = media_container.find("video", class_=re.compile(r"EdgeMedia_responsive"))
                if video:
                    # Prefer poster image as thumbnail
                    if video.get("poster"):
                        thumbnail_url = join_abs(base_url, video["poster"].strip())
                    # Optionally store video URL
                    srcs = [s.get("src") for s in video.find_all("source") if s.get("src")]
                    if srcs:
                        # Choose mp4 over webm when available
                        mp4s = [s for s in srcs if s.lower().endswith(".mp4")]
                        video_url = join_abs(base_url, mp4s[0] if mp4s else srcs[0])

    # 3️⃣ Fallback: ld_json["image"]
    if not thumbnail_url and isinstance(ld_json.get("image"), str):
        thumbnail_url = join_abs(base_url, ld_json["image"])
    elif not thumbnail_url and isinstance(ld_json.get("image"), list) and ld_json["image"]:
        thumbnail_url = join_abs(base_url, ld_json["image"][0])

    # 4️⃣ Clean up entities
    if thumbnail_url:
        thumbnail_url = thumbnail_url.replace("&amp;", "&").strip()
    if video_url:
        video_url = video_url.replace("&amp;", "&").strip()

#####################################################################################################################
   # --- DOWNLOAD LINK ---
#####################################################################################################################

    # Always use the original model page URL (from our input JSON)
    download_link = base_url.strip()

    return {
        "title": title or "",
        "type": model_type or "",
        "base_model": base_model or "",
        "published_on": published_on or "",
        "version": version or "",
        "about_version_html": about_version_html or "",
        "description_html": description_html or "",
        "trigger_words": trigger_words or "",
        "size": size or "",
        "thumbnail_url": thumbnail_url or "",
        "video_url": video_url or "",
        "download_link": download_link or ""
    }

print("⚙️ Script loaded successfully.")
print(f"LINKS file exists? {os.path.exists(LINKS)}")
print("About to call main()...")

def fetch_from_api(filename, url):
    """
    Fetch model/version info from CivitAI API.
    Handles both links with and without ?modelVersionId=...
    """
    # Extract numeric IDs
    match_model = re.search(r"/models/(\d+)", url)
    match_ver = re.search(r"modelVersionId=(\d+)", url)
    model_id = match_model.group(1) if match_model else None
    version_id = match_ver.group(1) if match_ver else None

    if not model_id:
        raise ValueError(f"No model ID found in URL: {url}")

    # 1️⃣ If version ID missing, fetch model JSON to find latest version
    if not version_id:
        model_api = f"https://civitai.com/api/v1/models/{model_id}"
        for _ in range(3):
            try:
                r = requests.get(model_api, headers=HEADERS, timeout=HTML_TIMEOUT)
                if r.status_code == 200:
                    model_json = r.json()
                    # grab latest version ID
                    versions = model_json.get("modelVersions", [])
                    if versions:
                        version_id = str(versions[0]["id"])
                        break
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Model API error: {e}")
                time.sleep(1)
        if not version_id:
            raise RuntimeError(f"Could not determine version ID for model {model_id}")

    # 2️⃣ Fetch version JSON (main data source)
    version_api = f"https://civitai.com/api/v1/model-versions/{version_id}"
    v = {}
    for _ in range(3):
        try:
            r = requests.get(version_api, headers=HEADERS, timeout=HTML_TIMEOUT)
            if r.status_code == 200:
                v = r.json()
                break
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ Version API error: {e}")
            time.sleep(1)
    if not v:
        raise RuntimeError(f"Failed to fetch version {version_id}")

    # --- extract fields ---
    model_info = v.get("model", {})
    file_info = (v.get("files") or [{}])[0]
    img_info = (v.get("images") or [{}])[0]

    title = f"{model_info.get('name','')} - {v.get('name','')}".strip(" -")
    model_type = model_info.get("type", "")
    base_model = v.get("baseModel", "")
    base_model_type = v.get("baseModelType", "")
    trained_words = ", ".join(v.get("trainedWords", []))
    size_kb = file_info.get("sizeKB", 0)
    size = (
        f"{round(size_kb/1024/1024,2)} GB" if size_kb >= 1024*1024
        else f"{round(size_kb/1024,2)} MB" if size_kb >= 1024
        else f"{int(size_kb)} KB" if size_kb else ""
    )
    # --- CORE MODEL DATA EXTRACTION ---
    hashes = file_info.get("hashes", {})
    download_link = file_info.get("downloadUrl") or url
    description_html = v.get("description", "")
    created_at = v.get("createdAt", "").split("T")[0]

    # derive a clean model page link (for viewer)
    model_id = model_info.get("id") or re.search(r"/models/(\d+)", url).group(1)
    model_link = f"https://civitai.com/models/{model_id}"

    # sequential ID for this model
    out_id = gen_id_from(filename, url)

    # --- DOWNLOAD UP TO 5 THUMBNAILS ---
    images = v.get("images") or []
    thumbs_remote, thumbs_local = [], []

    for j, img in enumerate(images[:5], 1):
        thumb_url = img.get("url")
        if not thumb_url:
            continue
        thumb_id = f"{out_id}_T{j}"
        try:
            remote, local = download_thumbnail(thumb_url, thumb_id, timeout=THUMB_TIMEOUT)
            if remote:
                thumbs_remote.append(remote)
            if local:
                thumbs_local.append(local)
        except Exception as e:
            print(f"  ⚠️ Thumbnail {j} failed: {e}")

    # choose first one as primary
    thumbnail = thumbs_remote[0] if thumbs_remote else ""
    thumbnail_local = thumbs_local[0] if thumbs_local else ""



    return {
        "filename": filename,
        "title": title,
        "type": model_type.lower(),
        "base_model": base_model,
        "base_model_type": base_model_type,
        "size": size,
        "thumbnail": thumbnail,
        "thumbnail_local": thumbnail_local,
        "thumbnails_all": thumbs_remote,
        "thumbnails_local": thumbs_local,
        "model_link": model_link,
        "metadata": {
            "trained_words": trained_words,
            "hashes": hashes,
            "description": description_html,
            "download_link": download_link,
            "published_on": created_at,
        },
    }

# -----------------------------
# MAIN
# -----------------------------
def main():
    ensure_dir(THUMB_DIR)

    try:
        links_list = load_links(LINKS)
    except Exception as e:
        print(f"\033[91m❌ Error loading link file:\033[0m {e}")
        return

    if not links_list:
        print("\033[93m⚠️ No valid links found in file.\033[0m")
        return

    # Apply TEST_LIMIT if set
    if TEST_LIMIT and len(links_list) > TEST_LIMIT:
        print(f"🧪 TEST MODE: limiting to first {TEST_LIMIT} of {len(links_list)} entries\n")
        links_list = links_list[:TEST_LIMIT]

    out = {}
    success_count = 0
    fail_count = 0

    print(f"\n=== 🚀 Starting API scrape: {len(links_list)} models ===\n")

    for i, (filename, url) in enumerate(links_list, 1):
        print(f"\033[94m→ [{i}/{len(links_list)}] Fetching via API:\033[0m {filename}")

        start_time = time.time()
        try:
            meta = fetch_from_api(filename, url)
        except Exception as e:
            print(f"  \033[91m❌ Failed:\033[0m {e}")
            fail_count += 1
            continue

        out_id = gen_id_from(filename, url)
        out[out_id] = meta
        success_count += 1

        duration = time.time() - start_time
        print(f"  ✓ Parsed in {duration:.1f}s — {meta['type']} / {meta['base_model']} / {meta['size']}")
        time.sleep(random.uniform(0.6, 1.2))  # polite delay

    # Save JSON
    try:
        ensure_dir(os.path.dirname(OUTPUT_JSON))
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\n\033[92m✅ JSON saved:\033[0m {OUTPUT_JSON}")
    except Exception as e:
        print(f"\033[91m❌ Failed to save output JSON:\033[0m {e}")

    print("\n=== 📊 Summary ===")
    print(f"✓ Successful: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"🧾 Output: {len(out)} entries\n")


if __name__ == "__main__":
    print("⚙️ Script loaded successfully.")
    print(f"LINKS file exists? {os.path.exists(LINKS)}")
    print("About to call main()...")
    main()
