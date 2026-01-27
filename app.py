import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Gra o Tron... i Igły",
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

# --- KONFIGURACJA API ---
try:
    DEFAULT_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    DEFAULT_API_KEY = ""

# --- SYSTEM PROMPT (RPG EDITION) ---
SYSTEM_PROMPT = """
Jesteś MISTRZEM GRY i cynicznym Jeżem w jednym.
Twoim celem jest komentowanie postępów Pawła w grze o nazwie "Życie".

ZASADY:
1. Paweł zbiera "Igły" (punkty).
2. OTRZYMASZ: Aktualny stan (np. Iglisko -5 pkt) oraz SUMĘ PUNKTÓW W TYM MIESIĄCU.
3. Jeśli suma jest niska (<0): Szydź z niego, że jest łysym kretem i traci godność.
4. Jeśli suma jest wysoka (>50): Chwal go, ale z przekąsem (np. "Oho, ktoś tu błyszczy").
5. Jeśli jest neutralnie (ok. 0): Narzekaj na nudę i stagnację.

Notatka od Pawła jest kluczowa - odnieś się do niej.
Styl: Krótko, złośliwie, jak w grze RPG, gdzie narrator nienawidzi gracza.
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

def get_monthly_score():
    """Oblicza sumę punktów w bieżącym miesiącu"""
    if os.path.isfile('historia_pawla.csv'):
        try:
            df = pd.read_csv('historia_pawla.csv')
            # Filtrowanie po aktualnym miesiącu
            current_month = datetime.now().strftime("%Y-%m")
            # Wyciągamy rok-miesiac z daty w CSV
            df['Month'] = df['Data'].apply(lambda x: x[:7]) 
            monthly_df = df[df['Month'] == current_month]
            
            return monthly_df['Punkty'].sum()
        except Exception:
            return 0
    return 0

def get_evolution_image(score):
    """Zwraca odpowiedni obrazek w zależności od wyniku"""
    if score < 0:
        return "level_1.png", "Poziom 1: ŁYSY KRET (Dno)"
    elif score < 20:
        return "level_2.png", "Poziom 2: JEŻ POSPOLITY (Start)"
    elif score < 60:
        return "level_3.png", "Poziom 3: JEŻ BOJOWY (Progres)"
    else:
        return "level_4.png", "Poziom 4: IMPERATOR IGLASTY (Max)"

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
        AKCJA:
        Paweł wybrał stan: {status} ({points} pkt).
        Jego powód: "{note}"
        
        STATYSTYKI RPG:
        Aktualny wynik miesięczny: {total_score} igieł.
        
        Skomentuj to. Jeśli traci punkty - jedź po nim. Jeśli zyskuje - gratuluj (ale bez przesady).
        """
        
        response = model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_prompt]}
        ])
        return response.text
    except Exception as e:
        return "Jeż liczy punkty i nie może mówić."

# --- UI APLIKACJI ---

def main():
    init_session_state()
    
    # Obliczamy wynik na start
    current_score = get_monthly_score()
    level_img, level_name = get_evolution_image(current_score)

    with st.sidebar:
        st.header("🏆 Statystyki Postaci")
        st.metric(label="Suma Igieł (Ten miesiąc)", value=current_score, delta=st.session_state.last_points_change)
        st.info(f"Aktualna forma:\n**{level_name}**")
        st.markdown("---")
        api_key_input = st.text_input("Klucz API", type="password", value=DEFAULT_API_KEY)

    st.title("🦔 Gra o Igły")
    st.caption("Zbieraj punkty, żeby ewoluować Jeża.")

    # 1. WIZUALIZACJA PROGRESU (Zamiast jednego obrazka po kliknięciu)
    col_img, col_stat = st.columns([1, 2])
    with col_img:
        if os.path.exists(level_img):
            st.image(level_img, caption=level_name)
        else:
            # Fallback jeśli brak plików
            st.header("🦔❓")
            st.caption(f"(Wgraj plik {level_img})")
    
    with col_stat:
        # Pasek postępu do następnego poziomu
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

    # 2. INPUT
    user_note = st.text_input("📝 Raport z pola walki (Dlaczego taki wybór?):")

    # 3. PRZYCISKI PUNKTOWE
    cols = st.columns(5)
    selected = None
    
    # Definicja przycisków z punktami
    buttons = [
        ("🗻 IGLICA", "IGLICA", 5, cols[0]),
        ("💎 IGŁA", "IGŁA", 2, cols[1]),
        ("🌿 IGLIK", "IGLIK", 0, cols[2]),
        ("🍂 IGLUTEK", "IGLUTEK", -2, cols[3]),
        ("💀 IGLISKO", "IGLISKO", -5, cols[4])
    ]

    for label, status, points, col in buttons:
        if col.button(f"{label}\n({points:+})", use_container_width=True):
            selected = (status, points)

    # 4. LOGIKA PO KLIKNIĘCIU
    if selected:
        status, points = selected
        if not api_key_input:
            st.error("Brak klucza API!")
        else:
            with st.spinner('Przeliczam igły...'):
                # Przewidywany nowy wynik dla AI
                new_total = current_score + points
                
                comment = get_hedgehog_comment(api_key_input, status, points, new_total, user_note)
                save_to_csv(status, points, comment, st.session_state.party_mode, user_note)
                
                # Zapisujemy zmianę do sesji, żeby wyświetlić ładny "Delta" w sidebarze
                st.session_state.last_points_change = points
                st.session_state.last_comment = comment
                st.rerun()

    # 5. OSTATNI KOMENTARZ
    if st.session_state.last_comment:
        st.success(f"💬 Jeż mówi: {st.session_state.last_comment}")

    # 6. HISTORIA
    with st.expander("📜 Dziennik punktowy"):
        if os.path.isfile('historia_pawla.csv'):
            df = pd.read_csv('historia_pawla.csv')
            st.dataframe(df[['Data', 'Godzina', 'Stan', 'Punkty', 'Notatka', 'Komentarz']].iloc[::-1], hide_index=True)

if __name__ == "__main__":
    main()
