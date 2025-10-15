##recursively checks folders for all files containing NSFW content

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# === CONFIGURATION ===
TARGET_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi", ".mkv",
    ".txt", ".json", ".md", ".zip", ".rar", ".7z", ".safetensors", ".ckpt", ".gguf"
}

NSFW_KEYWORDS = {
    # Ejaculatory & fluid-related #cum #release
    "ejaculation", "ejaculate", "ejaculating", "cum_", "_cum", " cum ", " cum", "cumming", "cumshot",
    "cumshots", "cum_on_face", "cum_on_body", "cum_in_mouth", "cum_in_ass",
    "cum_in_pussy", "cumdrip", "cumdripping", "drippingcum", "wetcum",
    "sperm", "semen", "seed", "load", "spunk", "spillage", "sticky", "messy",
    "orgasmic", "postorgasm", "afterglow", "climaxing", "milking",
    "milkingfetish", "milkingmachine", "bukkake", "gokkun", "titscum",
    "facecum", "bodycum", "bellycum", "breastcum", "backcum",
    "creampie", "creampies", "internalcum", "externalcum", "overflow",
    "oozing", "leaking", "leakage", "squirting", "squirt", "femaleejaculation",
    "wetorgasm", "juicy", "drippingwet", "arousalfluid", "lustfluid",
    "bodyfluids", "liquidfetish", "fluidfetish", "slimefetish",

    # Fetish-adjacent to fluids
    "watersports", "urination", "goldenshower", "wetfetish", "soak",
    "bodyslime", "slimeplay", "oilplay", "lotionplay", "sweatfetish",
    "sweaty", "saliva", "drool", "drooling", "licking", "tongueplay",
    "spit", "spitting", "spitroast", "doublepenetration", "dp", "triplepenetration",

    # Related descriptive euphemisms
    "drippinghot", "moist", "stickyload", "hotload", "massivecum",
    "spurting", "spurt", "gushing", "streaming", "splash", "flooded",
    "overflowing", "stickyfetish", "gooey", "wetmess", "orgasmfluid",
    "orgasmjuice", "lovejuice", "lustjuice", "nectar", "juices",
    "intimatefluid", "sexfluid", "bodyjuice"

        # General / Core
    "nsfw", "nude", "naked", "lewd", "sexual", "sex", "sexy", "sensual", "erotic",
    "adult", "explicit", "uncensored", "smut", "mature", "intimate", "suggestive",

    # Body / Anatomy #ass
    "boobs", "breasts", "tits", "nipples", "nipple", "cleavage", "chest", "underboob",
    "sideboob", "pussy", "vagina", "clitoris", "clit", "labia", "vulva", "penis",
    "cock", "dick", "shaft", "foreskin", "balls", "testicles", "cum", "sperm", "semen",
    "butt", "ass ", " ass ", " ass", "ass_", "_ass", "booty", "anus", "anal", "rectal", "prostate",

    # Actions / Acts
    "orgasm", "masturbation", "handjob", "blowjob", "fellatio", "deepthroat",
    "cumshot", "creampie", "ejaculation", "facial", "pegging", "fisting", "spanking",
    "threesome", "foursome", "groupsex", "orgy", "69", "missionary", "doggystyle",
    "cowgirl", "reversecowgirl", "rimming", "bondage", "bdsm", "submission", "dominatrix",

    # Fetishes / Kinks #master
    "fetish", "kink", "bdsmkitten", "ropeplay", "tentacle", "tentacles", "discipline",
    "humiliation", "leash", "collar", "submissive", "dominant", "slave",
    "latex", "leather", "lingerie", "panties", "thighhighs", "stockings", "garter",
    "heels", "fishnets", "corset", "choker", "gag", "whip", "strapon", "harness",

    # Anime / Subculture Tags
    "hentai", "ecchi", "oppai", "futa", "futanari", "loli", "shota", "yaoi", "yuri",
    "doujin", "rule34", "otokonoko", "ero", "eroart", "eroguro", "ecchigirl",
    "nakadashi", "oppailover", "nsfwart", "eroillustration", "ahegao", "oppaiart",

    # Adult Media / Platforms
    "porn", "pornhub", "xvideos", "xhamster", "xnxx", "camgirl", "camshow", "webcam",
    "onlyfans", "fansly", "chaturbate", "escort", "strip", "stripper", "hooker",
    "prostitute", "brothel", "nudes", "nudephoto", "sexvideo", "sexclip", "adultfilm",
    "jav", "avidol", "gravure", "softcore", "hardcore",

    # Descriptive Phrases
    "busty", "curvy", "thicc", "slutty", "naughty", "provocative", "seductive",
    "alluring", "tempting", "kissing", "fondling", "moaning", "pleasure", "pleasuring",
    "arousal", "aroused", "lust", "lustful", "wet", "hard", "stiff", "erect",
    "barelylegal", "teen", "younggirl", "youngboy", "schoolgirl", "maid", "nurse",
    "cosplaysex", "bathscene", "bedscene", "undressing", "pantydrop", "groping",
    "selfieboobs", "twerk", "bootyshake", "nsfwanime", "deepkiss",

    # Roleplay / Niche
    "incest", "rape", "molest", "forced", "abuse", "gangbang", "blackmail",
    "cuckold", "cheating", "pegged", "daddy", "mommy", "stepsister", "stepbrother",
    "teacherstudent", "officeaffair", "nanny", "massage", "voyeur", "exhibition",
    "peeping", "milf", "gilf", "cougar", "sugarbaby", "boytoy", "femboy",
    "crossdresser", "trap", "tgirl", "shemale", "ladyboy",

    # Artistic NSFW keywords
    "figurestudy", "sensualpose", "artnudity", "tastefulnude", "bodyreference",
    "life_drawing", "modelreference", "pinup", "burlesque", "glamour", "boudoir",

    # Misc. hidden / stylized tags
    "x_x", "nsfwmodel", "18plus", "18+", "xxxmodel", "adultonly", "spicyart",
    "nfsw", "no_sfw", "not_safe_for_work", "uncensor", "uncensored_art",
    "r18", "r-18", "r_18", "ero_ai", "sfw=false", "not_sfw", "spicy"

    # Gender-specific references #master #man
    "girl", "girls", "woman", "women", "lady", "ladies",
    "boy", "boys", "_man", " man", "_man_", " man ", "man ", "man_", "men", "male", "female",
    "girlfriend", "boyfriend", "lover", "mistress",
    "housewife", "hotwife", "husband", "wife",
    "couple", "couplesex", "marriedsex", "cheatingwife",
    "dominantwoman", "dominantman", "submissivewoman", "submissiveman",
    "alpha", "stud", "playboy", "playgirl", "seductress",
    "temptress", "nymph", "nympho", "nymphomania", "nymphomaniac",
    "succubus", "incubus", "goddess", "vixen", "tigress",
    "queenofsex", "kingofsex", "hotguy", "hotgirl", "hotman", "hotwoman",
    "babe", "babes", "hunk", "milf", "dilf", "gilf",
    "cougar", "sugarbaby", "sugarbabe", "boytoy", "femboy", "sissy",
    "crossdresser", "trap", "tgirl", "ladyboy", "transgirl", "transwoman",
    "transman", "transsexual", "transgender", "androgynous", "futanari",

    # Erotic / teasing adjectives & descriptors
    "sexy", "sexiest", "hot", "hotter", "hottest", "sultry", "steamy",
    "spicy", "naughty", "cheeky", "flirty", "flirtatious",
    "provocative", "tempting", "temptress", "suggestive",
    "seductive", "alluring", "ravishing", "voluptuous", "curvaceous",
    "busty", "bodacious", "temptation", "lusty", "lustful", "sinful",
    "kinky", "risque", "dirty", "filthy", "wild", "uninhibited",
    "intimate", "sensual", "passionate", "carnal", "pleasurable",
    "moodyerotic", "desire", "desiring", "romanticnight", "spicyart",
    "pleasure", "pleasing", "tease", "teasing", "pleasureplay",
    "fantasygirl", "fantasyboy", "dreamgirl", "dreamboy", "dreamwoman",
    "dreamman", "angelgirl", "badgirl", "goodgirl", "goodboy",
    "badboy", "lustqueen", "sexgoddess", "sexgod", "sexidol",
    "bedroom", "inbed", "nightin", "afterdark", "lovenight",
    "moonlightsex", "kissable", "touchme", "caress", "caressing",
    "enticing", "charming", "thrilling", "glamorous", "glamourshot",
    "pinup", "boudoir", "temptingpose", "teasingpose", "flirtylook",
    "comehither", "wink", "winkwink", "suggestion", "seduceme"

        # —— Erotic descriptors + gendered combos ——
    "sexy woman", "sexy man", "sexy girl", "sexy boy",
    "hot woman", "hot man", "hot girl", "hot guy",
    "naughty girl", "naughty boy", "cheeky girl", "cheeky boy",
    "busty milf", "curvy milf", "slutty teen", "barely legal teen",
    "schoolgirl uniform", "naughty nurse", "hotwife adventure",
    "dominant woman", "dominant man", "submissive woman", "submissive man",
    "bad girl", "bad boy", "good girl", "good boy",

    # —— Acts / positions (multi-word only) ——
    "blow job", "hand job", "foot job", "boob job", "tit job", "breast job",
    "deep throat", "reverse cowgirl", "doggy style", "missionary sex",
    "double penetration", "triple penetration", "anal sex", "vaginal sex",
    "face sitting", "face sit", "sit on face", "riding cock", "riding dick",
    "ride dick", "ride cock", "squirting orgasm", "female ejaculation",
    "anal creampie", "vaginal creampie",

    # —— Fluids / ejaculation phrasing ——
    "cum on face", "cum on tits", "cum on chest", "cum on body",
    "cum in mouth", "cum in pussy", "cum inside", "cum covered",
    "covered in cum", "dripping with cum", "post orgasm", "after orgasm",
    "sticky load", "hot load", "massive cum", "cum dripping",
    "creampie leak", "creampie oozing", "dripping wet", "wet orgasm",

    # —— Fetish & fluid-adjacent phrases ——
    "golden shower", "water sports", "urine play", "pee play",
    "oil play", "lotion play", "saliva play", "spit roast",
    "public sex", "public nudity", "public flashing",

    # —— Voyeur/exposure ——
    "upskirt shot", "downblouse shot", "open blouse", "open bra",
    "spread legs", "spread pussy", "anal gape", "vaginal gape", "gaping hole",

    # —— Platforms / media ——
    "only fans", "sex tape", "adult video", "cam girl", "web cam show",
    "amateur porn", "home made porn",

    # —— Anime / subculture phrasing ——
    "ahegao face", "oppai loli", "oppai lover", "nakadashi creampie",
    "paizuri titjob", "ero illustration", "nsfw anime",

    # —— Art NSFW ——
    "tasteful nude", "art nudity", "life drawing", "model reference", "glamour shot",
    "boudoir shoot", "pin up", "pinup pose", "come hither", "teasing pose",

        # Gendered + erotic descriptors
    "sexy woman", "sexy women", "sexy man", "sexy men", "sexy girl", "sexy guy",
    "hot woman", "hot women", "hot man", "hot men", "hot girl", "hot guy",
    "naughty girl", "naughty boy", "cheeky girl", "cheeky boy",
    "curvy woman", "curvy girl", "busty woman", "busty girl",
    "voluptuous woman", "voluptuous girl", "tight body", "perfect body",
    "good girl", "bad girl", "bad boy", "tempting woman", "tempting girl",
    "seductive woman", "seductive girl", "alluring woman", "alluring girl",
    "dominant woman", "dominant man", "submissive woman", "submissive man",
    "fantasy girl", "dream girl", "dream woman", "fantasy woman",
    "hotwife adventure", "cheating wife", "sexy couple", "adult couple",

    # Positions / acts (multiword only to reduce noise)
    "deep throat", "face sitting", "face sit", "sit on face",
    "reverse cowgirl", "doggy style", "missionary sex",
    "double penetration", "triple penetration", "anal sex", "vaginal sex",
    "tit job", "breast job", "boob job", "foot job", "hand job", "blow job",
    "titty fuck", "breast fuck", "boob fuck", "face fuck", "throat fuck",

    # Fluids / ejaculation phrasing
    "cum on face", "cum on tits", "cum on chest", "cum on body", "cum on hair",
    "cum on feet", "cum in mouth", "cum in pussy", "cum in ass",
    "covered in cum", "cum covered", "cum dripping", "dripping with cum",
    "post orgasm", "after orgasm", "sticky load", "hot load", "massive cum",
    "creampie leak", "creampie oozing", "dripping wet", "wet orgasm",
    "female ejaculation", "squirting orgasm",

    # Fetish & fluid-adjacent
    "golden shower", "water sports", "urine play", "pee play",
    "oil play", "lotion play", "wax play", "ice play", "saliva play", "spit play",
    "spit roast", "foot worship", "feet pics", "armpit fetish", "nipple play",

    # Exposure / voyeur
    "upskirt shot", "downblouse shot", "open blouse", "open bra",
    "see through top", "see through dress", "see through lingerie", "sheer lingerie",
    "micro bikini", "thong bikini", "no panties", "no bra",
    "public sex", "public nudity", "public flashing",
    "hidden cam", "spy cam", "caught on cam", "caught on tape", "caught on camera",

    # POV / scene context
    "pov blowjob", "pov bj", "pov handjob", "pov sex", "pov anal", "pov creampie",
    "shower sex", "bath sex", "car sex", "beach sex", "hotel sex", "office sex",
    "couch sex", "sofa sex", "kitchen sex", "bathroom sex",

    # Roleplay / outfits (multiword)
    "schoolgirl uniform", "naughty nurse", "maid cosplay", "bunny suit",
    "latex catsuit", "pole dance", "lap dance", "strip tease", "striptease",

    # Platforms / packy file names
    "only fans", "onlyfans leak", "fansly leak", "amateur porn", "home made porn",
    "adult video", "sex tape", "nsfw content", "nsfw pack", "mega pack",

    # Art NSFW
    "tasteful nude", "full nude", "full frontal", "art nudity",
    "life drawing", "model reference", "glamour shot", "boudoir shoot",
    "pin up", "pinup pose", "come hither", "teasing pose", "flirty look"
}
# ======================


