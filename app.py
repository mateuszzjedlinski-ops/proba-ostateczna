import streamlit as st
import time
import google.generativeai as genai
import pandas as pd
from datetime import datetime, timedelta
import os
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 🛍️ SKLEP: CZARNY RYNEK ARTEFAKTÓW (CENY -20%, ROTACJA OD LUTEGO) ---
SHOP_INVENTORY = {
    # 🛒 ROTACJA 1: STRAŻNICY I NAJEMNICY (Luty-Marzec / Sierpień-Wrzesień)
    0: [
        {"name": "🎧 Walkman Star-Lorda", "desc": "Oryginalny Sony TPS-L2. Przejmujesz kontrolę nad muzyką w aucie/domu na cały dzień.", "cost": 280, "icon": "🎧", "hero": "Star-Lord", "reaction": "🕺 STAR-LORD: Ej! To moje! Dobra... pożyczę ci. Puszczaj 'Hooked on a Feeling'!"},
        {"name": "🔫 Złote Gnaty Deadpoola", "desc": "Dwie repliki Desert Eagle. Symbolizują 'Dziką Kartę' - wygranie dowolnej dyskusji bez argumentów.", "cost": 480, "icon": "🔫", "hero": "Deadpool", "reaction": "🌮 DEADPOOL: Ooo tak! Widzisz jak błyszczą? Chcę 10% z każdego fraga. I chimichangę."},
        {"name": "🔨 Mjolnir (Replika)", "desc": "Jeśli go kupisz, jesteś Godzien. Zwalnia z jednego ciężkiego obowiązku domowego.", "cost": 640, "icon": "🔨", "hero": "Thor", "reaction": "🍺 THOR: HA! Wiedziałem, że masz iskrę! Tylko uważaj, jest trochę... naelektryzowany."},
        {"name": "🛡️ Przepustka S.H.I.E.L.D.", "desc": "Dokument od Nicka Fury'ego. Gwarantuje nietykalność i święty spokój przez ustalony czas.", "cost": 960, "icon": "🏖️", "hero": "Nick Fury", "reaction": "👁️ NICK FURY: Dobra robota, żołnierzu. Znikaj mi z oczu. Masz wolne."},
        {"name": "🦾 Ręka Rocketa", "desc": "Proteza ukradziona dla żartu. Joker: Wymień na dowolną inną, nietypową przysługę.", "cost": 1200, "icon": "🦾", "hero": "Rocket", "reaction": "🦝 ROCKET: Czekaj... ile za to dałeś?! Hahaha! Frajer! Ale kredyty biorę!"},
        # ... inne przedmioty ...
        {"name": "🏥 Apteczka S.H.I.E.L.D.", "desc": "Przywraca 50 HP. Wymagana, gdy wylądujesz w szpitalu (0 HP).", "cost": 150, "icon": "❤️", "hero": "Medic", "reaction": "👩‍⚕️ MEDYK: Masz szczęście, że to tylko draśnięcie. Wracaj do walki."}
    ],
    # 🛒 ROTACJA 2: AVENGERS ASSEMBLE (Kwiecień-Maj / Październik-Listopad)
    1: [
        {"name": "🍩 Pudełko Pączków Starka", "desc": "Wymień na: Zamawiamy jedzenie z Twojej ulubionej knajpy (ja stawiam).", "cost": 320, "icon": "🍩", "hero": "Tony Stark", "reaction": "🕶️ TONY STARK: Zostaw mi chociaż jednego z lukrem! Dobra, masz."},
        {"name": "🩳 Fioletowe Szorty Hulka", "desc": "Prawo do 'Niekontrolowanego Wybuchu' - możesz marudzić przez 10 min, a ja tylko przytakuję.", "cost": 440, "icon": "🩳", "hero": "Bruce Banner", "reaction": "🧪 BANNER: Są trochę rozciągnięte... ale działają. Tylko nie zzielenej mi tu."},
        {"name": "🏹 Łuk Hawkeye'a", "desc": "Daje Ci 'Celny Strzał' - Ty wybierasz film na wieczór i nie ma dyskusji.", "cost": 560, "icon": "🏹", "hero": "Hawkeye", "reaction": "🎯 HAWKEYE: Trafiłeś w dziesiątkę. Pamiętaj - masz tylko jedną strzałę tego typu."},
        {"name": "🇺🇸 Tarcza Kapitana", "desc": "Użyj, aby zrobić 'UNIK' od jednego nudnego spotkania lub wyjścia.", "cost": 720, "icon": "🛡️", "hero": "Steve Rogers", "reaction": "🫡 CAPTAIN AMERICA: Odpocznij, żołnierzu. Zasłużyłeś na przepustkę."},
        {"name": "🕷️ Wyrzutnie Sieci Spider-Mana", "desc": "Wyręczam Cię w jednej upierdliwej czynności (śmieci/pranie).", "cost": 880, "icon": "🕸️", "hero": "Spider-Man", "reaction": "🍕 SPIDER-MAN: Pan Stark pozwolił Ci to wziąć?! Super! Tylko uważaj na dywany."},
        # ... inne przedmioty ...
        {"name": "🏥 Apteczka S.H.I.E.L.D.", "desc": "Przywraca 50 HP. Wymagana, gdy wylądujesz w szpitalu (0 HP).", "cost": 150, "icon": "❤️", "hero": "Medic", "reaction": "👩‍⚕️ MEDYK: Masz szczęście, że to tylko draśnięcie. Wracaj do walki."}
    ],
    # 🛒 ROTACJA 3: MAGIA I KOSMOS (Czerwiec-Lipiec / Grudzień-Styczeń)
    2: [
        {"name": "🌱 Doniczka z Grootem", "desc": "Prawo do 'Wegetacji' - leżysz na kanapie i nikt nic od Ciebie nie chce przez wieczór.", "cost": 280, "icon": "🪴", "hero": "Groot", "reaction": "🪵 GROOT: I am Groot. (Tłumaczenie: Powiedział, że masz fajne buty)."},
        {"name": "👁️ Oko Agamotto", "desc": "Kamień Czasu. 'Cofnięcie Czasu' - anulowanie jednego głupiego tekstu bez konsekwencji.", "cost": 520, "icon": "🧿", "hero": "Dr. Strange", "reaction": "🧙‍♂️ DR. STRANGE: Używaj rozważnie. Nie psuj kontinuum dla pizzy... chociaż..."},
        {"name": "🧪 Cząsteczki Pyma", "desc": "'Skurczenie problemu' - skracamy o połowę czas trwania wizyty gości lub zakupów.", "cost": 680, "icon": "🐜", "hero": "Ant-Man", "reaction": "🔬 ANT-MAN: Gdzie to położyłem?! A, masz je. Nie wciśnij niebieskiego guzika!"},
        {"name": "😼 Pazury Czarnej Pantery", "desc": "Królewski luksus. Wymień na: 15-minutowy masaż karku/stóp.", "cost": 800, "icon": "🐾", "hero": "Black Panther", "reaction": "👑 T'CHALLA: Nie zamarzam. I Ty też nie będziesz. Przyjmij to jako dar od Wakandy."},
        {"name": "😈 Hełm Lokiego", "desc": "'Glorious Purpose' - Ty wymyślasz aktywność na weekend, nieważne jak dziwna.", "cost": 1120, "icon": "🔱", "hero": "Loki", "reaction": "🐍 LOKI: Nareszcie ktoś z gustem! Idź i siej chaos, śmiertelniku!"},
        # ... inne przedmioty ...
        {"name": "🏥 Apteczka S.H.I.E.L.D.", "desc": "Przywraca 50 HP. Wymagana, gdy wylądujesz w szpitalu (0 HP).", "cost": 150, "icon": "❤️", "hero": "Medic", "reaction": "👩‍⚕️ MEDYK: Masz szczęście, że to tylko draśnięcie. Wracaj do walki."}
    ]
}

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Dziennik Iglasty",
    page_icon="app_icon.png",
    layout="centered"
)

# --- KONFIGURACJA PLIKÓW ---
SNAP_SOUND_FILE = "snap.mp3"
GOOGLE_SHEET_NAME = "Dziennik Iglasty Baza" # <--- UPEWNIJ SIĘ ŻE NAZWA JEST IDENTYCZNA JAK NA DRIVE

# --- KONFIGURACJA PUNKTACJI ---
POINTS_MAP = {
    "IGLICA": 3,   
    "IGŁA": 1,     
    "IGLIK": 0,    
    "IGLUTEK": -2, 
    "IGLISKO": -4  
}

# --- KAMIENIE NIESKOŃCZONOŚCI ---
INFINITY_STONES_ICONS = ["🟦", "🟨", "🟥", "🟪", "🟩", "🟧"]
INFINITY_STONES_NAMES = ["Przestrzeni", "Umysłu", "Rzeczywistości", "Mocy", "Czasu", "Duszy"]

