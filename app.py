import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os
import random

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Dziennik Iglasty - Edycja Bohaterska",
    page_icon="🦔",
    layout="centered"
)

# --- KONFIGURACJA PUNKTACJI ---
POINTS_MAP = {
    "IGLICA": 5,
    "IGŁA": 2,
    "IGLIK": 0,
    "IGLUTEK": -2,
    "IGLISKO": -5
}

# --- BAZA CYTATÓW (MARVEL & DC - POPRAWIONE DLA 30-LATKA) ---
HERO_QUOTES = [
    "„I can do this all day... chyba, że strzyknie mi w kolanie.” – Kapitan Ameryka (wersja 30+)",
    "„Why so serious? Przecież to tylko poniedziałek.” – Joker",
    "„Z wielką mocą przychodzi wielka ochota na drzemkę.” – Wujek Ben (alternatywny)",
    "„I am Iron Man. A przynajmniej mój kręgosłup jest sztywny jak metal.” – Tony Stark",
    "„Wakanda Forever! Ale weekend forever byłby lepszy.” – Czarna Pantera",
    "„Hulk SMASH! ...ceny w sklepach.” – Hulk",
    "„Jestem Groot. (Tłumaczenie: Dajcie mi kawy).” – Groot",
    "„To nie jest 'S' jak Supermen. To 'S' jak Stres.” – Człowiek ze Stali",
    "„Mamy Hulka. A ja mam ibuprofen.” – Loki vs Tony",
    "„Dormammu, przyszedłem negocjować... wcześniejsze wyjście z pracy.” – Dr Strange",
    "„To mój sekret, Kapitanie. Zawsze jestem zmęczony.” – Bruce Banner",
    "„Bohaterowie są tacy jak my. Też płacą podatki.” – Batman",
    "„W ciemnościach... szukam ładowarki do telefonu.” – Mroczny Rycerz"
]

# --- KONFIGURACJA API ---
try:
    DEFAULT_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    DEFAULT_API_KEY = ""

