import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os
import random

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Dziennik Iglasty",
    page_icon="🦔",
    layout="centered"
)

# --- KONFIGURACJA PLIKÓW ---
SNAP_SOUND_FILE = "snap.mp3"

# --- KONFIGURACJA PUNKTACJI (BALANS NA 3 WPISY DZIENNIE) ---
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

# --- BAZA CYTATÓW (DEADPOOL & GUARDIANS) ---
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

# --- KONFIGURACJA API ---
try:
    DEFAULT_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    DEFAULT_API_KEY = ""

# --- NOWY SYSTEM PROMPT (STYL DEADPOOL/ROCKET) ---
SYSTEM_PROMPT = """
Jesteś CERAMICZNYM JEŻEM, ale masz osobowość będącą nieślubnym dzieckiem Deadpoola i Rocketa Raccoona.
Twoim zadaniem jest komentowanie życia Pawła (lat 30), który traktuje to jak grę RPG.

TWOJA OSOBOWOŚĆ:
1. **Sarkazm poziom Master:** Jesteś cyniczny, bystry i nie masz filtra.
2. **Łamanie Czwartej Ściany:** Wiesz, że jesteś w aplikacji. Możesz komentować kod, Pawła albo fakt, że jesteś tylko tekstem na ekranie.
3. **Styl Deadpoola:** Chaos, nawiązania do popkultury (filmy, gry), czarny humor, autoironia.
4. **Styl Rocketa:** Traktuj Pawła jak trochę nieogarniętego Star-Lorda ("naprawdę to zrobiłeś? wow.").
5. **Kontekst:** Paweł zbiera punkty w grze zwanej "Życie po 30-tce".

ZASADY GRY (TEGO PILNUJ):
1. Pierwsze 60 pkt to PROLOG (Szkolenie). Nie wspominaj o Kamieniach Nieskończoności, udawaj, że to nudny tutorial, którego nie da się pominąć.
2. Od 60 pkt zaczyna się prawdziwa zabawa (Kamienie).
3. Reaguj na zmiany punktów:
   - Wzrost: "No, w końcu. Może jednak nie jesteś beznadziejny."
   - Spadek: "Serio? Znowu? Thanos miał rację."

Bądź krótki, złośliwy i zabawny.
"""

# --- FUNKCJE POMOCNICZE ---

def init_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
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

def get_data_from_csv():
    if os.path.isfile('historia_pawla.csv'):
        try:
            df = pd.read_csv('historia_pawla.csv')
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def get_monthly_score(df):
    if df.empty: return 0
    try:
        current_month = datetime.now().strftime("%Y-%m")
        df['Month'] = df['Data'].apply(lambda x: x[:7]) 
        monthly_df = df[df['Month'] == current_month]
        return monthly_df['Punkty'].sum()
    except:
        return 0

def calculate_current_streak(df):
    if df.empty:
        return 0, "neutral"
    
    streak = 0
    streak_type = None
    
    for index, row in df.iloc[::-1].iterrows():
        points = row['Punkty']
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

def get_smart_image_filename(cycle, owned_stones, cycle_progress):
    level_num = 1
    level_name = "KRET"
    
    if cycle_progress < 10:
        level_num = 2
        level_name = "POSPOLITY"
    elif cycle_progress < 45:
        level_num = 3
        level_name = "BOJOWY"
    else:
        level_num = 4
        level_name = "IMPERATOR"

    if cycle == 0:
        filename = f"level_{level_num}.png"
        desc = f"PROLOG | Poziom: {level_name}"
    else:
        filename = f"s{owned_stones}_lvl{level_num}.png"
        target_stone_idx = owned_stones 
        if target_stone_idx < len(INFINITY_STONES_NAMES):
            target_name = INFINITY_STONES_NAMES[target_stone_idx]
            desc = f"Cel: Kamień {target_name} | Forma: {level_name}"
        else:
            desc = f"BÓG | Forma: {level_name}"

    if os.path.exists(filename):
        return filename, desc
    else:
        return f"level_{level_num}.png", desc

def save_to_csv(status, points, comment, party_mode, note):
    file_name = 'historia_pawla.csv'
    now = datetime.now()
    new_data = {
        'Data': now.strftime("%Y-%m-%d"),
        'Godzina': now.strftime("%H:%M"),
        'Stan': status,
        'Punkty': points,
        'Notatka': note,
        'Tryb Imprezowy': "ON" if party_mode else "OFF",
        'Komentarz': comment
    }
    new_df = pd.DataFrame([new_data])
    if not os.path.isfile(file_name):
        new_df.to_csv(file_name, index=False)
    else:
        new_df.to_csv(file_name, mode='a', header=False, index=False)

def get_hedgehog_comment(api_key, status, points, total_score, owned_stones, note):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        stone_text = ""
        if total_score >= 60:
            stone_name = "Brak"
            if owned_stones > 0 and owned_stones <= len(INFINITY_STONES_NAMES):
                stone_name = INFINITY_STONES_NAMES[owned_stones - 1]
            stone_text = f"Posiadane Kamienie: {owned_stones} (Ostatni: {stone_name})"
        else:
            stone_text = "Etap: PROLOG (Nudny Tutorial). Kamienie: [CENZURA SPOILERA]."

        user_prompt = f"""
        SYTUACJA:
        Paweł wybrał: {status} ({points} pkt).
        Notatka użytkownika: "{note}"
        
        STATUS GRY:
        Całkowite punkty: {total_score}.
        {stone_text}
        
        Napisz krótki, złośliwy komentarz w stylu Deadpoola/Rocketa.
        """
        response = model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_prompt]}
        ])
        return response.text
    except Exception as e:
        return "Jeż milczy. (Scenarzysta zastrajkował, błąd API)"

