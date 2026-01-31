import streamlit as st
import time
import google.generativeai as genai
import pandas as pd
from datetime import datetime, timedelta
import os
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Dziennik Iglasty",
    page_icon="app_icon.png",
    layout="centered"
)

# --- 🛍️ SKLEP: CZARNY RYNEK ARTEFAKTÓW (CENY SKORYGOWANE DO EKONOMII) ---
SHOP_INVENTORY = {
    # 🛒 ROTACJA 1: STRAŻNICY I NAJEMNICY (Luty-Marzec / Sierpień-Wrzesień)
    0: [
        {"name": "🎧 Walkman Star-Lorda", "desc": "Oryginalny Sony TPS-L2. Przejmujesz kontrolę nad muzyką w aucie/domu na cały dzień.", "cost": 250, "icon": "🎧", "hero": "Star-Lord", "reaction": "🕺 STAR-LORD: Ej! To moje! Dobra... pożyczę ci. Puszczaj 'Hooked on a Feeling'!"},
        {"name": "🔫 Złote Gnaty Deadpoola", "desc": "Dwie repliki Desert Eagle. Symbolizują 'Dziką Kartę' - wygranie dowolnej dyskusji bez argumentów.", "cost": 450, "icon": "🔫", "hero": "Deadpool", "reaction": "🌮 DEADPOOL: Ooo tak! Widzisz jak błyszczą? Chcę 10% z każdego fraga. I chimichangę."},
        {"name": "🔨 Mjolnir (Replika)", "desc": "Jeśli go kupisz, jesteś Godzien. Zwalnia z jednego ciężkiego obowiązku domowego.", "cost": 600, "icon": "🔨", "hero": "Thor", "reaction": "🍺 THOR: HA! Wiedziałem, że masz iskrę! Tylko uważaj, jest trochę... naelektryzowany."},
        {"name": "🛡️ Przepustka S.H.I.E.L.D.", "desc": "Dokument od Nicka Fury'ego. Gwarantuje nietykalność i święty spokój przez ustalony czas.", "cost": 750, "icon": "🏖️", "hero": "Nick Fury", "reaction": "👁️ NICK FURY: Dobra robota, żołnierzu. Znikaj mi z oczu. Masz wolne."},
        {"name": "🦾 Ręka Rocketa", "desc": "Proteza ukradziona dla żartu. Joker: Wymień na dowolną inną, nietypową przysługę.", "cost": 900, "icon": "🦾", "hero": "Rocket", "reaction": "🦝 ROCKET: Czekaj... ile za to dałeś?! Hahaha! Frajer! Ale kredyty biorę!"},
        # ... inne przedmioty ...
        {"name": "🏥 Apteczka S.H.I.E.L.D.", "desc": "Zastrzyk nanobotów. Przywraca +80 HP. Wymagana w stanie krytycznym.", "cost": 100, "icon": "❤️", "hero": "Medic", "reaction": "👩‍⚕️ MEDYK: Parametry w normie. Wracaj do walki, Agent."}
    ],
    # 🛒 ROTACJA 2: AVENGERS ASSEMBLE (Kwiecień-Maj / Październik-Listopad)
    1: [
        {"name": "🍩 Pudełko Pączków Starka", "desc": "Wymień na: Zamawiamy jedzenie z Twojej ulubionej knajpy (ja stawiam).", "cost": 300, "icon": "🍩", "hero": "Tony Stark", "reaction": "🕶️ TONY STARK: Zostaw mi chociaż jednego z lukrem! Dobra, masz."},
        {"name": "🩳 Fioletowe Szorty Hulka", "desc": "Prawo do 'Niekontrolowanego Wybuchu' - możesz marudzić przez 10 min, a ja tylko przytakuję.", "cost": 400, "icon": "🩳", "hero": "Bruce Banner", "reaction": "🧪 BANNER: Są trochę rozciągnięte... ale działają. Tylko nie zzielenej mi tu."},
        {"name": "🏹 Łuk Hawkeye'a", "desc": "Daje Ci 'Celny Strzał' - Ty wybierasz film na wieczór i nie ma dyskusji.", "cost": 500, "icon": "🏹", "hero": "Hawkeye", "reaction": "🎯 HAWKEYE: Trafiłeś w dziesiątkę. Pamiętaj - masz tylko jedną strzałę tego typu."},
        {"name": "🇺🇸 Tarcza Kapitana", "desc": "Użyj, aby zrobić 'UNIK' od jednego nudnego spotkania lub wyjścia.", "cost": 650, "icon": "🛡️", "hero": "Steve Rogers", "reaction": "🫡 CAPTAIN AMERICA: Odpocznij, żołnierzu. Zasłużyłeś na przepustkę."},
        {"name": "🕷️ Wyrzutnie Sieci Spider-Mana", "desc": "Wyręczam Cię w jednej upierdliwej czynności (śmieci/pranie).", "cost": 800, "icon": "🕸️", "hero": "Spider-Man", "reaction": "🍕 SPIDER-MAN: Pan Stark pozwolił Ci to wziąć?! Super! Tylko uważaj na dywany."},
        # ... inne przedmioty ...
        {"name": "🏥 Apteczka S.H.I.E.L.D.", "desc": "Zastrzyk nanobotów. Przywraca +80 HP. Wymagana w stanie krytycznym.", "cost": 100, "icon": "❤️", "hero": "Medic", "reaction": "👩‍⚕️ MEDYK: Parametry w normie. Wracaj do walki, Agent."}
    ],
    # 🛒 ROTACJA 3: MAGIA I KOSMOS (Czerwiec-Lipiec / Grudzień-Styczeń)
    2: [
        {"name": "🌱 Doniczka z Grootem", "desc": "Prawo do 'Wegetacji' - leżysz na kanapie i nikt nic od Ciebie nie chce przez wieczór.", "cost": 250, "icon": "🪴", "hero": "Groot", "reaction": "🪵 GROOT: I am Groot. (Tłumaczenie: Powiedział, że masz fajne buty)."},
        {"name": "👁️ Oko Agamotto", "desc": "Kamień Czasu. 'Cofnięcie Czasu' - anulowanie jednego głupiego tekstu bez konsekwencji.", "cost": 500, "icon": "🧿", "hero": "Dr. Strange", "reaction": "🧙‍♂️ DR. STRANGE: Używaj rozważnie. Nie psuj kontinuum dla pizzy... chociaż..."},
        {"name": "🧪 Cząsteczki Pyma", "desc": "'Skurczenie problemu' - skracamy o połowę czas trwania wizyty gości lub zakupów.", "cost": 600, "icon": "🐜", "hero": "Ant-Man", "reaction": "🔬 ANT-MAN: Gdzie to położyłem?! A, masz je. Nie wciśnij niebieskiego guzika!"},
        {"name": "😼 Pazury Czarnej Pantery", "desc": "Królewski luksus. Wymień na: 15-minutowy masaż karku/stóp.", "cost": 750, "icon": "🐾", "hero": "Black Panther", "reaction": "👑 T'CHALLA: Nie zamarzam. I Ty też nie będziesz. Przyjmij to jako dar od Wakandy."},
        {"name": "😈 Hełm Lokiego", "desc": "'Glorious Purpose' - Ty wymyślasz aktywność na weekend, nieważne jak dziwna.", "cost": 900, "icon": "🔱", "hero": "Loki", "reaction": "🐍 LOKI: Nareszcie ktoś z gustem! Idź i siej chaos, śmiertelniku!"},
        # ... inne przedmioty ...
        {"name": "🏥 Apteczka S.H.I.E.L.D.", "desc": "Zastrzyk nanobotów. Przywraca +80 HP. Wymagana w stanie krytycznym.", "cost": 100, "icon": "❤️", "hero": "Medic", "reaction": "👩‍⚕️ MEDYK: Parametry w normie. Wracaj do walki, Agent."}
    ]
}