def scan_filenames(base_path):
    matches = {}
    for root, _, files in os.walk(base_path):
        for name in files:
            lowered = name.lower()
            for kw in NSFW_KEYWORDS:
                if kw in lowered:
                    full_path = os.path.join(root, name)
                    matches[full_path] = [f"filename contains '{kw}'"]
                    break
    return matches


def scan_extensions(base_path):
    matches = {}
    for root, _, files in os.walk(base_path):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in TARGET_EXTENSIONS:
                full_path = os.path.join(root, name)
                matches[full_path] = [f"file extension '{ext}' is in target list"]
    return matches


def scan_both(base_path):
    file_matches = scan_filenames(base_path)
    ext_matches = scan_extensions(base_path)
    combined = file_matches.copy()
    for path, reasons in ext_matches.items():
        if path in combined:
            combined[path].extend([r for r in reasons if r not in combined[path]])
        else:
            combined[path] = reasons
    return combined


# === GUI APP ===
class NSFWScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NSFW Folder Scanner")
        self.root.geometry("950x600")

        self.folders = []
        self.mode = tk.StringVar(value="both")

        self.setup_ui()

    def setup_ui(self):
        # --- Folder selection ---
        folder_frame = ttk.LabelFrame(self.root, text="Target Folders", padding=10)
        folder_frame.pack(fill="x", padx=10, pady=10)

        self.folder_list = tk.Listbox(folder_frame, height=4)
        self.folder_list.pack(side="left", fill="x", expand=True)

        button_frame = tk.Frame(folder_frame)
        button_frame.pack(side="right", fill="y")

        ttk.Button(button_frame, text="Add Folder", command=self.add_folder).pack(fill="x", pady=2)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).pack(fill="x", pady=2)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).pack(fill="x", pady=2)

        # --- Mode selection ---
        mode_frame = ttk.LabelFrame(self.root, text="Scan Mode", padding=10)
        mode_frame.pack(fill="x", padx=10)

        ttk.Radiobutton(mode_frame, text="Filenames", variable=self.mode, value="filenames").pack(side="left", padx=5)
        ttk.Radiobutton(mode_frame, text="Extensions", variable=self.mode, value="extensions").pack(side="left", padx=5)
        ttk.Radiobutton(mode_frame, text="Both", variable=self.mode, value="both").pack(side="left", padx=5)

        # --- Results table ---
        result_frame = ttk.Frame(self.root)
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Directory", "Filename", "Reason")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("Directory", text="Directory Path")
        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Reason", text="Reason")

        self.tree.column("Directory", width=300, anchor="w")
        self.tree.column("Filename", width=200, anchor="w")
        self.tree.column("Reason", width=400, anchor="w")

        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<ButtonRelease-1>", self.on_click_copy_path)

        # --- Bottom Controls ---
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(control_frame, text="Start Scan", command=self.start_scan).pack(side="left", padx=5)
        self.status_label = ttk.Label(control_frame, text="Ready.")
        self.status_label.pack(side="right", padx=10)

    # === Folder list actions ===
    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if folder and folder not in self.folders:
            self.folders.append(folder)
            self.folder_list.insert("end", folder)

    def remove_selected(self):
        selection = self.folder_list.curselection()
        for i in reversed(selection):
            del self.folders[i]
            self.folder_list.delete(i)

    def clear_all(self):
        self.folders.clear()
        self.folder_list.delete(0, "end")

    # === Scan logic ===
    def start_scan(self):
        if not self.folders:
            messagebox.showwarning("No Folders", "Please add at least one folder to scan.")
            return

        self.tree.delete(*self.tree.get_children())
        total_found = 0

        for folder in self.folders:
            self.status_label.config(text=f"Scanning: {folder}...")
            self.root.update_idletasks()

            if self.mode.get() == "filenames":
                results = scan_filenames(folder)
            elif self.mode.get() == "extensions":
                results = scan_extensions(folder)
            else:
                results = scan_both(folder)

            for path, reasons in results.items():
                directory = os.path.dirname(path)
                filename = os.path.basename(path)
                for r in reasons:
                    self.tree.insert("", "end", values=(directory, filename, r))
                    total_found += 1

        self.status_label.config(text=f"Scan complete. {total_found} items found.")
        messagebox.showinfo("Scan Complete", f"Scan complete.\nTotal matches found: {total_found}")

    # === Copy path to clipboard ===
    def on_click_copy_path(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        col = self.tree.identify_column(event.x)
        if col != "#1":  # Only copy if Directory column clicked
            return
        values = self.tree.item(selected_item, "values")
        if not values:
            return
        directory_path = values[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(directory_path)
        self.status_label.config(text=f"Copied path: {directory_path}")
        self.root.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    app = NSFWScannerApp(root)
    root.mainloop()