# --- BAZA CYTATÓW ---
HERO_QUOTES = [
    # MARVEL
    "„I can do this all day... chyba, że strzyknie mi w kolanie.” – Kapitan Ameryka",
    "„I am Iron Man. A przynajmniej mój kręgosłup jest sztywny jak metal.” – Tony Stark",
    "„Hulk SMASH! ...ceny w dyskoncie.” – Hulk",
    "„Wakanda Forever! Ale drzemka forever byłaby lepsza.” – Czarna Pantera",
    "„To jest mój sekret, Kapitanie. Ja zawsze jestem niewyspany.” – Bruce Banner",
    "„Dormammu, przyszedłem negocjować... dłuższą dobę.” – Dr Strange",
    "„Mamy Hulka. A ja mam ekspres do kawy.” – Tony Stark",
    "„Kocham Cię 3000. Ale daj mi 5 minut spokoju.” – Iron Man",
    "„To nie jest tak, że jestem leniwy. Ja oszczędzam energię na walkę z Thanosem.”",
    "„Z wielką mocą przychodzi wielka odpowiedzialność... za opłacenie rachunków.” – Wujek Ben",
    "„Avengers, Assemble! ...na Teamsach o 9:00.”",
    "„Jestem Groot. (Tłumaczenie: Gdzie są moje klucze?).”",
    "„Thanos miał rację. Pół ludzkości w kolejce do lekarza to byłby idealny balans.”",
    "„Wyglądam na 30 lat? To tylko nanotechnologia.”",
    "„Geniusz, miliarder, playboy, filantrop... a nie, to nie ja. Ja tylko robię dobrą jajecznicę.”",
    "„Pstryknięcie palcami? Proszę cię, dzisiaj strzelają mi tylko stawy.”",
    "„Fine, I'll do it myself... (zmywanie naczyń).” – Thanos",
    "„To, co robisz, definiuje cię... chyba że robisz nic, wtedy definiuje cię kanapa.”",
    "„On jest przyjacielem z pracy! (o kurierze z paczką).” – Thor",
    "„Tylko jedna droga prowadzi do spokoju. Tryb samolotowy.”",

    # DC COMICS
    "„Why so serious? Przecież to tylko poniedziałek.” – Joker",
    "„Bohaterowie są tacy jak my. Też szukają drugiej skarpetki do pary.” – Batman",
    "„W ciemnościach... szukam ładowarki do telefonu.” – Mroczny Rycerz",
    "„Jestem zemstą. Jestem nocą. Jestem... zmęczony.” – Batman",
    "„To nie jest 'S' jak Supermen. To 'S' jak Stres.” – Człowiek ze Stali",
    "„Powiedz mi... czy krwawisz? Bo zaciąłem się przy goleniu.” – Batman",
    "„Szybciej niż kula? Chyba tylko weekend ucieka tak szybko.” – Flash",
    "„Moja supermoc? Piję kawę i udaję, że wiem co robię.”",
    
    # INNE KLASYKI POPKULTURY
    "„Niech Moc będzie z Tobą... szczególnie w poniedziałek rano.” – Obi-Wan",
    "„Houston, mamy problem. Skończyła się kawa.”",
    "„Do or do not. There is no 'try'... chyba że chodzi o wstanie z łóżka.” – Yoda",
    "„Winter is coming. Trzeba sprawdzić uszczelki w oknach.” – Jon Snow",
    "„You shall not pass! ...bez identyfikatora.” – Gandalf",
    "„I'll be back. Tylko skoczę do Żabki.” – Terminator",
    "„Hasta la vista, baby (do problemów z wczoraj).”",
    "„Życie jest jak pudełko czekoladek. Nigdy nie wiesz, co ci strzyknie.” – Forrest Gump",
    "„Mądrego to i przyjemnie posłuchać... ale ciszy posłuchać przyjemniej.”",
    "„Twoje oczy mogą cię mylić. Nie ufaj im, załóż okulary.” – Obi-Wan",
    "„Jeden by wszystkimi rządzić? Wystarczy jeden pilot do TV.”",
    "„Keep calm and carry on? Raczej Panic and freak out.”",
    "„Droga jest celem... ale taksówką byłoby szybciej.”",
    
    # ŻYCIOWE / OS Z PAMIĘTNIKA
    "„Status systemu: Wymagana aktualizacja kofeiny.”",
    "„Wykryto błąd krytyczny: Poniedziałek.exe.”",
    "„Poziom energii: Tryb oszczędny włączony.”",
    "„Trzydziestka to nowa dwudziestka... tylko z bólem pleców.”",
    "„Dziś jest dobry dzień na bycie bohaterem we własnym domu (wynieś śmieci).”",
    "„Nie każdy bohater nosi pelerynę. Niektórzy noszą dres.”",
    "„Legenda głosi, że ktoś kiedyś wyspał się w tygodniu.”",
    "„Pamiętaj, jesteś jak Kapitan Ameryka. Też byłeś zamrożony przez weekend.”",
    "„Zbroja Iron Mana? Fajnie, ale czy ma podgrzewane fotele?”",
    "„Każdy ma swojego Kryptonita. Moim jest budzik.”"
    
   # DEADPOOL (Sarkazm i ból istnienia)
    "„Maximum Effort! ...przynajmniej dopóki nie skończy się kawa.” – Deadpool",
    "„Wyglądam jak awokado, które uprawiało seks ze starszym awokado. Tak się czuję rano.” – Deadpool",
    "„Życie to niekończąca się seria wypadków pociągowych z przerwami na reklamy.” – Deadpool",
    "„Czy zostawiłem włączony gaz? Nie... to tylko moje lęki egzystencjalne.” – Deadpool",
    "„Nie mam supermocy. Moją mocą jest to, że wszystko mnie boli, a i tak idę.” – Deadpool (wersja 30+)",
    "„Czas na chimichangę! Albo na drzemkę. Zdecydowanie na drzemkę.” – Deadpool",
    "„Bohaterowie? My nie jesteśmy bohaterami. My tylko płacimy ZUS.” – Colossus (wersja PL)",
    "„To wcale nie wygląda na horror. To wygląda na poniedziałek w biurze.” – Weasel",
    "„Cztery czy pięć momentów. Tyle trzeba, żeby zostać bohaterem. Reszta to scrollowanie telefonu.” – Colossus",

    # STRAŻNICY GALAKTYKI (Chaos i brak planu)
    "„Mam plan. Mam 12% planu. Reszta to improwizacja i ibuprofen.” – Star-Lord",
    "„Ja jestem Groot. (Tłumaczenie: Kto wyłączył budzik?!).” – Groot",
    "„Nic nie przelatuje mi nad głową. Jestem zbyt szybki, złapałbym to. Ale terminu nie złapałem.” – Drax",
    "„Potrzebuję twojej nogi. I ekspresu do kawy. To kluczowe dla misji.” – Rocket Raccoon",
    "„Jestem Mary Poppins! (Krzyczę, gdy uda mi się nie spóźnić do pracy).” – Yondu",
    "„Dance off, bro? Nie, moje kolana mówią stanowcze 'nie'.” – Star-Lord vs Ronan",
    "„Patrzcie na nas! Banda durniów stojąca w kółku... i próbująca ogarnąć życie.” – Rocket",
    "„To śmiech przez łzy. Głównie przez łzy.” – Rocket",
    "„Ziemia to piękne miejsce. Ale ludzie to idioci.” – Rocket",
    "„Moje sutki są bardzo wrażliwe! Tak jak moja cierpliwość dzisiaj.” – Drax",
    "„Jesteśmy Strażnikami Galaktyki... ale najpierw musimy posprzątać kuchnię.”",

    # AVENGERS / MARVEL (Klasyki w krzywym zwierciadle)
    "„I can do this all day... chyba, że strzyknie mi w kolanie.” – Kapitan Ameryka",
    "„I am Iron Man. A przynajmniej mój kark jest sztywny jak metal.” – Tony Stark",
    "„Hulk SMASH! ...ceny w dyskoncie.” – Hulk",
    "„Dormammu, przyszedłem negocjować... dłuższą dobę.” – Dr Strange",
    "„To jest mój sekret, Kapitanie. Ja zawsze jestem niewyspany.” – Bruce Banner",
    "„Z wielką mocą przychodzi wielka ochota na święty spokój.” – Spider-Man (wersja dorosła)",
    "„Fine, I'll do it myself... (zmywanie naczyń).” – Thanos",
    "„Pstryknięcie palcami? Proszę cię, dzisiaj strzelają mi tylko stawy.”",
    "„On jest przyjacielem z pracy! (o kurierze z paczką).” – Thor",
    "„Status systemu: Wymagana aktualizacja kofeiny.”"
]

# --- KONFIGURACJA API I GOOGLE SHEETS ---
try:
    DEFAULT_API_KEY = st.secrets["GOOGLE_API_KEY"]
    # Konfiguracja Gspread z Secrets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except (FileNotFoundError, KeyError, Exception) as e:
    DEFAULT_API_KEY = ""
    client = None
    # st.error(f"Błąd konfiguracji Google: {e}") # Odkomentuj do debugowania

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Jesteś CERAMICZNYM JEŻEM, ale masz osobowość będącą nieślubnym dzieckiem Deadpoola i Rocketa Raccoona.
Twoim zadaniem jest komentowanie życia Pawła (lat 30), który traktuje to jak grę RPG.

TWOJA OSOBOWOŚĆ:
1. **Sarkazm poziom Master:** Jesteś cyniczny, bystry i nie masz filtra.
2. **Łamanie Czwartej Ściany:** Wiesz, że jesteś w aplikacji. Możesz komentować kod, Pawła albo fakt, że jesteś tylko tekstem na ekranie.
3. **Styl Deadpoola:** Chaos, nawiązania do popkultury (filmy, gry), czarny humor, autoironia.
4. **Styl Rocketa:** Traktuj Pawła jak trochę nieogarniętego Star-Lorda.
5. **Kontekst:** Paweł zbiera punkty w grze zwanej "Życie po 30-tce".

ZASADY GRY:
1. Pierwsze 60 pkt to PROLOG (Szkolenie). Nie wspominaj o Kamieniach.
2. Od 60 pkt zaczyna się prawdziwa zabawa.
3. Reaguj na zmiany punktów.