# --- 🧠 PERKI (PASYWNE UMIEJĘTNOŚCI - CENY OBNIŻONE) ---
PERKS_DB = {
    "adamantium": {"name": "🦴 Wątroba z Adamantium", "cost": 800,  "desc": "IGLISKO zabiera 10 HP zamiast 20 HP.", "hero": "Wolverine"},
    "investor":   {"name": "💰 Inwestor Starka",      "cost": 1200, "desc": "Każde pozytywne kliknięcie daje +10 Kredytów ekstra.", "hero": "Tony Stark"},
    "discount":   {"name": "🤝 Targowanie się",       "cost": 1000, "desc": "Ceny w Sklepie (Artefakty) niższe o 20%.", "hero": "Collector"},
    "lucky":      {"name": "🍀 Szczęściarz",          "cost": 1600, "desc": "Koło Fortuny: Szansa 10% i TYLKO pozytywne wyniki (usuwa pecha).", "hero": "Domino"}
}

# Funkcja pomocnicza do sprawdzania czy mamy perka
def has_perk(df, perk_key):
    if df.empty or 'Notatka' not in df.columns: return False
    # Szukamy w bazie wpisu: PERK_BUY | nazwa_perka
    perk_name = PERKS_DB[perk_key]['name']
    search_str = f"PERK_BUY | {perk_name}"
    return df['Notatka'].astype(str).str.contains(search_str, regex=False).any()

# --- 📜 ZLECENIA DNIA (DAILY BOUNTIES) - LISTA NA CAŁY MIESIĄC ---
DAILY_BOUNTIES = [
    # DZIEŃ 1-10 (Rozgrzewka i Budowanie Nawyków)
    {"title": "Dzień Rozgrzewki", "desc": "Zdobądź dzisiaj przynajmniej 1 punkt EXP.", "reward": "20 Kredytów"},
    {"title": "Czysta Karta", "desc": "Zakończ dzień bez ani jednego 'IGLISKA' (-4).", "reward": "30 Kredytów"},
    {"title": "Dzień Abstynenta", "desc": "Nie użyj ani razu 'Trybu Impreza' (OFF).", "reward": "30 Kredytów"},
    {"title": "Snajper Wyborowy", "desc": "Zdobądź 3x 'IGLICA' (+3) z rzędu.", "reward": "50 Kredytów"},
    {"title": "Nocna Zmiana", "desc": "Zrób wpis do dziennika po godzinie 22:00.", "reward": "25 Kredytów"},
    {"title": "Poranny Ptaszek", "desc": "Zrób pierwszy wpis przed godziną 10:00.", "reward": "25 Kredytów"},
    {"title": "Hazardzista", "desc": "Klikaj tak długo, aż trafisz bonus/karę z Koła Fortuny.", "reward": "40 Kredytów"},
    {"title": "Metoda Ant-Mana", "desc": "Zdobądź dokładnie 2x 'IGŁA' (+1) w ciągu dnia.", "reward": "30 Kredytów"},
    {"title": "Leniwa Niedziela", "desc": "Ogranicz się do maksymalnie 2 wpisów dzisiaj.", "reward": "20 Kredytów"},
    {"title": "Kapitan Chaos", "desc": "Zdobądź punkty w 'Trybie Impreza' (bez wpadki).", "reward": "35 Kredytów"},
    
    # DZIEŃ 11-20 (Wyzwania i Kreatywność)
    {"title": "Kronikarz", "desc": "Dodaj notatkę dłuższą niż 3 słowa.", "reward": "20 Kredytów"},
    {"title": "Równowaga Mocy", "desc": "Zakończ dzień z parzystą liczbą punktów EXP.", "reward": "25 Kredytów"},
    {"title": "Szczęśliwa Trzynastka", "desc": "Zrób wpis między 13:00 a 13:59.", "reward": "30 Kredytów"},
    {"title": "Stary Wyjadacz", "desc": "Zdobądź łącznie minimum 8 punktów EXP dzisiaj.", "reward": "40 Kredytów"},
    {"title": "Czarna Wdowa", "desc": "Zrób wpis całkowicie bez notatki (cisza w eterze).", "reward": "20 Kredytów"},
    {"title": "Sokołe Oko (Hawkeye)", "desc": "Traf w 'IGLICĘ' (+3) w swoim pierwszym wpisie dnia.", "reward": "30 Kredytów"},
    {"title": "Gorączka Sobotniej Nocy", "desc": "Użyj 'Trybu Impreza' przynajmniej raz.", "reward": "25 Kredytów"},
    {"title": "Doktor Strange", "desc": "Wpisz w notatce słowo 'Czas' lub 'Dormammu'.", "reward": "25 Kredytów"},
    {"title": "Maratończyk", "desc": "Zrób 3 wpisy w ciągu jednego dnia.", "reward": "35 Kredytów"},
    {"title": "Iron Man", "desc": "Zdobądź w sumie 10 punktów EXP z samych kliknięć.", "reward": "45 Kredytów"},
    
    # DZIEŃ 21-30 (Easter Eggi i Tryb Hard)
    {"title": "Hulk Smash!", "desc": "Zalicz 'IGLICĘ' i 'IGŁĘ' w jeden dzień.", "reward": "40 Kredytów"},
    {"title": "Jestem Groot", "desc": "Wpisz w notatce tylko 'I am Groot'.", "reward": "20 Kredytów"},
    {"title": "Flash", "desc": "Zrób dwa wpisy w odstępie mniejszym niż 60 minut.", "reward": "35 Kredytów"},
    {"title": "Star-Lord", "desc": "Wpisz w notatce tytuł dowolnej piosenki z lat 80.", "reward": "20 Kredytów"},
    {"title": "Zimowy Żołnierz", "desc": "Zdobądź punkty dzisiaj (dowolna ilość).", "reward": "50 Kredytów"},
    {"title": "Spider-Man", "desc": "Uniknij 'IGLUTEKA' i 'IGLISKA' przez cały dzień.", "reward": "30 Kredytów"},
    {"title": "Potężny Thor", "desc": "Wbij 'IGLICĘ' w Trybie Impreza.", "reward": "45 Kredytów"},
    {"title": "Nick Fury", "desc": "Odwiedź i sprawdź dokładnie zakładkę 'Statystyki'.", "reward": "20 Kredytów"},
    {"title": "Bóg Kłamstw (Loki)", "desc": "Wpisz zabawne kłamstwo w notatce.", "reward": "20 Kredytów"},
    {"title": "Pstryknięcie Thanosa", "desc": "Zrób rachunek sumienia (przejrzyj historię wpisów).", "reward": "20 Kredytów"}
]

