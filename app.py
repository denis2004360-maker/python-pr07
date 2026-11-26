from enum import Enum
from google import genai
from pydantic import BaseModel, Field
import streamlit as st

MODEL = "gemini-flash-lite-latest"

st.set_page_config(page_title="PY-B5T | Аналіз відгуку", page_icon="🎬")
st.title("🎬 Аналіз відгуку про фільм (PY-B5T)")


class Tonalnist(str, Enum):
    POZYTYVNYI = "позитивний"
    NEITRALNYI = "нейтральний"
    NEHATYVNYI = "негативний"


class Audytoria(str, Enum):
    USIM = "усім"
    POCINOVUVACHAM = "поціновувачам"
    NIKOMU = "нікому"
    VAZHKO_SKAZATY = "важко сказати"


class MijAnaliz(BaseModel):
    pidstava: str = Field(description="дослівна цитата з відгуку, на якій ґрунтується висновок")
    tonalnist: Tonalnist
    audytoria: Audytoria = Field(description="кому автор радить фільм")
    temy: list[str] = Field(min_length=2, max_length=4, description="теми, яких торкається відгук")
    mistyt_spoiler: bool = Field(description="чи розкриває відгук сюжетні повороти")


SYSTEM_MY = """Ти аналітик відгуків про фільми. Працюєш українською.
Спирайся тільки на текст відгуку. Жодних пояснень поза полями схеми."""


@st.cache_resource
def klijent():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def mij_analiz_app(text: str) -> MijAnaliz | None:
    try:
        resp = klijent().models.generate_content(
            model=MODEL,
            contents=f"Відгук про фільм:\n{text}",
            config={
                "system_instruction": SYSTEM_MY,
                "response_mime_type": "application/json",
                "response_schema": MijAnaliz,
                "temperature": 0.0,
                "max_output_tokens": 400,
            },
        )
        return resp.parsed
    except Exception:
        return None


with st.form("vidhuk"):
    text = st.text_area("Ваш відгук про фільм", height=150)
    nadislano = st.form_submit_button("Розібрати")

if nadislano and text.strip():
    with st.spinner("Аналізую відгук..."):
        r = mij_analiz_app(text)
    if r is None:
        st.warning("Не вдалося отримати відповідь від AI-сервісу. Спробуйте пізніше.")
    else:
        st.metric("Тональність", r.tonalnist.value)
        st.write("**Підстава (цитата):**", r.pidstava)
        st.write("**Аудиторія:**", r.audytoria.value)
        st.write("**Теми:**", ", ".join(r.temy))
        st.write("**Містить спойлер:**", "Так" if r.mistyt_spoiler else "Ні")