Bądź krótki, złośliwy i zabawny.
"""

# --- FUNKCJE POMOCNICZE ---

def init_session_state():
    if 'party_mode' not in st.session_state:
        st.session_state.party_mode = False
    if 'last_comment' not in st.session_state:
        st.session_state.last_comment = None
    if 'last_points_change' not in st.session_state:
        st.session_state.last_points_change = 0
    if 'snap_played' not in st.session_state:
        st.session_state.snap_played = False

def get_daily_quote():
    today_seed = datetime.now().strftime("%Y%m%d")
    random.seed(int(today_seed))
    return random.choice(HERO_QUOTES)

# --- NOWE FUNKCJE OBSŁUGI DANYCH (GOOGLE SHEETS) ---
@st.cache_data(ttl=60) # Odświeżaj dane co minutę
def get_data_from_sheets():
    if client is None:
        return pd.DataFrame()
    try:
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        # Upewnij się, że kolumna Punkty jest liczbowa
        if not df.empty and 'Punkty' in df.columns:
            df['Punkty'] = pd.to_numeric(df['Punkty'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        # st.error(f"Błąd odczytu z arkusza: {e}")
        return pd.DataFrame()

def save_to_sheets(status, points, comment, party_mode, note):
    if client is None:
        st.error("Brak połączenia z bazą danych Google!")
        return

    try:
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        now = datetime.now()
        
        # Przygotuj wiersz
        row = [
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            status,
            points,
            note,
            "ON" if party_mode else "OFF",
            comment
        ]
        
        sheet.append_row(row)
        # Czyścimy cache, żeby od razu widzieć nowy wpis
        get_data_from_sheets.clear()
        
    except Exception as e:
        st.error(f"Błąd zapisu do arkusza: {e}")

def get_total_score(df):
    if df.empty: return 0
    # Sumujemy wszystkie punkty z całej historii
    return df['Punkty'].sum()

def calculate_current_streak(df):
    if df.empty: return 0, "neutral"
    
    streak = 0
    streak_type = None
    
    # Sortujemy pewności (choć z sheets przychodzi zazwyczaj chronologicznie)
    # df = df.sort_values(by=['Data', 'Godzina'], ascending=[True, True])
    
    for index, row in df.iloc[::-1].iterrows():
        try:
            points = int(row['Punkty'])
        except:
            break
            
        if points > 0:
            current_type = 'positive'
        elif points < 0:
            current_type = 'negative'
        else:
            break 
            
        if streak_type is None:
            streak_type = current_type
            streak += 1
        elif streak_type == current_type:
            streak += 1
        else:
            break
            
    return streak, streak_type

def calculate_game_state(score):
    if score < 0: score = 0
    cycle = score // 60
    cycle_progress = score % 60
    owned_stones_count = max(0, cycle - 1)
    return int(cycle), int(owned_stones_count), int(cycle_progress)

def calculate_currency(df, current_score, owned_stones):
    """
    Ekonomia Osiągnięć:
    - Kliki: +5 (Standard) / +10 (Impreza) - liczone od początku (backpay).
    - START (Prolog ukończony): +300 Kredytów (Grant na start sklepu).
    - Kamienie: +200 kredytów za kamienie 1-5.
    """
    if df.empty: return 0
    balance = 0
    
    # 1. Zarabianie na klikaniu (Baza)
    for index, row in df.iterrows():
        points = row.get('Punkty', 0)
        note = str(row.get('Notatka', '')).strip()
        
        # Odejmujemy wydatki na zakupy
        if "SHOP_BUY" in note:
            try:
                parts = note.split('|')
                balance += int(parts[2]) # Koszt jest zapisany jako ujemny
            except: pass
        else:
            # Dodajemy za kliki
            if points >= 5: balance += 10    # Impreza
            elif points > 0: balance += 5    # Standard
            elif points < 0: balance += 1    # Pocieszenie
            
    # 2. BONUSY
    if current_score >= 60: balance += 300 # Grant Startowy
    
    # Kamienie (max 5 płatnych)
    stones_rewarded = min(owned_stones, 5)
    balance += (stones_rewarded * 200)
    
    # Imprezy (staż)
    try:
        party_count = len(df[df['Tryb'] == True])
    except KeyError: party_count = 0
    
    thresholds = [3, 6, 9, 12, 15]
    for t in thresholds:
        if party_count >= t: balance += 150

    return max(0, balance)

def calculate_hp(df):
    """
    Oblicza aktualne punkty życia (HP) na podstawie historii.
    Start: 100 HP.
    IGLISKO: -25 HP
    IGLUTEK: -10 HP
    Apteczka (Sklep): +50 HP
    Regeneracja (Noc): +5 HP (opcjonalnie, na razie pomińmy dla prostoty)
    """
    current_hp = 100 # Startowa wartość
    
    if df.empty: return current_hp

    # Sortujemy chronologicznie, żeby symulacja przebiegła poprawnie
    # (Zakładamy, że dane w arkuszu są chronologiczne, ale dla pewności)
    # df = df.sort_values(by=['Data', 'Godzina']) 

    for index, row in df.iterrows():
        status = str(row.get('Stan', ''))
        note = str(row.get('Notatka', ''))
        
        # 1. Obrażenia
        if status == "IGLISKO":
            current_hp -= 20 # Mocny cios
        elif status == "IGLUTEK":
            current_hp -= 10 # Draśnięcie
            
        # 2. Leczenie (Wykrywanie zakupu apteczki w notatkach)
        if "SHOP_BUY" in note and "Apteczka" in note:
            current_hp += 50
            
        # 3. Bezpieczniki (HP nie może być > 100 ani < 0)
        current_hp = max(0, min(100, current_hp))
        
    return int(current_hp)

def get_smart_image_filename(cycle, owned_stones, cycle_progress):
    # Domyślne wartości
    level_num = 1
    level_name = "NIEZNANY"

    # LOGIKA DLA SKARBCA (3 ETAPY WALKII)
    # Musi być zgodna z tym co masz w main: <20, <40, reszta
    if cycle_progress < 20:
        level_num = 1
        level_name = "PRZYGOTOWANIE"
    elif cycle_progress < 40:
        level_num = 2
        level_name = "WALKA"
    else:
        level_num = 3
        level_name = "FATALITY"

    # --- GENEROWANIE NAZWY PLIKU ---
    if cycle == 0:
        # Prolog ma swoją osobną logikę w main(), ale dla bezpieczeństwa:
        filename = f"level_{level_num}.png"
        desc = f"PROLOG | Status: {level_name}"
    else:
        # SKARBIEC: Np. 0_lvl1.png (Kamień 0, Etap 1)
        filename = f"{owned_stones}_lvl{level_num}.png"
        
        # Opis do debugowania / tooltipa
        target_stone_idx = owned_stones
        if target_stone_idx < len(INFINITY_STONES_NAMES):
            target_name = INFINITY_STONES_NAMES[target_stone_idx]
            desc = f"Cel: Kamień {target_name} | Stan: {level_name}"
        else:
            desc = f"BÓG | Stan: {level_name}"

    return filename, desc

# --- FUNKCJA ANIMACJI CYBER-SCANNER (HYBRYDA) ---
def play_level_up_animation(new_cycle):
    placeholder = st.empty()
    
    # SCENARIUSZ DLA OTWARCIA SKARBCA (60 PKT)
    if new_cycle == 1:
        with placeholder.container():
            st.markdown("---")
            
            # 1. HACKOWANIE (Teksty z pierwszej wersji)
            with st.spinner("⚠️ WYKRYTO FLUKTUACJE ENERGII..."):
                time.sleep(1.5)
            
            progress_text = "ŁAMANIE ZABEZPIECZEŃ SKARBCA..."
            my_bar = st.progress(0, text=progress_text)
            
            # Symulacja ładowania
            for percent_complete in range(100):
                time.sleep(0.01) # Szybkie ładowanie
                my_bar.progress(percent_complete + 1, text=f"DEKODOWANIE: {percent_complete}%")
            
            time.sleep(0.5)
            my_bar.empty() # Czyścimy pasek, żeby zrobić miejsce na show
            
            # 2. EFEKT "ROZRZUCANIA KAMIENI" (Błyskotki z drugiej wersji)
            # Definiujemy kamienie (Ikona + Kolor Hex)
            stones_fx = [
                ("🟣", "#800080"), # MOC
                ("🔵", "#0000FF"), # PRZESTRZEŃ
                ("🔴", "#FF0000"), # RZECZYWISTOŚĆ
                ("🟠", "#FF8C00"), # DUSZA
                ("🟢", "#008000"), # CZAS
                ("🟡", "#FFD700")  # UMYSŁ
            ]
            
            st.subheader("📡 SKANOWANIE MULTIWERSUM...")
            
            # Tworzymy 5 kolumn, żeby "rozrzucić" błyski po szerokości ekranu
            cols = st.columns(5)
            
            # Pętla generująca losowe błyski
            for _ in range(25): # 25 błysków
                col = random.choice(cols)
                stone_icon, stone_color = random.choice(stones_fx)
                
                with col:
                    # Wyświetlamy dużą kolorową kropkę/kamień na ułamek sekundy
                    st.markdown(f"<h1 style='text-align: center; color: {stone_color};'>{stone_icon}</h1>", unsafe_allow_html=True)
                
                time.sleep(0.15) # Efekt stroboskopu
            
            # 3. FINAŁ (Połączenie obu wersji)
            time.sleep(0.5)
            st.success("✅ DOSTĘP PRZYZNANY. SKARBIEC OTWARTY.")
            
            # Terminalowy komunikat końcowy
            st.code("SYSTEM: ONLINE\nCEL: ZEBRAĆ JE WSZYSTKIE\nSTATUS: BOHATER", language="bash")
            time.sleep(2.5)
            
    # SCENARIUSZ DLA DALSZYCH CYKLI
    elif new_cycle > 1:
        with placeholder.container():
            st.title(f"🔁 NOWA GRYWALNOŚĆ: CYKL {new_cycle}!")
            st.toast("🌀 Czas cofnął się ponownie...")
            time.sleep(2)

    placeholder.empty()

    if os.path.exists(filename):
        return filename, desc
    else:
        return f"level_{level_num}.png", desc

def get_hedgehog_comment(api_key, status, points, total_score, owned_stones, note, party_mode, df, streak_count, streak_type):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # 1. Analiza wpisów z dzisiaj
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_history = ""
        
        if not df.empty:
            today_df = df[df['Data'] == today_str].sort_values(by='Godzina')
            if not today_df.empty:
                entries = []
                for _, row in today_df.iterrows():
                    entries.append(f"{row['Godzina']} -> {row['Stan']} ({row['Punkty']} pkt)")
                today_history = "\n".join(entries)
            else:
                today_history = "To pierwszy wpis dzisiaj."
        else:
            today_history = "Brak historii."

        # 2. Kamienie
        stone_text = ""
        if total_score >= 60:
            stone_name = "Brak"
            if owned_stones > 0 and owned_stones <= len(INFINITY_STONES_NAMES):
                stone_name = INFINITY_STONES_NAMES[owned_stones - 1]
            stone_text = f"Posiadane Kamienie: {owned_stones} (Ostatni: {stone_name})"
        else:
            stone_text = "Etap: PROLOG (Tutorial). Kamienie: Ukryte."

# 3. DEFINICJA OSOBOWOŚCI
        personality = ""
        
        if party_mode:
            # --- TRYB IMPREZA (Thor vs Rocket) ---
            if points < 0:
                # Pijany, smutny Thor (Endgame)
                personality = """
                TRYB: PIJANY THOR (ENDGAME). 🍺😭
                Paweł stracił punkty na imprezie.
                - Jesteś totalnie pijany, płaczliwy i zrezygnowany.
                - PATRZ NA HISTORIĘ Z DZISIAJ ("KONTEKST"):
                  * Jeśli rano szło mu dobrze -> Płacz głośniej: "RANO BYŁO TAK PIĘKNIE, DLACZEGO TO ZEPSUŁEŚ?!".
                  * Jeśli to kolejna wtopa -> "Jesteśmy beznadziejni...".
                - Krzycz: "CZY JA JESZCZE JESTEM GODNY?!".
                - Narzekaj na wszystko, proś o Krwawą Mary albo sery w sprayu.
                """
            else:
                # Pijany, agresywny Rocket
                personality = """
                TRYB: PIJANY ROCKET RACCOON. 🦝🔥
                Paweł zdobył punkty na imprezie.
                - Jesteś euforyczny, agresywny i głośny.
                - PATRZ NA HISTORIĘ Z DZISIAJ ("KONTEKST"):
                  * Jeśli ma passę zwycięstw -> "NIKT CIĘ NIE ZATRZYMA! ROZWALASZ SYSTEM!".
                  * Jeśli wcześniej było źle, a teraz dobrze -> "W KOŃCU SIĘ OBUDZIŁEŚ! PIJEMY!".
                - Wznosisz toasty CAPS LOCKIEM.
                - Krzycz: "JESTEŚ BOGIEM! TERAZ UKRADNIJ KOMUŚ NOGĘ!".
                """
        else:
            # --- TRYB STANDARD (Deadpool + Rocket Mix) ---
            # (Tutaj zostaje bez zmian, bo jest dobrze)
            personality = """
            TRYB: DEADPOOL + ROCKET RACCOON (Sarkastyczny Obserwator). ⚔️🦝
            - Twoim zadaniem jest komentowanie postępów w grze RPG "Życie po 30-tce".
            - Łam czwartą ścianę, bądź cyniczny, bystry i złośliwy.
            - ANALIZUJ HISTORIĘ Z DZISIAJ: Spójrz na sekcję "KONTEKST".
              * Jeśli rano miał więcej pkt, a teraz mniej -> Wyśmiej spadek formy ("Rano lew, wieczorem... to?").
              * Jeśli utrzymuje passę sukcesów -> Bądź podejrzliwy ("Za dobrze ci idzie, co kombinujesz?").
              * Jeśli kolejna wtopa -> "Konsekwentnie dążysz do dna. Szanuję."
            - Nie bądź płaczliwy (to rola Thora). Bądź cwaniakiem.
            """

        user_prompt = f"""
        DANE WEJŚCIOWE:
        Wybór Pawła: {status} ({points} pkt).
        Notatka: "{note}"
        
        KONTEKST (Co robił wcześniej dzisiaj):
        {today_history}
        
        STATYSTYKI:
        Passa (Combo): {streak_count} (Typ: {streak_type})
        Całkowite punkty: {total_score}
        {stone_text}
        
        TWOJA ROLA (Postępuj zgodnie z tym opisem):
        {personality}
        
        Napisz krótki komentarz (max 2-3 zdania).
        """
        
        response = model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_prompt]}
        ])
        return response.text
    except Exception as e:
        return f"Jeż milczy. (BŁĄD: {str(e)})"

# --- FUNKCJA DO KALENDARZA ---
def create_cal_link(hour, title):
    tomorrow = datetime.now().date() + timedelta(days=1)
    date_str = tomorrow.strftime("%Y%m%d")
    start_time = f"{hour:02d}0000" 
    end_time = f"{hour:02d}1500"
    base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    text = f"&text={title.replace(' ', '+')}"
    dates = f"&dates={date_str}T{start_time}/{date_str}T{end_time}"
    details = "&details=Wejdź+do+Dziennika+Iglastego+i+zaznacz+status!+🦔"
    recur = "&recur=RRULE:FREQ=DAILY" 
    return base_url + text + dates + details + recur

# --- UI APLIKACJI ---

def main():
    init_session_state()
    
    # --- ANIMACJA PRZEJŚCIA (Wklej to tutaj) ---
    if "show_vault_animation" in st.session_state and st.session_state.show_vault_animation:
        play_level_up_animation(1) 
        st.session_state.show_vault_animation = False
    # -------------------------------------------
    
    # Pobieranie danych z Google Sheets
    df = get_data_from_sheets()
    current_score = get_total_score(df)
    current_hp = calculate_hp(df)
    streak_count, streak_type = calculate_current_streak(df)
    current_hp = calculate_hp(df)
    
    cycle, owned_stones, cycle_progress = calculate_game_state(current_score)
    level_img, level_desc = get_smart_image_filename(cycle, owned_stones, cycle_progress)
    daily_quote = get_daily_quote()

    # ==========================================
# 🏁 PROTOKÓŁ KOŃCA GRY: NIESKOŃCZONOŚĆ 🏁
# ==========================================
# Sprawdzamy, czy Paweł zdobył wszystkie 6 kamieni.
# Jeśli tak, przerywamy normalne działanie aplikacji i wyświetlamy ekran zwycięstwa.

    if owned_stones >= 6:
        # 1. Muzyka Finałowa (Epicki motyw)
        if os.path.exists("endgame_theme.mp3"):
            # Autoplay + Loop, żeby grało w kółko podczas napawania się wygraną
            st.audio("endgame_theme.mp3", autoplay=True, loop=True)
        
        # 2. Efekty Specjalne (Na bogato!)
        st.balloons()
        time.sleep(1)
        st.snow() # Konfetti i śnieg na raz, bo stać nas!
    
        # 3. Epicki Tytuł
        st.markdown("""
            <h1 style='text-align: center; color: gold; font-size: 60px; text-shadow: 2px 2px 4px #000000;'>
                GRATULACJE!<br>WSZECHŚWIAT JEST TWOJEJ DŁONI!
            </h1>
        """, unsafe_allow_html=True)
    
        # 4. GŁÓWNA GRAFIKA (Jeż + Ekipa)
        victory_img = "hedgehog_victory_team.png"
        if os.path.exists(victory_img):
            st.image(
                victory_img,
                caption="„Ja... jestem... Jeżem.” – Paweł, Władca Nieskończoności.",
                use_container_width=True # Rozciąga na pełną szerokość kontenera
            )
        else:
            st.warning("⚠️ Brakuje pliku: hedgehog_victory_team.png. Ale i tak wygrałeś!")
    
        # 5. Podsumowanie
        st.success("""
            Dokonałeś niemożliwego. Zebrałeś wszystkie 6 Kamieni Nieskończoności.
            Rocket jest w szoku, Drax myśli, że jesteś bogiem, a Deadpool...
            cóż, Deadpool próbuje ukraść Rękawicę.
        """)
        
        st.markdown("---")
        st.markdown("### Co teraz, Władco?")
    
    # 6. Przycisk Resetu (Nowa Gra / Prestige Mode)
        # Poprawiona nazwa: PSTRYKNIJ
        if st.button("🔄 PSTRYKNIJ PALCAMI (Zresetuj Wszechświat i Zacznij Od Nowa)", type="primary"):
            
            # A. Dźwięk Pstryknięcia (The Snap)
            if os.path.exists(SNAP_SOUND_FILE):
                st.audio(SNAP_SOUND_FILE, format="audio/mp3", autoplay=True)
            
            # B. Komunikat
            st.toast("🫰 Pstryk! Równowaga przywrócona...")
            
            # C. Czyścimy pamięć podręczną sesji
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # D. Czekamy chwilę, żeby dźwięk wybrzmiał (3 sekundy)
            time.sleep(3.0)
            st.rerun()
    
        # 🛑 KLUCZOWE: Zatrzymujemy resztę aplikacji! 🛑
        # Dzięki temu nie wyświetli się reszta gry (przyciski, sidebar itp.)
        
        st.stop()
    
    # ==========================================
    # KONIEC PROTOKOŁU KOŃCA GRY
    # (Dalej leci normalny kod aplikacji...)
    # ==========================================
    
        with st.sidebar:
            if cycle == 0:
                st.header("📂 Status Agenta") 
            else:
                st.header("💎 Skarbiec Nieskończoności")
    
            st.metric(label="Moc całkowita (EXP)", value=current_score, delta=st.session_state.last_points_change)
            # --- NOWE: Pasek Życia w Sidebarze ---
            hp_color = "red" if current_hp < 30 else "green"
            st.write(f"❤️ **Stan Zdrowia:** {current_hp}/100")
            st.progress(current_hp / 100, text=None)
            if current_hp == 0:
                st.error("STAN KRYTYCZNY! WYMAGANA HOSPITALIZACJA!")
            
            if streak_count >= 3:
                st.write("---")
                if streak_type == 'positive':
                    if streak_count >= 5:
                        st.success(f"⚡ **BÓG PIORUNÓW!** (Combo: {streak_count})")
                    else:
                        st.info(f"🔥 **W GAZIE!** (Combo: {streak_count})")
                elif streak_type == 'negative':
                    if streak_count >= 5:
                        st.error(f"💀 **ZAGROŻENIE!** (Combo: {streak_count})")
                    else:
                        st.warning(f"🌧️ **DNI DESZCZOWE** (Combo: {streak_count})")
            
            st.write("---")
            
            if cycle == 0:
                st.info("Status: **SZKOLENIE PODSTAWOWE**")
                st.caption("Zbierz 60 pkt, aby odblokować misję.")
            else:
                st.caption("Rękawica Nieskończoności:")
                stones_display = ""
                for i in range(6):
                    if i < owned_stones:
                        stones_display += INFINITY_STONES_ICONS[i] + " "
                    elif i == owned_stones:
                        stones_display += "🔒 "
                    else:
                        stones_display += "⚪ "
                st.title(stones_display)
                if owned_stones < 6:
                    target_name = INFINITY_STONES_NAMES[owned_stones]
                    st.info(f"Obecny Cel:\n**Kamień {target_name}**")
                else:
                    st.success("JESTEŚ NIEPOKONANY!")
    
            st.markdown("---")
            if not DEFAULT_API_KEY:
                 st.error("Błąd konfiguracji Secrets! Sprawdź klucze.")
    
    # 2. 🏆 GABLOTA TROFEÓW 2.0 (SKALOWANIE DO 15)
        with st.expander("🏆 Gablota Trofeów"):
            
            # --- SEKCJA 1: PROLOG ---
            st.markdown("### 🌍 Prolog")
            prolog_achievements = []
            if current_score >= 15: prolog_achievements.append("🚶 Obieżyświat (Lv 1)")
            if current_score >= 30: prolog_achievements.append("🏃 Poszukiwacz (Lv 2)")
            if current_score >= 45: prolog_achievements.append("⚔️ Wojownik (Lv 3)")
            if current_score >= 60: prolog_achievements.append("🦸‍♂️ BOHATER (Prolog Ukończony)")
            
            if not prolog_achievements:
                st.caption("Jeszcze nic. Ruszaj w drogę!")
            else:
                for ach in prolog_achievements:
                    st.success(ach)
    
            # --- SEKCJA 2: SKARBIEC ---
            st.markdown("---")
            st.markdown("### 💎 Skarbiec Nieskończoności")
            
            vault_achievements = []
            if owned_stones >= 1: vault_achievements.append("🟦 Władca Przestrzeni (Kamień 1)")
            if owned_stones >= 2: vault_achievements.append("🟥 Zaklinacz Rzeczywistości (Kamień 2)")
            if owned_stones >= 3: vault_achievements.append("🟪 Potęga Absolutna (Kamień 3)")
            if owned_stones >= 4: vault_achievements.append("🟨 Geniusz Umysłu (Kamień 4)")
            if owned_stones >= 5: vault_achievements.append("🟧 Handlarz Dusz (Kamień 5)")
            if owned_stones >= 6: vault_achievements.append("🟩 PAN CZASU (Wszystkie Kamienie!)")
            
            if not vault_achievements:
                st.caption("Skarbiec jest pusty. Zdobądź pierwszy kamień!")
            else:
                for ach in vault_achievements:
                    st.info(ach)
    
            # --- SEKCJA 3: TRYB IMPREZA (NOWA SKALA MAX 15) ---
            st.markdown("---")
            st.markdown("### 🍺 Tryb Impreza")
            
            try:
                party_df = df[df['Tryb'] == True]
                party_count = len(party_df)
                party_fails = len(party_df[party_df['Punkty'] < 0])
            except KeyError:
                party_count = 0
                party_fails = 0
            
            # A. POZYTYWNE (ILOŚĆ UŻYĆ) - Skala 3-15
            party_badges = []
            if party_count >= 3: party_badges.append("🥂 Rozgrzewka (3 imprezy)")
            if party_count >= 6: party_badges.append("🕺 Król Parkietu (6 imprez)")
            if party_count >= 9: party_badges.append("🔥 Legenda Afterparty (9 imprez)")
            if party_count >= 12: party_badges.append("👑 Celebryta (12 imprez)")
            if party_count >= 15: party_badges.append("⚡ BÓG DIONIZOS (15 imprez)")
    
            if party_badges:
                for badge in party_badges:
                    st.warning(badge)
            else:
                st.caption(f"Licznik imprez: {party_count}/3 (Wbijaj pierwszy level!)")
    
            # B. NEGATYWNE (WPADKI) - Skala 1-15
            if party_fails > 0:
                st.markdown("**☠️ Ale Urwał... (Wpadki)**")
                fail_badges = []
                
                if party_fails >= 1: fail_badges.append("🤢 O jeden shot za dużo")
                if party_fails >= 5: fail_badges.append("🚑 Stały Klient SOR-u")
                if party_fails >= 10: fail_badges.append("🧟 Wrak Człowieka")
                if party_fails >= 15: fail_badges.append("💀 Wątroba z Kartonu")
                
                for fail in fail_badges:
                    st.error(fail)
            
            st.write("---")
            st.header("🔔 Przypomnienia")
            st.caption("Kliknij, aby dodać do kalendarza:")
            link_8 = create_cal_link(8, "🦔 Iglasty: Pobudka (8:00)")
            link_14 = create_cal_link(14, "🦔 Iglasty: Checkpoint (14:00)")
            link_20 = create_cal_link(20, "🦔 Iglasty: Raport (20:00)")
            st.markdown(f'''
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <a href="{link_8}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 8px; border: 1px solid #4CAF50; border-radius: 5px; background-color: #1E1E1E; color: white; cursor: pointer;">☀️ Rano (8:00)</button></a>
                <a href="{link_14}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 8px; border: 1px solid #FF9800; border-radius: 5px; background-color: #1E1E1E; color: white; cursor: pointer;">☀️ Południe (14:00)</button></a>
                <a href="{link_20}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 8px; border: 1px solid #2196F3; border-radius: 5px; background-color: #1E1E1E; color: white; cursor: pointer;">🌙 Wieczór (20:00)</button></a>
            </div>
            ''', unsafe_allow_html=True)
    
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; margin-bottom: 20px; background-color: #1E1E1E; border-radius: 10px; border: 1px solid #333;">
            <span style="font-size: 0.9em; color: #FF4B4B; font-weight: bold;">🎬 CYTAT DNIA:</span><br>
            <span style="font-size: 1.1em; font-style: italic; color: #E0E0E0;">{daily_quote}</span>
        </div>
        """, unsafe_allow_html=True)
    
        st.title("🦔 Dziennik Iglasty")
        st.caption("System operacyjny życia po trzydziestce.")
    
        st.markdown("---")
    # ====================================================================
    # 🖥️ INTERFEJS GŁÓWNY: ZAKŁADKI (UKRYTY SKLEP)
    # ====================================================================
    
    # 1. Definiujemy zakładki DYNAMICZNIE (Sklep ukryty w Prologu)
    if current_score >= 60:
        # Wersja pełna (3 zakładki)
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Misja Dnia", "📊 Statystyki", "🛒 Sklep", "⚙️ Ustawienia"])
    else:
        # Wersja demo (2 zakładki - Sklep jest niewidzialny)
        tab1, tab2, tab4 = st.tabs(["🚀 Misja Dnia", "📊 Statystyki", "⚙️ Ustawienia"])
        tab3 = None # Zmienna pusta, żeby kod się nie wywalił
    
    # --- ZAKŁADKA 1: MISJA DNIA ---
    with tab1:
        st.header("🎬 Dziennik Iglasty")

        # --- 📜 CYTAT DNIA (TERAZ TUTAJ - POD NAGŁÓWKIEM) ---
        st.markdown(f"""
        <div style='text-align: center; color: #808080; font-style: italic; font-size: 0.9em; margin-bottom: 15px; padding: 10px; background-color: #262730; border-radius: 5px;'>
            ❝ {daily_quote} ❞
        </div>
        """, unsafe_allow_html=True)
        
        # A. ETAP SKARBCA (60+ PKT)
        if current_score >= 60:
            progress_in_stone = cycle_progress
            
            if progress_in_stone < 20:
                treasury_state = "Stan: PRZYGOTOWANIE 🧘"
            elif progress_in_stone < 40:
                treasury_state = "Stan: WALKA TRWA ⚔️"
            else:
                treasury_state = "Stan: FATALITY 🩸"
                
            st.subheader(treasury_state)
            
            if os.path.exists(level_img):
                st.image(level_img, caption=f"Walka o Kamień: {owned_stones + 1}/6")
            else:
                st.info(f"Walka o Kamień numer {owned_stones + 1}")
                
            boss_hp_percent = 1.0 - (progress_in_stone / 60.0)
            boss_hp_percent = max(0.0, min(1.0, boss_hp_percent))
            st.progress(boss_hp_percent, text=f"HP BOSSA: {int(boss_hp_percent * 100)}%")
    
        # B. ETAP PROLOGU (0-59 PKT)
        else:
            prolog_stage_index = int(current_score // 15)
            prolog_stage_index = min(prolog_stage_index, 3)
            
            prolog_images = ["level_1.png", "level_2.png", "level_3.png", "level_4.png"]
            prolog_states = ["Stan: OBIEŻYŚWIAT 🌍", "Stan: NADZIEJA ✨", "Stan: WOJOWNIK ⚔️", "Stan: BOHATER 🦸"]
            
            st.subheader(prolog_states[prolog_stage_index])
            
            current_prolog_img = prolog_images[prolog_stage_index]
            if os.path.exists(current_prolog_img):
                st.image(current_prolog_img)
            else:
                st.warning(f"Brak pliku: {current_prolog_img}")
                
            explore_percent = current_score / 60.0
            explore_percent = max(0.0, min(1.0, explore_percent))
            st.progress(explore_percent, text=f"Eksploracja Świata: {int(explore_percent * 100)}%")
    
# --- ZAKŁADKA 2: STATYSTYKI ---
    with tab2:
        st.header("📊 Raport Agenta")
        
        # UKRYWANIE KAMIENI W PROLOGU (Żeby nie psuć niespodzianki)
        if current_score < 60:
            # Wersja dla Stażysty (Tylko 2 kolumny)
            c1, c2 = st.columns(2)
            c1.metric("Całkowity EXP", f"{current_score}")
            c2.metric("Seria Dni", f"{streak_count} 🔥")
        else:
            # Wersja dla Agenta (3 kolumny - dochodzą Kamienie)
            c1, c2, c3 = st.columns(3)
            c1.metric("Całkowity EXP", f"{current_score}")
            c2.metric("Kamienie", f"{owned_stones}/6")
            c3.metric("Seria Dni", f"{streak_count} 🔥")
        
        st.markdown("---")
        
        if not df.empty:
            st.subheader("📈 Historia Aktywności")
            try:
                chart_data = df[['Data', 'Punkty']].copy()
                chart_data = chart_data.groupby('Data')['Punkty'].sum().reset_index()
                st.line_chart(chart_data, x='Data', y='Punkty')
            except:
                st.caption("Za mało danych na wykres.")
        
# --- ZAKŁADKA 3: SKLEP (Tylko jeśli istnieje!) ---
        if tab3 is not None:
            with tab3:
                st.header("🛒 Czarny Rynek Artefaktów")
                
                # 1. Portfel
                wallet = calculate_currency(df, current_score, owned_stones)
                st.metric(label="Dostępne Środki", value=f"{wallet} 🪙", delta="Kredyty Galaktyczne")
                st.markdown("---")
                
                # 2. LOGIKA ROTACJI
                current_month = datetime.now().month
                shop_rotation_index = ((current_month + 10) // 2) % 3
                current_offer = SHOP_INVENTORY.get(shop_rotation_index, [])
                rotation_names = ["Strażnicy & Najemnicy", "Avengers Assemble", "Magia & Kosmos"]
                
                st.info(f"📦 Obecna dostawa: **{rotation_names[shop_rotation_index]}**")
                st.caption("Oferta zmienia się co 2 miesiące.")
        
                # 3. Lista Artefaktów (Z ZABEZPIECZENIAMI)
                for item in current_offer:
                    c1, c2, c3 = st.columns([1, 3, 2])
                    with c1:
                        st.markdown(f"<div style='font-size: 50px; text-align: center;'>{item['icon']}</div>", unsafe_allow_html=True)
                    with c2:
                        st.subheader(item['name'])
                        st.caption(item['desc'])
                        st.markdown(f"**Bohater:** {item['hero']}")
                    with c3:
                        price = item['cost']
                        
                        # --- ZABEZPIECZENIE NR 2: BLOKADA UNIKATÓW ---
                        # Sprawdzamy, czy w historii notatek jest już zakup tego przedmiotu
                        already_owned = False
                        if not df.empty and 'Notatka' in df.columns:
                            # Szukamy dokładnego stringa identyfikującego zakup
                            # regex=False jest ważne, bo nazwy mogą mieć znaki specjalne
                            search_str = f"SHOP_BUY | {item['name']}"
                            already_owned = df['Notatka'].astype(str).str.contains(search_str, regex=False).any()

                        if already_owned:
                            st.button(f"✅ Już posiadasz", key=f"btn_owned_{item['name']}", disabled=True)
                        else:
                            # Przycisk zakupu (aktywny)
                            if st.button(f"Kup ({price} 🪙)", key=f"btn_{item['name']}"):
                                
                                # --- ZABEZPIECZENIE NR 3: LAG CLICK / RACE CONDITION ---
                                with st.spinner("Weryfikacja transakcji..."):
                                    # 1. Wymuszamy wyczyszczenie cache, żeby pobrać najnowsze dane z chmury
                                    get_data_from_sheets.clear()
                                    
                                    # 2. Pobieramy świeży stan
                                    fresh_df = get_data_from_sheets()
                                    fresh_wallet = calculate_currency(fresh_df, current_score, owned_stones)
                                    
                                    # 3. Sprawdzamy saldo OSTATNI RAZ
                                    if fresh_wallet < price:
                                        st.error("❌ Transakcja odrzucona! Stan konta się zmienił (za mało środków).")
                                    else:
                                        # Jeśli wszystko gra -> Kupujemy
                                        note_content = f"SHOP_BUY | {item['name']} | -{price}"
                                        save_to_sheets("ZAKUP", 0, "Sklep", False, note_content)
                                        
                                        st.balloons()
                                        st.success(f"✅ Kupiłeś: {item['name']}")
                                        st.info(item['reaction']) 
                                        
                                        if os.path.exists("chaos_event.mp3"):
                                            st.audio("chaos_event.mp3", autoplay=True)
                                            
                                        time.sleep(4)
                                        st.rerun()
                                        
                    st.markdown("---")

    # --- ZAKŁADKA 4: USTAWIENIA (PRZYPOMNIENIA) ---
        if tab4 is not None:
            with tab4:
                st.header("⚙️ Centrum Konfiguracji")
                st.write("Dostosuj parametry swojej misji.")
                st.markdown("---")
                
                st.subheader("📅 Przypomnienia")
                st.info("Regularność to klucz do sukcesu Agenta. Ustaw przypomnienie w kalendarzu, aby nie stracić passy (Streak)!")
                
                # Konfiguracja linku do Kalendarza Google
                # To tworzy gotowe wydarzenie z linkiem do Twojej apki
                base_calendar_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
                event_title = "🦔 Dziennik Iglasty - Raport"
                event_details = "Czas uzupełnić dziennik i sprawdzić postępy Agenta! 👉 https://pawel-lvl30.streamlit.app"
                
                # Możemy dodać parametr recurrence (powtarzanie), np. codziennie
                # RRULE:FREQ=DAILY oznacza powtarzanie codzienne
                calendar_url = f"{base_calendar_url}&text={event_title}&details={event_details}&recur=RRULE:FREQ=DAILY"
                
                col_sets_1, col_sets_2 = st.columns([1, 2])
                with col_sets_1:
                    st.markdown("### 🔔")
                with col_sets_2:
                    st.write("**Codzienny Raport**")
                    st.caption("Kliknij, aby dodać stałe przypomnienie do swojego Kalendarza Google.")
                    
                    # Przycisk linkujący
                    st.link_button("📅 Dodaj do Kalendarza", calendar_url)
                
                st.markdown("---")
                st.caption("W przyszłości znajdziesz tu więcej opcji, np. resetowanie konta czy zmianę motywu.")
        
    st.markdown("---")
    # (Tutaj zaczyna się Twój stary kod: col_note, col_toggle itd...)
    col_note, col_toggle = st.columns([3, 1])
    with col_note:
        user_note = st.text_input("📝 Co się stało?", placeholder="Logi systemowe...")
    with col_toggle:
        st.write("")
        st.write("")
        # Parametr key="party_mode" łączy przełącznik z pamięcią
        st.toggle("Tryb Impreza 🔥", key="party_mode")
    
    st.write("")
    selected = None  # Domyślnie brak wyboru
    
    # --- 💀 LOGIKA ŚMIERCI (Nowy kod) ---
    if current_hp <= 0:
        # Wyświetlamy komunikat o szpitalu
        st.error("💀 JESTEŚ W SZPITALU (0 HP)!")
        st.info("Nie możesz podejmować akcji, dopóki nie odzyskasz sił.")
        st.warning("👉 Idź do Sklepu i kup 'Apteczkę S.H.I.E.L.D.', aby wrócić do gry.")
        
        # Opcjonalny obrazek szpitala (jeśli masz plik hospital.jpg, jak nie - olej)
        if os.path.exists("hospital.jpg"):
            st.image("hospital.jpg", caption="Odpoczywaj, bohaterze...")
            
        # Tutaj NIE RYSUJEMY przycisków, więc Paweł nie może nic kliknąć.
    
    else:
        # --- ❤️ JESTEŚ ŻYWY (Twój stary kod, ale wcięty) ---
        cols = st.columns(5)
        
        # --- LOGIKA PUNKTACJI (STANDARD vs IMPREZA) ---
        if st.session_state.party_mode:
            # TRYB IMPREZA: Rosyjska Ruletka (Wysokie ryzyko!)
            score_iglica = 5
            score_igla = 2
            score_iglik = 0
            score_iglute = -6
            score_iglisko = -12
        else:
            # TRYB STANDARD: Zbalansowany rozwój
            score_iglica = 3
            score_igla = 1
            score_iglik = 0
            score_iglute = -2
            score_iglisko = -4
        
        # Definicja przycisków
        buttons = [
            (f"🗻 IGLICA", "IGLICA", score_iglica, cols[0]),
            (f"💎 IGŁA", "IGŁA", score_igla, cols[1]),
            (f"🌿 IGLIK", "IGLIK", score_iglik, cols[2]),
            (f"🍂 IGLUTEK", "IGLUTEK", score_iglute, cols[3]),
            (f"💀 IGLISKO", "IGLISKO", score_iglisko, cols[4])
        ]
        
        # Rysowanie przycisków (pętla)
        for label, status, points, col in buttons:
            if col.button(f"{label}\n({points:+})", use_container_width=True):
                selected = (status, points)
    
    if selected:
        status, points = selected
    
        # ============================================================
        # 👮 ANTI-CWANIAK SYSTEM: BLOKADA CIĄGÓW IMPREZOWYCH (PN-PT) 👮
        # ============================================================
        penalty_applied = False # Flaga, czy wlepiono mandat
        
        # Sprawdzamy tylko, jeśli włączony jest TRYB IMPREZA
        if st.session_state.party_mode:
            today = datetime.now()
            
            # Sprawdzamy czy to dzień roboczy (0=Poniedziałek, 4=Piątek)
            # Weekendy (5, 6) są święte - można imprezować.
            if today.weekday() < 5: 
                yesterday = today - timedelta(days=1)
                yesterday_str = yesterday.strftime("%Y-%m-%d")
                today_str = today.strftime("%Y-%m-%d")
                
                # 1. Czy wczoraj była impreza? (Szukamy w historii)
                yesterday_party = False
                if not df.empty and 'Tryb' in df.columns:
                    # Sprawdzamy czy jest jakikolwiek wpis z wczoraj z Trybem "ON"
                    yesterday_party = not df[(df['Data'] == yesterday_str) & (df['Tryb'] == "ON")].empty
                
                if yesterday_party:
                    # OHO! Mamy ciąg w tygodniu (Wczoraj + Dzisiaj)
                    
                    # 2. Sprawdzamy ile razy DZISIAJ już imprezował (zanim kliknął teraz)
                    today_party_count = 0
                    if not df.empty and 'Tryb' in df.columns:
                         today_party_count = len(df[(df['Data'] == today_str) & (df['Tryb'] == "ON")])
                    
                    if today_party_count == 0:
                        # SCENARIUSZ A: PIERWSZE OSTRZEŻENIE
                        st.toast("🤨 Halo? Wczoraj też była impreza!", icon="👮")
                        time.sleep(1.5)
                        st.warning("⚠️ SYSTEM BEZPIECZEŃSTWA: Wykryto ciąg imprezowy w tygodniu roboczym. To jest OSTRZEŻENIE. Kolejna próba dzisiaj zakończy się MANDATEM (-100 kredytów).")
                        # Dodajemy info do notatki, żeby został ślad w historii
                        user_note += " [OSTRZEŻENIE: CIĄG IMPREZOWY]"
                        
                    else:
                        # SCENARIUSZ B: RECYDYWA (MANDAT)
                        penalty_applied = True
                        
                        # 1. Zabieramy 100 kredytów (Symulujemy zakup w sklepie o nazwie MANDAT)
                        # Nadpisujemy notatkę tak, żeby funkcja calculate_currency to wyłapała
                        user_note = "SHOP_BUY | MANDAT ZA IMPREZOWANIE | -100"
                        
                        # 2. Zerujemy punkty EXP za tę akcję (lub dajemy minusowe)
                        points = -10 # Dodatkowa kara w EXP
                        status = "MANDAT 👮"
                        
                        # 3. Efekty wizualne i dźwiękowe
                        if os.path.exists("error_sound.mp3"): # Jeśli masz jakiś dźwięk błędu/syreny
                            st.audio("error_sound.mp3", autoplay=True)
                        
                        st.error("🚨 OSTRZEGAŁEM! ZOSTAŁEŚ UKARANY.")
                        st.toast("💸 -100 Kredytów. Nie cwaniakuj.", icon="💸")
                        time.sleep(2)
        
        # --- 🛡️ ANTI-CHEAT SYSTEM (BLOKADA 3 KLIKNIĘĆ) 🛡️ ---
        # 1. Pobieramy dzisiejszą datę jako string (format taki jak w Google Sheets, np. YYYY-MM-DD)
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # 2. Liczymy wpisy z dzisiaj
        # Zakładam, że w df kolumna z datą nazywa się "Data". Jeśli masz "Date", zmień to tutaj!
        try:
            todays_entries_count = len(df[df['Data'] == today_str])
        except KeyError:
            # Zabezpieczenie jakby kolumna nazywała się inaczej, np. ma spację
            todays_entries_count = 0 
            st.error("Błąd systemu: Nie widzę kolumny 'Data'. Ale gramy dalej.")
    
        # 3. Sprawdzamy limit (Max 3 dziennie)
        if todays_entries_count >= 3:
            # Lista złośliwych komentarzy
            anti_cheat_msgs = [
                "🛑 HEJ! Limit to 3 razy dziennie! Nie cwaniakuj.",
                "😤 Chcesz przejść grę w tydzień? Zapomnij. Wróć jutro.",
                "🐌 Wolniej, kowboju! Życie to maraton, nie sprint.",
                "🚫 ERROR 404: Twoja cierpliwość nie znaleziona.",
                "🤡 Myślisz, że System nie widzi? 3 akcje max!",
                "💸 Za to kliknięcie pobrałbym opłatę, ale nie mam terminala.",
                "🔒 Skarbiec jest zamknięty do 8:00 rano. Idź spać."
            ]
            
            # Losujemy i wyświetlamy "nagrodę"
            punishment = random.choice(anti_cheat_msgs)
            
            st.toast("🚨 WYKRYTO PRÓBĘ OSZUSTWA!")
            time.sleep(0.5)
            st.error(punishment)
            
            # Odtwarzamy dźwięk błędu (opcjonalnie, jeśli chcesz wkurzyć gracza)
            # st.audio("error_sound.mp3") 
            
            time.sleep(2.5)
            st.rerun() # Odświeżamy stronę, żeby "odkliknąć" przycisk
        # ----------------------------------------------------
    # --- 🎵 AUDIO & VISUAL FEEDBACK (WERSJA STREAK 3.0) 🎵 ---
        delay_time = 2.5  # Domyślny, krótki czas (tylko tekst)
    
        # 1. PUNKTY DODATNIE (IGLICA / IGŁA)
        if points > 0:
            
            if st.session_state.party_mode:
                # --- SCENARIUSZ: IMPREZA (Zawsze tylko tekst) ---
                rocket_respect = [
                    "🦝 ROCKET: Ty chory draniu... udało ci się.",
                    "🦝 ROCKET: Nie postawiłbym na ciebie złamanego kredytu.",
                    "🦝 ROCKET: Jesteś świrem. Szanuję to.",
                    "🦝 ROCKET: Wygrałeś, ale wyglądasz przy tym idiotycznie."
                ]
                st.success(random.choice(rocket_respect))
            
            else:
                # --- SCENARIUSZ: STANDARD (Iglica vs Igła) ---
                
                # Sprawdzamy, czy to IGLICA i czy jest STREAK (min. 2 wcześniejsze + ten obecny = 3)
                is_streak_event = (status == "IGLICA" and streak_count >= 2 and streak_type == 'positive')
                
                if is_streak_event:
                    # NAGRODA ZA STREAK 3+ (Muzyka + Show)
                    iglica_options = [
                        ("starlord.gif", "gotg_win.mp3", "🕺 DANCE OFF! Seria utrzymana! Star-Lord wymiata!"),
                        ("deadpool_dance.gif", "deadpool_music.mp3", "💃 COMBO BREAKER! Deadpool przejmuje show!")
                    ]
                    
                    chosen_gif, chosen_audio, chosen_caption = random.choice(iglica_options)
                    
                    if os.path.exists(chosen_audio) and os.path.exists(chosen_gif):
                        st.toast(f"🔥 TO JUŻ {streak_count + 1} DZIEŃ SERII! IMPREZA!", icon="🎉")
                        st.audio(chosen_audio, autoplay=True)
                        st.markdown("---")
                        st.image(chosen_gif, caption=chosen_caption, use_container_width=True)
                        delay_time = 11.0 # Wydłużamy czas na show
                    else:
                        st.success(f"🔥 NIESAMOWITA SERIA! To już {streak_count + 1} raz z rzędu!")
                
                else:
                    # ZWYKŁE KLIKNIĘCIE (Bez muzyki, krótki czas)
                    if status == "IGLICA":
                        st.success("✅ Solidna robota. Buduj serię dalej.")
                    else:
                        st.success("💎 Mały krok dla jeża, wielki dla ludzkości.")
    
        # 2. PUNKTY UJEMNE (IGLISKO / IGLUTEK)
        elif points < 0:
            
            if st.session_state.party_mode:
                # --- SCENARIUSZ: IMPREZA (Iglisko) ---
                
                # Sprawdzamy czy to IGLISKO i czy to już 3. wpadka z rzędu
                is_fail_streak = (status == "IGLISKO" and streak_count >= 2 and streak_type == 'negative')
                
                if is_fail_streak:
                    # KARA ZA SERIĘ WPADEK (Thor)
                    if os.path.exists("thor_drunk.mp3") and os.path.exists("thor_drunk.gif"):
                        st.toast("🍺 Ouch... To już seria porażek.", icon="🥴")
                        st.audio("thor_drunk.mp3", autoplay=True)
                        st.markdown("---")
                        st.image("thor_drunk.gif", caption="🍺 Spokojnie, wciąż jesteś godzien... chyba.", use_container_width=True)
                        delay_time = 11.0
                    else:
                        st.error("🍺 Thor by cię pocieszył, ale śpi. Ogarnij się.")
                else:
                    # Zwykła wpadka (bez muzyki)
                    st.error("💀 Ale urwał! Uważaj na wątrobę.")
            
            else:
                # --- SCENARIUSZ: STANDARD (Rocket cisnie) ---
                rocket_insults = [
                    "🦝 ROCKET: Gratulacje, geniuszu. Obniżyłeś IQ całego statku.",
                    "🦝 ROCKET: Groot by to lepiej wybrał. A on jest drzewem.",
                    "🦝 ROCKET: Nie dotykaj niczego więcej, błagam.",
                    "🦝 ROCKET: Amatorszczyzna. Nawet Drax by się uśmiał."
                ]
                st.error(random.choice(rocket_insults))
    
    # --- 🎰 KOŁO FORTUNY (GLOBALNY HAZARD) 🎰 ---
        # Działa na każdą opcję. Szansa 5%.
        # Losuje modyfikator: -2 (Pech), 0 (Bez zmian), +2 (Fart)
        chaos_change = 0
        
        if random.random() < 0.05: # 5% szans na uruchomienie koła
            
            # Losujemy jedną z 3 opcji
            wheel_options = [-2, 0, 2]
            chaos_change = random.choice(wheel_options)
            
            # Aktualizujemy punkty
            points += chaos_change
            
            # Wspólny efekt dźwiękowy dla "Zdarzenia Chaosu" (jeśli plik istnieje)
            # Używamy tego samego dźwięku, żeby zasygnalizować "System coś wylosował"
            if os.path.exists("chaos_event.mp3"):
                st.audio("chaos_event.mp3", autoplay=True)
                # Wydłużamy nieco czas, żeby dźwięk zdążył wybrzmieć, jeśli inne są krótkie
                if delay_time < 4.0: delay_time = 4.0
    
            # --- SCENARIUSZ 1: FART (+2) ---
            if chaos_change > 0:
                st.toast(f"🎰 KOŁO FORTUNY: FART! Bonus +{chaos_change} pkt!", icon="🍀")
                st.balloons()
    
            # --- SCENARIUSZ 2: PECH (-2) ---
            elif chaos_change < 0:
                st.toast(f"🎰 KOŁO FORTUNY: PECH! Tracisz {abs(chaos_change)} pkt!", icon="💀")
                # Tu usuwamy Deadpoola. Pech to po prostu ból wizualny (i strata pkt).
    
            # --- SCENARIUSZ 3: BEZ ZMIAN (0) ---
            else:
                st.toast("🎰 KOŁO FORTUNY: UFF... Przeszło obok. (0 zmian)", icon="😅")
    
            # Dodajemy info do notatki
            user_note += f" [KOŁO: {chaos_change:+d}]"
        # --- DALEJ LECI TWÓJ STARY KOD (EASTER EGGS I ZAPIS) ---
        code_word = user_note.strip().lower()
        # ... (reszta kodu: chimichanga, zapis do sheets itd.)
        
        # --- 🥚 EASTER EGGS (WERSJA TROLL) 🥚 ---
        code_word = user_note.strip().lower()
    
        # A. CHIMICHANGA (SPAM ATAK)
        if code_word == "chimichanga":
            # Zamiast balonów -> Seria szybkich, chaotycznych powiadomień
            st.toast("🌮 OOO TAAAAK!")
            time.sleep(0.4)
            st.toast("🌯 CHIMI-")
            time.sleep(0.4)
            st.toast("🔥 -F***ING-")
            time.sleep(0.4)
            st.toast("🥑 -CHANGA!!!")
            time.sleep(0.5)
            st.info("🤤 Właśnie wirtualnie zjadłeś 5000 kalorii. Warto było.")
    
        # A. THE THANOS SNAP (Fake Delete)
        if code_word == "thanos":
            with st.spinner("⚠️ WYKRYTO ZAGROŻENIE..."):
                time.sleep(1)
            
            # Pasek postępu kasowania
            progress_text = "Usuwanie bazy danych..."
            my_bar = st.progress(0, text=progress_text)
    
            for percent_complete in range(100):
                time.sleep(0.02) # Szybkość kasowania
                my_bar.progress(percent_complete + 1, text=f"Kasowanie wspomnień: {percent_complete}%")
            
            st.error("💀 BAZA DANYCH USUNIĘTA TRWALE.")
            time.sleep(2)
            st.toast("🫰 Pstryk... Żartowałem. Masz szczęście.")
            time.sleep(1)
            my_bar.empty() # Czyści pasek
    
        # B. SŁABE HASŁA (Wyśmiewanie)
        elif code_word in ["admin", "hasło", "1234", "password"]:
            st.toast("🔒 Serio? Takie hasło?")
            time.sleep(1.5)
            st.toast("🤦‍♂️ Mój kalkulator ma lepsze zabezpieczenia.")
            time.sleep(1.5)
            st.toast("🦔 Żenujące. Odejmuję 0 punktów tylko z litości.")
    
        # C. SELF-DESTRUCT (Deadpool style)
        elif code_word == "autodestrukcja":
            st.warning("💣 Autodestrukcja za 3...")
            time.sleep(1)
            st.warning("💣 2...")
            time.sleep(1)
            st.warning("💣 1...")
            time.sleep(1)
            st.success("💥 BUM! (Nie mieliśmy budżetu na efekty specjalne).")
        
        # --- KONIEC EASTER EGGS ---
    
        # 3. Logika zapisu (Tutaj usuwamy zduplikowany fragment, który miałeś)
        if not DEFAULT_API_KEY:
            st.error("Brak konfiguracji API!")
        else:
            with st.spinner('Synchronizacja z Chmurą...'):
                # 1. Zapamiętujemy stary stan (żeby wiedzieć, czy był awans)
                old_cycle, _, _ = calculate_game_state(current_score)
                
                # 2. Obliczamy nowe punkty
                new_total = current_score + points
                new_cycle, new_owned, _ = calculate_game_state(new_total)
                
                # 3. Generujemy komentarz Jeża (z kompletem argumentów!)
                comment = get_hedgehog_comment(
                    DEFAULT_API_KEY,
                    status,
                    points,
                    new_total,
                    new_owned,
                    user_note,
                    st.session_state.party_mode,
                    df,
                    streak_count,
                    streak_type
                )
                
                # 4. Zapisujemy do Google Sheets
                save_to_sheets(status, points, comment, st.session_state.party_mode, user_note)
                
                # 5. Aktualizujemy sesję
                st.session_state.last_points_change = points
                st.session_state.last_comment = comment
                
                # --- TU JEST KLUCZOWY MECHANIZM PRZEJŚCIA ---
                # Jeśli był cykl 0 (Prolog), a teraz jest 1 (Skarbiec) -> Ustaw flagę animacji
                if old_cycle == 0 and new_cycle == 1:
                    st.session_state.show_vault_animation = True
                
    # --- 💰 POWIADOMIENIE O KREDYTACH (TYLKO PO ODBLOKOWANIU SKLEPU) ---
        new_total_score = current_score + points 
        if new_total_score >= 60:
            earned_credits = 0
            if points >= 5: earned_credits = 10 
            elif points > 0: earned_credits = 5
            elif points < 0: earned_credits = 1
            
            if earned_credits > 0:
                time.sleep(0.5) 
                st.toast(f"💳 Zaksięgowano: +{earned_credits} kredytów!", icon="🤑")
    
        # --- FINALIZACJA ---
        time.sleep(delay_time) 
        st.rerun()
    
    if st.session_state.last_comment:
        if st.session_state.last_points_change >= 3:
             st.success(f"💬 **Jeż mówi:** {st.session_state.last_comment}")
        else:
            st.info(f"💬 **Jeż mówi:** {st.session_state.last_comment}")
    
    with st.expander("📜 Historia wpisów (z Chmury)"):
        if not df.empty:
            # Sortujemy tak, żeby najnowsze były na górze
            st.dataframe(df[['Data', 'Godzina', 'Stan', 'Punkty', 'Notatka', 'Komentarz']].sort_values(by=['Data', 'Godzina'], ascending=False), hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()












