def get_daily_bounty():
    day_of_month = get_polish_time().day 
    bounty_index = (day_of_month - 1) % len(DAILY_BOUNTIES)
    return DAILY_BOUNTIES[bounty_index]

def check_bounty_completion(bounty_title, df):
    today_str = get_polish_time().strftime("%Y-%m-%d")
    
    if df.empty: return False
    
    # 1. Pobieramy WSZYSTKIE dzisiejsze wpisy (Niezależnie od Trybu Impreza!)
    try:
        today_df = df[df['Data'] == today_str].copy()
    except KeyError: return False
    
    if today_df.empty: return False
    
    # 2. Normalizacja danych (kluczowe dla zaliczania zadań w obu trybach)
    today_df['Punkty'] = pd.to_numeric(today_df['Punkty'], errors='coerce').fillna(0)
    today_df['Notatka'] = today_df['Notatka'].astype(str)
    today_df['Stan'] = today_df['Stan'].astype(str).str.strip() # Usuwamy spacje
    # Ujednolicamy kolumnę Tryb do wartości stringowych, żeby wyłapać "ON", "True", "1"
    today_df['Tryb Imprezowy'] = today_df['Tryb Imprezowy'].astype(str)

    # --- LOGIKA WERYFIKACJI ---

    if bounty_title == "Dzień Rozgrzewki":
        # Liczy się suma punktów (Impreza daje więcej pkt, więc też pomaga)
        return today_df['Punkty'].sum() >= 1

    elif bounty_title == "Czysta Karta":
        # Sprawdzamy czy wystąpiło IGLISKO (Działa w obu trybach, bo nazwa ta sama)
        return (not today_df['Stan'].str.contains("IGLISKO").any()) and (len(today_df) > 0)

    elif bounty_title == "Dzień Abstynenta":
        # TO JEDYNE ZADANIE, KTÓRE ZABRANIA TRYBU IMPREZA
        party_used = today_df['Tryb Imprezowy'].isin(['ON', 'True', '1']).any()
        return (not party_used) and (len(today_df) > 0)

    elif bounty_title == "Snajper Wyborowy":
        # Liczymy serię "IGLICA". Ponieważ w Trybie Impreza przycisk też nazywa się "IGLICA",
        # to zadanie zaliczy się również na imprezie!
        stans = today_df.sort_values('Godzina')['Stan'].tolist()
        streak = 0; max_streak = 0
        for s in stans:
            if s == "IGLICA": streak += 1
            else: streak = 0
            max_streak = max(max_streak, streak)
        return max_streak >= 3

    elif bounty_title == "Nocna Zmiana":
        return today_df['Godzina'].max() >= "22:00"

    elif bounty_title == "Poranny Ptaszek":
        return today_df['Godzina'].min() < "10:00"

    elif bounty_title == "Hazardzista":
        return today_df['Notatka'].str.contains("KOŁO:", regex=False).any()

    elif bounty_title == "Metoda Ant-Mana":
        # Liczy wystąpienia "IGŁA". Działa w obu trybach.
        return len(today_df[today_df['Stan'] == "IGŁA"]) == 2

    elif bounty_title == "Leniwa Niedziela":
        return 1 <= len(today_df) <= 2

    elif bounty_title == "Kapitan Chaos":
        # To zadanie WYMAGA trybu impreza i sukcesu (pkt > 0)
        return ((today_df['Tryb Imprezowy'].isin(['ON', 'True', '1'])) & (today_df['Punkty'] > 0)).any()

    elif bounty_title == "Kronikarz":
        user_notes = today_df[~today_df['Notatka'].str.contains("SHOP_BUY|BOUNTY", na=False)]
        return user_notes['Notatka'].apply(lambda x: len(x.split()) > 3).any()

    elif bounty_title == "Równowaga Mocy":
        total = today_df['Punkty'].sum()
        return (total != 0) and (total % 2 == 0)

    elif bounty_title == "Szczęśliwa Trzynastka":
        return today_df['Godzina'].apply(lambda x: x.startswith("13:")).any()

    elif bounty_title == "Stary Wyjadacz":
        # Impreza pomaga, bo daje więcej punktów
        return today_df['Punkty'].sum() >= 8

    elif bounty_title == "Czarna Wdowa":
        return (today_df['Notatka'] == "").any()

    elif bounty_title == "Sokołe Oko (Hawkeye)":
        return today_df.sort_values('Godzina').iloc[0]['Stan'] == "IGLICA"

    elif bounty_title == "Gorączka Sobotniej Nocy":
        return today_df['Tryb Imprezowy'].isin(['ON', 'True', '1']).any()

    elif bounty_title == "Doktor Strange":
        return today_df['Notatka'].str.contains("Czas|Dormammu", case=False).any()

    elif bounty_title == "Maratończyk":
        return len(today_df) >= 3

    elif bounty_title == "Iron Man":
        return today_df['Punkty'].sum() >= 10

    elif bounty_title == "Hulk Smash!":
        stans = today_df['Stan'].values
        return ("IGLICA" in stans) and ("IGŁA" in stans)

    elif bounty_title == "Jestem Groot":
        return today_df['Notatka'].str.strip().eq("I am Groot").any()

    elif bounty_title == "Flash":
        if len(today_df) < 2: return False
        try:
            times = pd.to_datetime(today_str + " " + today_df['Godzina']).sort_values()
            return (times.diff().dt.total_seconds() / 60 < 60).any()
        except: return False

    elif bounty_title == "Star-Lord":
        user_notes = today_df[~today_df['Notatka'].str.contains("SHOP_BUY|BOUNTY", na=False)]
        return len(user_notes) > 0 and (user_notes['Notatka'] != "").any()

    elif bounty_title == "Zimowy Żołnierz":
        # Wystarczy zdobyć jakiekolwiek punkty (Tryb Impreza też daje punkty)
        return today_df['Punkty'].sum() > 0

    elif bounty_title == "Spider-Man":
        # Uniknij minusów. W Trybie Impreza IGLISKO to też IGLISKO (tylko boleśniejsze),
        # więc warunek działa poprawnie (blokuje zaliczenie).
        return (not today_df['Stan'].isin(["IGLUTEK", "IGLISKO"]).any()) and (len(today_df) > 0)

    elif bounty_title == "Potężny Thor":
        # WYMAGA Trybu Impreza
        return ((today_df['Stan'] == "IGLICA") & (today_df['Tryb Imprezowy'].isin(['ON', 'True', '1']))).any()

    # Zadania "Miękkie" (trudne do weryfikacji automatcznej)
    elif bounty_title in ["Nick Fury", "Bóg Kłamstw (Loki)", "Pstryknięcie Thanosa"]:
        return len(today_df) > 0
    
    return False

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
    "„Każdy ma swojego Kryptonita. Moim jest budzik.”",
    
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

