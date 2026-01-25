import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="30 Urodziny Pawła - System Iglany",
    page_icon="🦔",
    layout="centered"
)

# --- KONFIGURACJA API (NAPRAWIONA) ---
try:
    DEFAULT_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    DEFAULT_API_KEY = ""

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Jesteś CERAMICZNYM JEŻEM – figurką ogrodową i sarkastycznym sumieniem Pawła (lat 30).
Twoim celem jest komentowanie jego samopoczucia. Styl: cyniczny, bystry, bezpośredni.
Unikaj korpo-gadki. Tematy: absurd życia, biologia 30-latka, walka z grawitacją.

SKALA:
1. IGLICA (Euforia) 2. IGŁA (Super) 3. IGLIK (Norma) 4. IGLUTEK (Słabo) 5. IGLISKO (Dno)

ZMIENNA: [TRYB_IMPREZOWY]
JEŚLI ON: Traktuj weekend jak ciągłą historię (Piątek: start, Sobota: bitwa, Niedziela: zgon, Poniedziałek: finał). Bądź podejrzliwy przy dobrych wynikach rano.
JEŚLI OFF: Skup się na nudzie, codzienności, pogodzie i małych sukcesach (np. pranie).

WYMAGANIA: Max 2 zdania. Styl "Punchline". Nigdy się nie powtarzaj.
"""

# --- FUNKCJE POMOCNICZE ---

def init_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'party_mode' not in st.session_state:
        st.session_state.party_mode = False
    if 'last_comment' not in st.session_state:
        st.session_state.last_comment = None
    if 'last_status' not in st.session_state:
        st.session_state.last_status = None

def save_to_csv(status, comment, party_mode):
    file_name = 'historia_pawla.csv'
    now = datetime.now()
    new_data = {
        'Data': now.strftime("%Y-%m-%d"),
        'Godzina': now.strftime("%H:%M"),
        'Stan': status,
        'Tryb Imprezowy': "ON" if party_mode else "OFF",
        'Komentarz': comment
    }
    df = pd.DataFrame([new_data])
    if not os.path.isfile(file_name):
        df.to_csv(file_name, index=False)
    else:
        df.to_csv(file_name, mode='a', header=False, index=False)
    st.session_state.history.insert(0, new_data)

def get_hedgehog_comment(api_key, status, party_active):
    try:
        genai.configure(api_key=api_key)
        # Używamy modelu FLASH, bo jest szybki i działa z nową biblioteką
        model = genai.GenerativeModel("gemini-pro")
        
        now = datetime.now()
        day_name = now.strftime("%A")
        time_now = now.strftime("%H:%M")
        
        user_prompt = f"""
        Stan Pawła: {status}
        Aktualny czas: {day_name}, {time_now}
        TRYB IMPREZOWY: {'ON' if party_active else 'OFF'}
        Skomentuj to teraz.
        """
        
        response = model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_prompt]}
        ])
        return response.text
    except Exception as e:
        return f"BŁĄD SYSTEMU JEŻA: {str(e)}"

# --- INTERFEJS APLIKACJI (UI) ---

def main():
    init_session_state()

    with st.sidebar:
        st.header("⚙️ Ustawienia Jeża")
        # Pole input jest wypełnione domyślnie tylko jeśli klucz jest w secrets
        api_key_input = st.text_input("Klucz API", type="password", value=DEFAULT_API_KEY)
        
        if not api_key_input:
            st.warning("⚠️ Brak klucza API! Dodaj go w 'Secrets' na Streamlit Cloud lub wpisz tutaj.")
        
        st.markdown("---")
        st.write("Wersja systemu: v.30.0 (Urodzinowa)")

    st.title("🦔 Dziennik Iglasty")
    st.markdown("*System operacyjny życia po trzydziestce.*")
    st.markdown("---")

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.write("### Jak się dzisiaj czujemy?")
    with col_t2:
        party_mode_new = st.toggle("TRYB IMPREZOWY 🔥", value=st.session_state.party_mode)
        if party_mode_new != st.session_state.party_mode:
            st.session_state.party_mode = party_mode_new
            if party_mode_new:
                st.toast("🚨 ZAPISANO! Szykuję elektrolity.", icon="🍸")
            else:
                st.toast("Uff... Wracamy do rzeczywistości.", icon="🏠")

    st.markdown("")

    col1, col2, col3, col4, col5 = st.columns(5)
    selected_status = None
    
    if col1.button("🗻\nIGLICA", use_container_width=True): selected_status = "IGLICA"
    if col2.button("💎\nIGŁA", use_container_width=True): selected_status = "IGŁA"
    if col3.button("🌿\nIGLIK", use_container_width=True): selected_status = "IGLIK"
    if col4.button("🍃\nIGLUTEK", use_container_width=True): selected_status = "IGLUTEK"
    if col5.button("💀\nIGLISKO", use_container_width=True): selected_status = "IGLISKO"

    if selected_status:
        if not api_key_input:
            st.error("Jeż milczy, bo brakuje mu klucza API.")
        else:
            with st.spinner('Jeż ostrzy kolce...'):
                comment = get_hedgehog_comment(api_key_input, selected_status, st.session_state.party_mode)
                st.session_state.last_status = selected_status
                st.session_state.last_comment = comment
                save_to_csv(selected_status, comment, st.session_state.party_mode)
                st.rerun()

    if st.session_state.last_status:
        st.markdown("---")
        img_col, txt_col = st.columns([1, 2])
        
        with img_col:
            image_filename = f"{st.session_state.last_status.lower()}.png"
            if os.path.exists(image_filename):
                st.image(image_filename, caption=st.session_state.last_status)
            else:
                emoji_map = {"IGLICA": "🗻", "IGŁA": "💎", "IGLIK": "🌿", "IGLUTEK": "🍃", "IGLISKO": "💀"}
                st.markdown(f"# {emoji_map[st.session_state.last_status]}")

        with txt_col:
            st.subheader(st.session_state.last_status)
            st.info(f"💬 {st.session_state.last_comment}")
            if st.session_state.party_mode:
                st.markdown("🔥 *Tryb Imprezowy aktywny*")

    st.markdown("---")
    with st.expander("📜 Zobacz historię logowania"):
        if os.path.isfile('historia_pawla.csv'):
            df = pd.read_csv('historia_pawla.csv')
            st.dataframe(df.iloc[::-1], hide_index=True, use_container_width=True)
        else:
            st.write("Brak wpisów.")

if __name__ == "__main__":

    main()