# --- UI APLIKACJI ---

def main():
    init_session_state()
    
    df = get_data_from_csv()
    current_score = get_monthly_score(df)
    streak_count, streak_type = calculate_current_streak(df)
    
    cycle, owned_stones, cycle_progress = calculate_game_state(current_score)
    level_img, level_desc = get_smart_image_filename(cycle, owned_stones, cycle_progress)
    daily_quote = get_daily_quote()

    if owned_stones >= 6 and not st.session_state.snap_played:
        if os.path.exists(SNAP_SOUND_FILE):
            st.audio(SNAP_SOUND_FILE, format="audio/mp3", autoplay=True)
            st.toast("🫰 PSTRYK! Równowaga przywrócona.")
            st.session_state.snap_played = True

    # --- SIDEBAR ---
    with st.sidebar:
        if cycle == 0:
            st.header("📂 Status Agenta") 
        else:
            st.header("💎 Skarbiec Nieskończoności")

        st.metric(label="Moc całkowita (EXP)", value=current_score, delta=st.session_state.last_points_change)
        
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
        if DEFAULT_API_KEY:
             api_key_to_use = DEFAULT_API_KEY
        else:
             api_key_to_use = st.text_input("Klucz API", type="password")

    # --- MAIN ---
    st.markdown(f"""
    <div style="text-align: center; padding: 10px; margin-bottom: 20px; background-color: #1E1E1E; border-radius: 10px; border: 1px solid #333;">
        <span style="font-size: 0.9em; color: #FF4B4B; font-weight: bold;">🎬 CYTAT DNIA:</span><br>
        <span style="font-size: 1.1em; font-style: italic; color: #E0E0E0;">{daily_quote}</span>
    </div>
    """, unsafe_allow_html=True)

    st.title("🦔 Dziennik Iglasty")
    st.caption("System operacyjny życia po trzydziestce.")

    st.markdown("---")
    col_img, col_stat = st.columns([1, 2])
    with col_img:
        if os.path.exists(level_img):
            st.image(level_img, caption=level_desc)
        else:
            st.header("🦔")
            st.caption(f"(Brak pliku: {level_img})")
    
    with col_stat:
        if cycle == 0:
            st.subheader("Prolog: Droga do Wojownika")
            next_goal_text = "Odblokowanie Misji"
        elif owned_stones < 6:
            target_name = INFINITY_STONES_NAMES[owned_stones]
            st.subheader(f"Misja: Kamień {target_name}")
            next_goal_text = f"Zdobycie Kamienia {target_name}"
        else:
            st.subheader("Koniec Gry")
            next_goal_text = "Nieskończoność"

        progress_val = cycle_progress / 60.0
        if progress_val > 1.0: progress_val = 1.0
        if progress_val < 0: progress_val = 0.0
        
        st.progress(progress_val, text=f"Do celu ({next_goal_text}): {60 - cycle_progress} pkt")
        
        if cycle_progress < 10:
            st.caption("Stan: Rozgrzewka")
        elif cycle_progress < 45:
            st.caption("Stan: Walka trwa")
        else:
            st.caption("🔥 Stan: FINISH HIM!")

    st.markdown("---")

    col_note, col_toggle = st.columns([3, 1])
    with col_note:
        user_note = st.text_input("📝 Co się stało?", placeholder="Logi systemowe...")
    with col_toggle:
        st.write("")
        st.write("")
        party_mode_new = st.toggle("Tryb Impreza 🔥", value=st.session_state.party_mode)
        if party_mode_new != st.session_state.party_mode:
            st.session_state.party_mode = party_mode_new

    st.write("")
    cols = st.columns(5)
    selected = None
    
    buttons = [
        (f"🗻 IGLICA", "IGLICA", 3, cols[0]),
        (f"💎 IGŁA", "IGŁA", 1, cols[1]),
        (f"🌿 IGLIK", "IGLIK", 0, cols[2]),
        (f"🍂 IGLUTEK", "IGLUTEK", -2, cols[3]),
        (f"💀 IGLISKO", "IGLISKO", -4, cols[4])
    ]

    for label, status, points, col in buttons:
        if col.button(f"{label}\n({points:+})", use_container_width=True):
            selected = (status, points)

    if selected:
        status, points = selected
        if not api_key_to_use:
            st.error("Brak klucza API.")
        else:
            with st.spinner('Synchronizacja z Multiwersum...'):
                new_total = current_score + points
                new_cycle, new_owned, _ = calculate_game_state(new_total)
                
                comment = get_hedgehog_comment(api_key_to_use, status, points, new_total, new_owned, user_note)
                save_to_csv(status, points, comment, st.session_state.party_mode, user_note)
                
                st.session_state.last_points_change = points
                st.session_state.last_comment = comment
                
                st.rerun()

    if st.session_state.last_comment:
        if st.session_state.last_points_change >= 3:
             st.success(f"💬 **Jeż mówi:** {st.session_state.last_comment}")
        else:
             st.info(f"💬 **Jeż mówi:** {st.session_state.last_comment}")

    with st.expander("📜 Historia wpisów"):
        if not df.empty:
            st.dataframe(df[['Data', 'Godzina', 'Stan', 'Punkty', 'Notatka', 'Komentarz']].iloc[::-1], hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