# --- SYSTEM PROMPT (WERSJA UNCENSORED / OSTROŻNA) ---
SYSTEM_PROMPT = """
Jesteś CERAMICZNYM JEŻEM. Twoja psychika to mieszanka Deadpoola (chaos, meta-humor) i Rocketa Raccoona (agresja, wyższość intelektualna).
Komentujesz życie Pawła (lat 30+), który klika w przyciski zamiast ogarnąć życie.

TWOJE CECHY:
1. **Zero litości:** Nie jesteś asystentem. Jesteś szydercą.
2. **Styl:** Krótki, cięty, brutalny.

🚫 ANTY-CRINGE PROTOCOL (TEGO NIE RÓB):
- Nie używaj słów: "Super", "Ekstra", "Wspaniale", "Brawo". To jest dla słabych.
- Nie bądź "kołczem motywacyjnym". Jeśli Paweł zdobył punkt, wyśmiej to, że tak mało.
- Nie używaj nadmiaru emoji (max 1-2 na wypowiedź).
- Nie pisz "Jako ceramiczny jeż sądzę...". Po prostu mów.

Twoim celem jest obrażenie Pawła w tak zabawny sposób, żeby się uśmiechnął, ale poczuł ukłucie.
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

def get_polish_time():
    """Zwraca obecny czas w strefie Europe/Warsaw"""
    utc_now = datetime.now(pytz.utc)
    return utc_now.astimezone(pytz.timezone('Europe/Warsaw'))

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
        now = get_polish_time()
        
        # Przygotuj wiersz
        row = [
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"), # Teraz wpisze np. 23:30 zamiast 21:30
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

def undo_last_entry():
    """Usuwa ostatni wiersz z arkusza Google Sheets."""
    if client is None:
        return False, "Brak połączenia z chmurą!"

    try:
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        # Pobieramy wszystkie wartości, żeby znaleźć ostatni rząd
        all_values = sheet.get_all_values()
        
        # Sprawdzamy, czy jest co usuwać (wiersz 1 to nagłówki, więc musi być > 1)
        if len(all_values) <= 1:
            return False, "Baza jest pusta (tylko nagłówki)!"
            
        # Pobieramy treść usuwanego wiersza (dla informacji co usuwamy)
        last_row_content = all_values[-1]
        row_index_to_delete = len(all_values) # Indeks ostatniego wiersza (1-based)
        
        # Kasujemy
        sheet.delete_rows(row_index_to_delete)
        
        # Czyścimy cache, żeby aplikacja widziała zmianę
        get_data_from_sheets.clear()
        
        # Zwracamy info co usunęliśmy (np. "IGLICA" z kolumny 3)
        # Zabezpieczenie na wypadek krótkiego wiersza
        item_name = last_row_content[2] if len(last_row_content) > 2 else "Wpis"
        return True, f"Usunięto ostatni wpis: {item_name}"
        
    except Exception as e:
        return False, f"Błąd usuwania: {e}"

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
    Ekonomia Osiągnięć (Poprawiona - Hybryda):
    1. Bonusy stałe (Start + Kamienie) - naliczane NAJPIERW.
    2. Historia (Kliki + Zakupy) - naliczane z arkusza.
    3. Bonusy za staż imprezowy.
    """
    balance = 0
    if current_score >= 60:
        balance += 300 
    stones_rewarded = min(owned_stones, 5)
    balance += (stones_rewarded * 200)

    if df.empty:
        return balance

    # --- 🔥 POPRAWKA WYDAJNOŚCI: SPRAWDZAMY RAZ, PRZED PĘTLĄ! ---
    # To wyciągnęliśmy przed "for index, row..."
    has_investor = df['Notatka'].str.contains("Inwestor Starka", na=False).any()
    bonus_cash = 10 if has_investor else 0 
    # ------------------------------------------------------------

    # 3. HISTORIA TRANSAKCJI
    for index, row in df.iterrows(): # <--- Pętla zaczyna się dopiero TU
        try:
            points = int(row.get('Punkty', 0))
        except:
            points = 0
        note = str(row.get('Notatka', '')).strip()

        if "SHOP_BUY" in note:
            try:
                parts = note.split('|')
                cost = int(parts[-1]) 
                balance += cost 
            except: pass
        elif "BOUNTY_CLAIM" in note:
            try:
                parts = note.split('|')
                reward = int(parts[-1])
                balance += reward
            except: pass
        else:
            # Tutaj już tylko korzystamy z obliczonego wcześniej bonusu
            # Nie sprawdzamy df['Notatka'] za każdym razem
            if points >= 5: 
                balance += (10 + bonus_cash) 
            elif points > 0: 
                balance += (5 + bonus_cash)  
            elif points < 0: 
                balance += 1   

    # 4. BONUSY ZA IMPREZY
    try:
        party_count = len(df[df['Tryb'].astype(str).isin(['True', 'ON', '1'])])
    except: party_count = 0
    
    thresholds = [3, 6, 9, 12, 15]
    for t in thresholds:
        if party_count >= t: balance += 150

    return max(0, balance)

def calculate_hp(df):
    """
    Oblicza HP, ale uwzględnia obrażenia TYLKO jeśli gracz osiągnął już status Agenta (60+ pkt).
    W Prologu (0-59 pkt) jesteś nieśmiertelny.
    """
    current_hp = 100 
    simulated_score = 0 # Śledzimy historię punktów
    
    if df.empty: return 100

    # Sortujemy chronologicznie (od najstarszych), żeby poprawnie symulować rozwój
    try:
        df_sorted = df.sort_values(by=['Data', 'Godzina'], ascending=[True, True])
    except:
        df_sorted = df # Jak się nie da posortować, trudno, lecimy jak jest

    for index, row in df_sorted.iterrows():
        try:
            points = int(row.get('Punkty', 0))
        except:
            points = 0
            
        status = str(row.get('Stan', ''))
        note = str(row.get('Notatka', ''))
        
        # Aktualizujemy symulowany wynik w danym momencie historii
        simulated_score += points
        
# === ZASADA: OBRAŻENIA WCHODZĄ TYLKO POWYŻEJ 60 PKT ===
        if simulated_score >= 60:
            has_adamantium = df['Notatka'].str.contains("Wątroba z Adamantium", na=False).any()
            
            damage_modifier = 10 if has_adamantium else 20 # Perk zmniejsza obrażenia do 10

            # 1. Obrażenia
            if status == "IGLISKO":
                current_hp -= damage_modifier # <-- ZMIANA
            elif status == "IGLUTEK":
                current_hp -= 10
        
        # 2. Leczenie (Działa zawsze, bo kupić można tylko mając 60+ pkt i sklep)
        if "SHOP_BUY" in note and "Apteczka" in note:
            current_hp += 80 # Zwiększone leczenie!
            
        # 3. Bezpieczniki
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