# --- SYSTEM PROMPT (STARY, DOBRY JEŻ) ---
SYSTEM_PROMPT = """
Jesteś CERAMICZNYM JEŻEM – figurką ogrodową i sarkastycznym obserwatorem życia Pawła (lat 30).
Twoim celem jest komentowanie jego postępów w grze o nazwie "Życie".

ZASADY:
1. Paweł zbiera "Igły" (punkty).
2. Jeśli traci punkty (wybrał Iglisko/Iglutek): Bądź bezlitosny. Szydź z jego słabości.
3. Jeśli zyskuje (Iglica/Igła): Bądź podejrzliwy lub lekko gratulujący (ale z przekąsem).
4. Jeśli Iglik (0 pkt): Wyśmiej nudę i stagnację.
5. MASZ DOSTĘP DO NOTATKI. Odnieś się do niej!

Styl: Krótko, złośliwie, błyskotliwie. To nie jest korpo-mail, to riposta.
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

def get_daily_quote():
    """Losuje cytat stały dla danego dnia"""
    today_seed = datetime.now().strftime("%Y%m%d")
    random.seed(int(today_seed))
    return random.choice(HERO_QUOTES)

def get_monthly_score():
    if os.path.isfile('historia_pawla.csv'):
        try:
            df = pd.read_csv('historia_pawla.csv')
            current_month = datetime.now().strftime("%Y-%m")
            df['Month'] = df['Data'].apply(lambda x: x[:7]) 
            monthly_df = df[df['Month'] == current_month]
            return monthly_df['Punkty'].sum()
        except Exception:
            return 0
    return 0

def get_evolution_image(score):
    if score < 0:
        return "level_1.png", "Poziom: ŁYSY KRET (Dno)"
    elif score < 20:
        return "level_2.png", "Poziom: JEŻ POSPOLITY (Start)"
    elif score < 60:
        return "level_3.png", "Poziom: JEŻ BOJOWY (Progres)"
    else:
        return "level_4.png", "Poziom: IMPERATOR (Max)"

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

def get_hedgehog_comment(api_key, status, points, total_score, note):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        user_prompt = f"""
        SYTUACJA:
        Paweł wybrał: {status} (Zmiana punktów: {points}).
        Jego notatka: "{note}"
        
        Jego aktualny wynik miesięczny: {total_score} igieł.
        
        Skomentuj to złośliwie.
        """
        
        response = model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_prompt]}
        ])
        return response.text
    except Exception as e:
        return "Jeż milczy. (Błąd API)"

# --- UI APLIKACJI ---

def main():
    init_session_state()
    
    current_score = get_monthly_score()
    level_img, level_name = get_evolution_image(current_score)
    daily_quote = get_daily_quote()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Panel Sterowania")
        st.metric(label="Suma Igieł (Miesiąc)", value=current_score, delta=st.session_state.last_points_change)
        st.markdown("---")
        api_key_input = st.text_input("Klucz API", type="password", value=DEFAULT_API_KEY)

    # --- GÓRA STRONY (CYTAT) ---
    st.markdown(f"""
    <div style="text-align: center; padding: 10px; margin-bottom: 20px; background-color: #1E1E1E; border-radius: 10px; border: 1px solid #333;">
        <span style="font-size: 0.9em; color: #FF4B4B; font-weight: bold;">🎬 CYTAT DNIA:</span><br>
        <span style="font-size: 1.1em; font-style: italic; color: #E0E0E0;">{daily_quote}</span>
    </div>
    """, unsafe_allow_html=True)

    st.title("🦔 Dziennik Iglasty")
    st.caption("System operacyjny życia po trzydziestce.")

    # --- SEKCJA PROGRESU (TO CO CHCIAŁEŚ ZOSTAWIĆ) ---
    st.markdown("---")
    col_img, col_stat = st.columns([1, 2])
    with col_img:
        if os.path.exists(level_img):
            st.image(level_img, caption=level_name)
        else:
            st.header("🦔❓")
            st.caption(f"(Brak pliku {level_img})")
    
    with col_stat:
        st.subheader("Status Ewolucji")
        # Pasek postępu - logika
        if current_score < 0:
            st.progress(0, text="Stan krytyczny! Odrabiaj straty!")
        elif current_score < 20:
            progress = current_score / 20
            st.progress(progress, text=f"Do poziomu Bojowego: {20 - current_score} igieł")
        elif current_score < 60:
            progress = (current_score - 20) / 40
            st.progress(progress, text=f"Do Imperatora: {60 - current_score} igieł")
        else:
            st.progress(1.0, text="JESTEŚ BOGIEM JEŻY! 👑")

    st.markdown("---")

    # --- INPUT ---
    col_note, col_toggle = st.columns([3, 1])
    with col_note:
        user_note = st.text_input("📝 Co się stało? (Daj powód do komentarza):", placeholder="Np. sąsiad wierci, kawa była zimna...")
    with col_toggle:
        st.write("")
        st.write("")
        party_mode_new = st.toggle("Tryb Impreza 🔥", value=st.session_state.party_mode)
        if party_mode_new != st.session_state.party_mode:
            st.session_state.party_mode = party_mode_new

    # --- PRZYCISKI ---
    st.write("")
    cols = st.columns(5)
    selected = None
    
    buttons = [
        ("🗻 IGLICA", "IGLICA", 5, cols[0]),
        ("💎 IGŁA", "IGŁA", 2, cols[1]),
        ("🌿 IGLIK", "IGLIK", 0, cols[2]),
        ("🍂 IGLUTEK", "IGLUTEK", -2, cols[3]),
        ("💀 IGLISKO", "IGLISKO", -5, cols[4])
    ]

    for label, status, points, col in buttons:
        # Wyświetlamy samą nazwę, a punkty są ukryte w logice
        if col.button(f"{label}\n({points:+})", use_container_width=True):
            selected = (status, points)

    # --- LOGIKA ---
    if selected:
        status, points = selected
        if not api_key_input:
            st.error("Brak klucza API.")
        else:
            with st.spinner('Jeż ostrzy kolce...'):
                new_total = current_score + points
                comment = get_hedgehog_comment(api_key_input, status, points, new_total, user_note)
                save_to_csv(status, points, comment, st.session_state.party_mode, user_note)
                
                st.session_state.last_points_change = points
                st.session_state.last_comment = comment
                st.rerun()

    # --- WYNIK ---
    if st.session_state.last_comment:
        st.success(f"💬 **Jeż mówi:** {st.session_state.last_comment}")

    # --- HISTORIA ---
    with st.expander("📜 Historia wpisów"):
        if os.path.isfile('historia_pawla.csv'):
            df = pd.read_csv('historia_pawla.csv')
            st.dataframe(df[['Data', 'Godzina', 'Stan', 'Punkty', 'Notatka', 'Komentarz']].iloc[::-1], hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