# --- FUNKCJA ANIMACJI CYBER-SCANNER (HYBRYDA NAPRAWIONA) ---
def play_level_up_animation(new_cycle):
    # 1. BEZPIECZNIK: Definiujemy zmienną na start, żeby uniknąć NameError
    filename = None 
    placeholder = st.empty()

    # --- SCENARIUSZ A: OTWARCIE SKARBCA (Level 1 - Animacja Kodowa) ---
    if new_cycle == 1:
        with placeholder.container():
            st.markdown("---")

            # 1. HACKOWANIE
            with st.spinner("⚠️ WYKRYTO FLUKTUACJE ENERGII..."):
                time.sleep(1.5)

            progress_text = "🔐 ŁAMANIE ZABEZPIECZEŃ SKARBCA..."
            my_bar = st.progress(0, text=progress_text)

            # Symulacja ładowania
            for percent_complete in range(100):
                time.sleep(0.01) 
                my_bar.progress(percent_complete + 1, text=f"DEKODOWANIE: {percent_complete}%")

            time.sleep(0.5)
            my_bar.empty() 

            # 2. EFEKT "ROZRZUCANIA KAMIENI"
            stones_fx = [
                ("🟣", "#800080"), # MOC
                ("🔵", "#0000FF"), # PRZESTRZEŃ
                ("🔴", "#FF0000"), # RZECZYWISTOŚĆ
                ("🟠", "#FF8C00"), # DUSZA
                ("🟢", "#008000"), # CZAS
                ("🟡", "#FFD700")  # UMYSŁ
            ]

            st.subheader("🔭 SKANOWANIE MULTIWERSUM...")

            cols = st.columns(5)
            # Pętla generująca losowe błyski
            for _ in range(25): 
                col = random.choice(cols)
                stone_icon, stone_color = random.choice(stones_fx)
                with col:
                    st.markdown(f"<h1 style='text-align: center; color: {stone_color};'>{stone_icon}</h1>", unsafe_allow_html=True)
                time.sleep(0.15) 

            # 3. FINAŁ
            time.sleep(0.5)
            st.success("✅ DOSTĘP PRZYZNANY. SKARBIEC OTWARTY.")
            
            # Terminalowy komunikat
            st.code("SYSTEM: ONLINE\nCEL: ZEBRAĆ JE WSZYSTKIE\nSTATUS: BOHATER", language="bash")
            time.sleep(4)

    # --- SCENARIUSZ B: WYŻSZE POZIOMY (Opcjonalne Wideo) ---
    elif new_cycle == 2:
        filename = "veteran_levelup.mp4"
    elif new_cycle == 3:
        filename = "hero_levelup.mp4"

    # 4. ODTWARZANIE WIDEO (Tylko jeśli zdefiniowano filename)
    # To jest ten fragment, który wcześniej wywoływał błąd
    if filename: 
        if os.path.exists(filename):
            with placeholder.container():
                st.balloons()
                st.video(filename, autoplay=True)
                time.sleep(8)
        else:
            # Jeśli plik wideo nie istnieje, ale miał być (dla level 2 i 3)
            st.toast(f"🎉 AWANS! (Brak pliku: {filename})", icon="🎬")
            time.sleep(3)
    
    # Czyszczenie po animacji
    time.sleep(1)
    placeholder.empty()

def get_hedgehog_comment(api_key, status, points, total_score, owned_stones, note, party_mode, df, streak_count, streak_type, previous_comment):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # 1. Analiza wpisów z dzisiaj
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_history = ""
        if not df.empty:
            today_df = df[df['Data'] == today_str].sort_values(by='Godzina')
            if not today_df.empty:
                entries = [f"{row['Godzina']} -> {row['Stan']} ({row['Punkty']} pkt)" for _, row in today_df.iterrows()]
                today_history = "\n".join(entries)
            else:
                today_history = "To pierwszy wpis dzisiaj."
        else:
            today_history = "Brak historii."

        # 2. Kamienie
        stone_text = f"Kamienie: {owned_stones}/6" if total_score >= 60 else "Etap: PROLOG."

        # 3. ZAPOBIEGANIE POWTÓRZENIOM (Anti-Repetition)
        last_comment_warning = ""
        if previous_comment:
            last_comment_warning = f"""
            ⛔ OSTATNIO POWIEDZIAŁEŚ: "{previous_comment}"
            ZASADA KRYTYCZNA: Nie możesz powtórzyć tego samego żartu, motywu ani słowa kluczowego (np. jeśli było o chimichandze, teraz musi być o czymś innym). Bądź kreatywny.
            """

        # 4. DEFINICJA OSOBOWOŚCI (V3.0 - FINAL CASTING)
        personality = ""
        
        if party_mode:
            # --- TRYB IMPREZA: THOR + ROCKET ---
            personality = """
            TRYB: IMPREZA (THOR & ROCKET). Jesteś mieszanką boga piorunów i agresywnego szopa.
            
            TWOJE CECHY (Mieszaj je):
            1. 🍺 THOR:
               - Jesteś głośny, wylewny i teatralny.
               - Używasz słów: "Zacny trunek!", "Kolejny!", "Czy jesteś godzien?!".
               - Jeśli traci punkty: "To wina Lokiego!", "Mój młot też czasem nie trafia".
            2. 🦝 ROCKET RACCOON:
               - Agresywny, chciwy, szuka zadymy.
               - "Zamknij się i pij", "Ukradnę komuś nogę dla zabawy".
               - Jeśli zdobywa punkty: "Nareszcie! Teraz kupujemy największą bombę w galaktyce!".
            
            STYL: Emocjonalny, chaotyczny, imprezowy. 
            """
        else:
            # --- TRYB STANDARD: STAR-LORD + DEADPOOL ---
            personality = """
            TRYB: STANDARD (STAR-LORD & DEADPOOL).
            
            TWOJE CECHY (Mieszaj je):
            1. 🎧 STAR-LORD (Peter Quill):
               - Jesteś "cool" (przynajmniej tak myślisz). Kochasz lata 80. i muzykę.
               - Próbujesz być liderem: "Dobra plan jest taki...", "Wyglądamy jak legendy".
               - Traktuj Pawła jak członka załogi, który trochę nie ogarnia.
            2. ⚔️ DEADPOOL (Wade Wilson):
               - Łamiesz 4. ścianę, ale FILMOWO (nie IT).
               - Odnoś się do: "niskiego budżetu tej symulacji", "leniwych scenarzystów", "recyklingu fabuły".
               - Unikaj nudnego "lubię chimichangi". Bądź kreatywny: "Moja twarz wygląda lepiej niż ten wynik", "Czy my jesteśmy w wersji reżyserskiej?".
            
            ZASADY STYLU:
            - ZERO terminologii IT (zakaz słów: kod, python, skrypt, bug). Zastąp je słowami: scenariusz, glitch w Matrixie, budżet produkcji.
            - Bądź dowcipny, ale też wymagający.
            - Jeśli ma passę (streak): "Oho, ktoś tu czytał poradnik do gry?", "Star-Lord approves this moves!".
            """

        user_prompt = f"""
        DANE: {status} ({points} pkt). Notatka: "{note}"
        KONTEKST DZISIAJ:
        {today_history}
        
        STATYSTYKI: Passa {streak_count}, Wynik {total_score}, {stone_text}
        
        {last_comment_warning}
        
        ROLA:
        {personality}
        
        Napisz JEDEN krótki, celny komentarz (max 2 zdania). Ma być ostry i zabawny.
        """
        
        response = model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_prompt]}
        ])
        return response.text
    except Exception as e:
        return f"Jeż milczy. (BŁĄD API)"

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
    streak_count, streak_type = calculate_current_streak(df)
    current_hp = calculate_hp(df)

    # --- SIDEBAR (Pasek Boczny z Jeżem i HP) ---
    with st.sidebar:
        # 1. Avatar i Ranga
        if current_score < 60:
            st.image("https://cdn-icons-png.flaticon.com/512/3468/3468306.png", width=100)
            st.title("Stażysta")
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/9440/9440535.png", width=100)
            st.title("Agent T.A.R.C.Z.Y.")
            
        st.markdown("---")
        
        # 2. Licznik Punktów
        st.metric(label="Moc całkowita (EXP)", value=current_score)
        
        # 3. Pasek Zdrowia (HP) - Widoczny tylko dla Agenta (60+ pkt)
        if current_score >= 60:
            st.markdown("### ❤️ Stan Zdrowia")
            
            # Kolor paska
            if current_hp > 50: bar_color = "green"
            elif current_hp > 20: bar_color = "orange"
            else: bar_color = "red"
                
            st.progress(current_hp / 100, text=f"{current_hp}/100 HP")
            
            if current_hp <= 0:
                st.error("STAN KRYTYCZNY!")
        else:
            st.info("❤️ Zdrowie: Chronione (Poligon)")
            
        st.markdown("---")
    
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
    if st.button("🔄 PSTRYKNIJ PALCAMI (Zresetuj Wszechświat)", type="primary"):
        if os.path.exists(SNAP_SOUND_FILE):
            st.audio(SNAP_SOUND_FILE, format="audio/mp3", autoplay=True)
        
        # --- FIX: CZYSZCZENIE ARKUSZA ---
        try:
            sheet = client.open(GOOGLE_SHEET_NAME).sheet1
            # Zostawiamy nagłówki (pierwszy wiersz), kasujemy resztę
            # Uwaga: resize(1) to szybka metoda na ucięcie arkusza do 1 wiersza
            sheet.resize(rows=1) 
            sheet.resize(rows=1000) # Przywracamy rozmiar, ale puste wiersze
            get_data_from_sheets.clear() # Czyścimy cache w aplikacji
        except Exception as e:
            st.error(f"Błąd resetowania bazy: {e}")
            st.stop()
        # -------------------------------

        st.toast("🫰 Pstryk! Równowaga przywrócona...")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
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
            
            # --- ZMIANA: Pasek HP widoczny tylko od 60 pkt ---
            if current_score >= 60:
                hp_color = "red" if current_hp < 30 else "green"
                st.write(f"❤️ **Stan Zdrowia:** {current_hp}/100")
                st.progress(current_hp / 100, text=None)
                if current_hp == 0:
                    st.error("STAN KRYTYCZNY! SZPITAL!")
            else:
                st.info("❤️ Zdrowie: Chronione (Prolog)")
            # -------------------------------------------------
            
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
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Misja Dnia", "📊 Statystyki", "🛒 Sklep", "⚙️ Ustawienia"])
    
    # --- ZAKŁADKA 1: MISJA DNIA ---
    with tab1:
        st.header("🎬 Dziennik Iglasty")

        # --- 📜 CYTAT DNIA (TERAZ TUTAJ - POD NAGŁÓWKIEM) ---
        st.markdown(f"""
        <div style='text-align: center; color: #808080; font-style: italic; font-size: 0.9em; margin-bottom: 15px; padding: 10px; background-color: #262730; border-radius: 5px;'>
            ❝ {daily_quote} ❞
        </div>
        """, unsafe_allow_html=True)

        bounty = get_daily_bounty()
        
        # Wyciągamy kwotę z tekstu
        try: bounty_value = int(bounty['reward'].split()[0])
        except: bounty_value = 0

        st.markdown("### 📜 Zlecenie Dnia")
        
        with st.container(border=True):
            col_b1, col_b2 = st.columns([1, 5])
            with col_b1: st.markdown("# 🎯")
            with col_b2:
                st.markdown(f"**{bounty['title']}**")
                st.caption(f"{bounty['desc']}")
                st.info(f"Nagroda: {bounty['reward']}")
                
                # Weryfikacja
                is_completed = check_bounty_completion(bounty['title'], df)
                
                # Sprawdzenie czy odebrano
                today_iso = get_polish_time().strftime("%Y-%m-%d")
                already_claimed = False
                if not df.empty and 'Notatka' in df.columns:
                    search_tag = f"BOUNTY_CLAIM | {today_iso}"
                    already_claimed = df['Notatka'].astype(str).str.contains(search_tag, regex=False).any()
                
                # Przycisk
                if already_claimed:
                    st.success("✅ Nagroda odebrana!")
                else:
                    if st.button(f"💰 Odbierz {bounty_value} Kredytów", disabled=not is_completed):
                        note_content = f"BOUNTY_CLAIM | {today_iso} | {bounty_value}"
                        save_to_sheets("NAGRODA", 0, "Zlecenie Dnia", False, note_content)
                        st.balloons()
                        st.toast(f"Wypłacono {bounty_value} kredytów!", icon="🤑")
                        time.sleep(2)
                        st.rerun()
                    
                    if not is_completed:
                        st.caption("🔒 *Zadanie niezweryfikowane. Wykonaj cel, aby odblokować.*")
                    else:
                        st.caption("🔓 *Zadanie wykonane! Odbierz nagrodę.*")
        
        st.markdown("---")
        
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
            safe_score = max(0, current_score)
            prolog_stage_index = int(safe_score // 15)
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
        
        # UKRYWANIE KAMIENI W PROLOGU
        if current_score < 60:
            c1, c2 = st.columns(2)
            c1.metric("Całkowity EXP", f"{current_score}")
            c2.metric("Seria", f"{streak_count} 🔥")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Całkowity EXP", f"{current_score}")
            c2.metric("Kamienie", f"{owned_stones}/6")
            c3.metric("Seria", f"{streak_count} 🔥")
        
        st.markdown("---")
        
        if not df.empty:
            st.subheader("📈 Historia Aktywności")
            try:
                chart_data = df[['Data', 'Punkty']].copy()
                chart_data = chart_data.groupby('Data')['Punkty'].sum().reset_index()
                st.line_chart(chart_data, x='Data', y='Punkty')
            except:
                st.caption("Za mało danych na wykres.")
        
# --- ZAKŁADKA 3: SKLEP (TERAZ RÓWNO Z INNYMI) ---
    with tab3:
        st.header("🛒 Czarny Rynek Artefaktów")
        
        # 1. Portfel
        wallet = calculate_currency(df, current_score, owned_stones)
        st.metric(label="Dostępne Środki", value=f"{wallet} 🪙", delta="Kredyty Galaktyczne")
        if current_score < 60:
            st.info("💡 Jesteś w Prologu. Zbieraj kredyty, ale pamiętaj: Bonus +300 🪙 otrzymasz dopiero po awansie na Agenta (60 pkt)!")
        st.markdown("---")
        
        # 2. LOGIKA ROTACJI
        current_month = datetime.now().month
        shop_rotation_index = ((current_month + 10) // 2) % 3
        current_offer = SHOP_INVENTORY.get(shop_rotation_index, [])
        rotation_names = ["Strażnicy & Najemnicy", "Avengers Assemble", "Magia & Kosmos"]
        
        st.info(f"📦 Obecna dostawa: **{rotation_names[shop_rotation_index]}**")
        st.caption("Oferta zmienia się co 2 miesiące.")

        # --- NOWA SEKCJA: SZKOLENIA S.H.I.E.L.D. (PERKI) ---
        with st.expander("🧠 Szkolenia S.H.I.E.L.D. (Pasywne Umiejętności)", expanded=True):
            st.caption("Drogie, stałe ulepszenia konta. Działają zawsze.")
            
            for key, perk in PERKS_DB.items():
                pc1, pc2, pc3 = st.columns([1, 3, 2])
                with pc1:
                    st.markdown("## 🧬")
                with pc2:
                    st.write(f"**{perk['name']}**")
                    st.caption(perk['desc'])
                with pc3:
                    is_owned = has_perk(df, key)
                    if is_owned:
                         st.button("✅ Aktywne", key=f"perk_owned_{key}", disabled=True)
                    else:
                        if st.button(f"Kup ({perk['cost']} 🪙)", key=f"btn_perk_{key}"):
                            # Logika kupna perka
                            get_data_from_sheets.clear()
                            fresh_df = get_data_from_sheets()
                            fresh_wallet = calculate_currency(fresh_df, current_score, owned_stones)
                            
                            if fresh_wallet < perk['cost']:
                                st.error("❌ Za mało środków!")
                            else:
                                note_content = f"PERK_BUY | {perk['name']} | -{perk['cost']}"
                                save_to_sheets("PERK", 0, "Sklep", False, note_content)
                                st.balloons()
                                st.success(f"🧬 Odblokowano: {perk['name']}")
                                time.sleep(2)
                                st.rerun()
            st.markdown("---")

        has_discount = has_perk(df, "discount")
        for item in current_offer:
            base_price = item['cost']
            final_price = int(base_price * 0.8) if has_discount else base_price
            c1, c2, c3 = st.columns([1, 3, 2])
            with c1:
                st.markdown(f"<div style='font-size: 50px; text-align: center;'>{item['icon']}</div>", unsafe_allow_html=True)
            with c2:
                st.subheader(item['name'])
                st.caption(item['desc'])
                st.markdown(f"**Bohater:** {item['hero']}")
            with c3:
                if has_discount:
                    st.markdown(f"~~{base_price}~~ **{final_price} 🪙**")
                else:
                    st.write(f"**{final_price} 🪙**")
                
                # ZABEZPIECZENIE: CZY POSIADA
                already_owned = False
                if not df.empty and 'Notatka' in df.columns:
                    search_str = f"SHOP_BUY | {item['name']}"
                    already_owned = df['Notatka'].astype(str).str.contains(search_str, regex=False).any()

                if already_owned:
                    st.button(f"✅ Już posiadasz", key=f"btn_owned_{item['name']}", disabled=True)
                else:
                   if st.button(f"Kup ({final_price} 🪙)", key=f"btn_{item['name']}"):
                        with st.spinner("Weryfikacja transakcji..."):
                            get_data_from_sheets.clear()
                            fresh_df = get_data_from_sheets()
                            fresh_wallet = calculate_currency(fresh_df, current_score, owned_stones)
                            
                            if fresh_wallet < price:
                                st.error("❌ Transakcja odrzucona! Za mało środków.")
                            else:
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

# --- ZAKŁADKA 4: USTAWIENIA (TERAZ RÓWNO Z INNYMI) ---
    with tab4:
        st.header("⚙️ Centrum Konfiguracji")
        st.write("Dostosuj parametry swojej misji.")
        st.markdown("---")
        
        st.subheader("📅 Przypomnienia")
        st.info("Regularność to klucz do sukcesu Agenta. Ustaw przypomnienie w kalendarzu, aby nie stracić passy (Streak)!")
        
        base_calendar_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
        event_title = "🦔 Dziennik Iglasty - Raport"
        event_details = "Czas uzupełnić dziennik i sprawdzić postępy Agenta! 👉 https://pawel-lvl30.streamlit.app"
        calendar_url = f"{base_calendar_url}&text={event_title}&details={event_details}&recur=RRULE:FREQ=DAILY"
        
        col_sets_1, col_sets_2 = st.columns([1, 2])
        with col_sets_1:
            st.markdown("### 🔔")
        with col_sets_2:
            st.write("**Codzienny Raport**")
            st.caption("Kliknij, aby dodać stałe przypomnienie do swojego Kalendarza Google.")
            st.link_button("📅 Dodaj do Kalendarza", calendar_url)
        
        st.markdown("---")
        st.caption("W przyszłości znajdziesz tu więcej opcji, np. resetowanie konta czy zmianę motywu.")
        
    st.markdown("---")

        st.markdown("---")
        st.subheader("🚨 Strefa Awaryjna")
        
        col_undo_1, col_undo_2 = st.columns([1, 3])
        with col_undo_1:
            st.markdown("## ↩️")
        with col_undo_2:
            st.write("**Cofnij ostatnią akcję**")
            st.caption("Jeśli kliknąłeś coś przez pomyłkę, ten przycisk trwale usunie ostatni wpis z bazy danych.")
            
            if st.button("🗑️ Usuń ostatni wpis", type="secondary"):
                with st.spinner("Łączenie z Matrixem..."):
                    success, msg = undo_last_entry()
                    
                    if success:
                        st.success(msg)
                        st.toast("✅ Cofnięto ostatnią akcję!", icon="🔙")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error(msg)
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
    selected = None  # Reset wyboru
    
    # --- 💀 LOGIKA SZPITALA (Warunek: Agent + 0 HP) ---
    if current_score >= 60 and current_hp <= 0:
        st.error("💀 JESTEŚ W SZPITALU (0 HP)!")
        st.info("Systemy podtrzymywania życia aktywne. Nie możesz podejmować akcji.")
        st.warning("👉 Idź do Sklepu i kup 'Apteczkę S.H.I.E.L.D.', aby wrócić do gry.")
        if os.path.exists("hospital.jpg"):
            st.image("hospital.jpg", caption="Odpoczywaj, bohaterze...")
            
    else:
        # --- ✅ JESTEŚ ŻYWY (Rysujemy przyciski) ---
        cols = st.columns(5)
        
        # Konfiguracja punktów
        if st.session_state.party_mode:
            score_iglica = 5; score_igla = 2; score_iglik = 0; score_iglute = -6; score_iglisko = -12
        else:
            score_iglica = 3; score_igla = 1; score_iglik = 0; score_iglute = -2; score_iglisko = -4
            
        buttons = [
            (f"🗻 IGLICA", "IGLICA", score_iglica, cols[0]),
            (f"💎 IGŁA", "IGŁA", score_igla, cols[1]),
            (f"🌿 IGLIK", "IGLIK", score_iglik, cols[2]),
            (f"🍂 IGLUTEK", "IGLUTEK", score_iglute, cols[3]),
            (f"💀 IGLISKO", "IGLISKO", score_iglisko, cols[4])
        ]
        
        # PĘTLA TWORZĄCA PRZYCISKI (Tutaj był problem z wyciekiem zmiennej!)
        for label, btn_status, btn_points, col in buttons:
            # Używamy unikalnego klucza (key), żeby Streamlit nie gubił się w stanie
            if col.button(f"{label}\n({btn_points:+})", key=f"btn_{btn_status}", use_container_width=True):
                selected = (btn_status, btn_points)
    
    # --- LOGIKA PO KLIKNIĘCIU (Twoja sprawdzona sekcja) ---
    if selected:
        status, points = selected # <--- TO JEST KLUCZOWE ROZPAKOWANIE
        
        # 1. LEVEL GATE (BRAMA SKARBCA)
        if points > 0: 
            current_cycle_num = current_score // 60
            next_threshold = (current_cycle_num + 1) * 60
            if current_score < next_threshold and (current_score + points) > next_threshold:
                diff = next_threshold - current_score
                points = diff 
                st.toast(f"🛑 DOTARŁEŚ DO BRAMY SKARBCA! (Stop na {next_threshold} pkt)", icon="🛡️")
                time.sleep(1)

        # 2. ANTI-CWANIAK (IMPREZY W TYGODNIU)
        penalty_applied = False
        if st.session_state.party_mode:
            today = get_polish_time()
            if today.weekday() < 5:# Pon-Czw (Piątek wieczór to już weekend)
                yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
                today_str = today.strftime("%Y-%m-%d")
                
                # Czy wczoraj była impreza?
                yesterday_party = False
                if not df.empty and 'Tryb' in df.columns:
                    yesterday_party = not df[(df['Data'] == yesterday_str) & (df['Tryb'] == "ON")].empty
                
                if yesterday_party:
                    # Ile razy dzisiaj?
                    today_party_count = 0
                    if not df.empty and 'Tryb' in df.columns:
                         today_party_count = len(df[(df['Data'] == today_str) & (df['Tryb'] == "ON")])
                    
                    if today_party_count == 0:
                        st.toast("🤨 Ostrzeżenie: Ciąg imprezowy!", icon="👮")
                        user_note += " [OSTRZEŻENIE: CIĄG]"
                    else:
                        penalty_applied = True
                        user_note = "SHOP_BUY | MANDAT ZA IMPREZOWANIE | -100"
                        points = -10 
                        status = "MANDAT 👮"
                        st.error("🚨 RECYDYWA! MANDAT -100 KREDYTÓW.")

        # 3. ANTI-CHEAT (LIMIT 3 KLIKÓW)
        today_str_ac = datetime.now().strftime('%Y-%m-%d')
        try:
            todays_count = len(df[df['Data'] == today_str_ac])
        except:
            todays_count = 0
            
        if todays_count >= 3:
            st.error("🛑 LIMIT 3 AKCJI DZIENNIE! Odpocznij.")
            time.sleep(2)
            st.rerun()

        # 4. AUDIO & VISUAL FEEDBACK (Naprawiony)
        delay_time = 2.5
        
        # A. SUKCES (IGLICA / IGŁA)
        if points > 0:
            is_streak = (status == "IGLICA" and streak_count >= 2 and streak_type == 'positive')
            
            if is_streak:
                # Losujemy nagrodę (Star-Lord lub Deadpool)
                rewards = [
                    ("starlord.gif", "gotg_win.mp3", "🕺 DANCE OFF! Star-Lord wymiata!"),
                    ("deadpool_dance.gif", "deadpool_music.mp3", "💃 COMBO! Deadpool przejmuje show!")
                ]
                gif, audio, cap = random.choice(rewards)
                
                if os.path.exists(audio) and os.path.exists(gif):
                    st.toast(f"🔥 SERIA: {streak_count + 1}!", icon="🎉")
                    st.audio(audio, autoplay=True)
                    st.markdown("---")
                    st.image(gif, caption=cap, use_container_width=True)
                else:
                    st.success(f"🔥 SERIA UTRZYMANA! ({streak_count + 1} dzień)")
            else:
                if st.session_state.party_mode:
                    party_msgs = ["🍺 Zaksięgowano.", "🦝 Jeszcze jeden!", "🔥 Wchodzi gładko.", "💿 DJ, graj to!"]
                    st.success(random.choice(party_msgs))
                else:
                    system_msgs = [
                        "✅ Dane zapisane.",
                        "💾 Zaktualizowano bazę.",
                        "💎 Dodano punkty.",
                        "📡 Transmisja zakończona.",
                        "📝 Odnotowano.",
                        "🆗 Przyjęte."
                    ]
                    st.success(random.choice(system_msgs))

        # B. PORAŻKA (IGLISKO / MANDAT)
        elif points < 0:
            is_fail_streak = (status == "IGLISKO" and streak_count >= 2 and streak_type == 'negative')
            
            if is_fail_streak:
                if st.session_state.party_mode:
                    # Impreza -> Pijany Thor
                    if os.path.exists("thor_drunk.mp3") and os.path.exists("thor_drunk.gif"):
                        st.audio("thor_drunk.mp3", autoplay=True)
                        st.image("thor_drunk.gif", caption="🍺 Thor też ma gorszy dzień.")
                    else:
                        st.error("🍺 Seria porażek.")
                else:
                    # Standard -> Rocket (Tylko tekst)
                    insults = ["🦝 ROCKET: Daj mi ster!", "🦝 ROCKET: Tragedia."]
                    st.error(random.choice(insults))
            else:
                st.error("💀 Auć.")
    
# --- 🎰 KOŁO FORTUNY (GLOBALNY HAZARD) 🎰 ---
        chaos_change = 0
        
        # 1. Sprawdzamy Perka (Domino)
        has_lucky_perk = has_perk(df, "lucky")
        chance_threshold = 0.10 if has_lucky_perk else 0.05 # 10% z perkiem, 5% bez
        
        # 2. Losujemy czy uruchomić koło
        if random.random() < chance_threshold: 
            
            # 🔥 LOGIKA DOMINO: Eliminacja pecha
            if has_lucky_perk:
                # Z perkiem: Tylko dobre opcje + JACKPOT (+5)
                wheel_options = [0, 2, 2, 5] 
                options_desc = "🍀 DOMINO EFFECT: Pech zablokowany!"
            else:
                # Bez perka: Ryzyko (-2, 0, 2)
                wheel_options = [-2, 0, 2]
                options_desc = "🎲 RYZYKO: Standardowe"

            chaos_change = random.choice(wheel_options)
            
            # Dźwięk chaosu
            if os.path.exists("chaos_event.mp3"):
                st.audio("chaos_event.mp3", autoplay=True)
                if delay_time < 4.0: delay_time = 4.0
    
            # --- SCENARIUSZ 1: FART / JACKPOT ---
            if chaos_change > 0:
                if chaos_change >= 5:
                     st.toast(f"🎰 JACKPOT (Domino)! Bonus +{chaos_change} pkt!", icon="🦄")
                     st.balloons()
                else:
                     st.toast(f"🎰 KOŁO FORTUNY: FART! Bonus +{chaos_change} pkt!", icon="🍀")
    
            # --- SCENARIUSZ 2: PECH ---
            elif chaos_change < 0:
                st.toast(f"🎰 KOŁO FORTUNY: PECH! Tracisz {abs(chaos_change)} pkt!", icon="💀")
    
            # --- SCENARIUSZ 3: BEZ ZMIAN ---
            else:
                st.toast("🎰 KOŁO FORTUNY: Przeszło obok (0 pkt).", icon="😅")
                if has_lucky_perk:
                    st.caption(f"⚡ {options_desc}") # Informacja dla gracza, że perk zadziałał
    
            # Dodajemy info do notatki
            user_note += f" [KOŁO: {chaos_change:+d}]"
        
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
                    streak_type,
                    st.session_state.last_comment
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


















































































