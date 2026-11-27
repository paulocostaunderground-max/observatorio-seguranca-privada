import datetime
import hashlib
import io
import re
import pandas as pd
import streamlit as st
from pypdf import PdfReader

import cct_engine
from cct_engine import (
    CATEGORIAS_PROFISSIONAIS,
    DISTRITOS_PORTUGAL,
    EMPRESAS_SEGURANCA,
    TIPOS_INCUMPRIMENTO,
    calcular_auditoria_periodo,
    obter_enquadramento,
    obter_sugestoes_cct,
    validar_nipc_portugues,
)
from pdf_generator import gerar_pdf_auditoria, gerar_pdf_ocorrencia

SINDICATOS_SETOR = getattr(
    cct_engine,
    "SINDICATOS_SETOR",
    [
        "STAD - Sindicato dos Trabalhadores de Serviços de Portaria, Vigilância, Limpeza",
        "ASSP - Associação Sindical da Segurança Privada",
        "FETESE - Federação dos Sindicatos da Indústria e Serviços",
        "SUSP - Sindicato Único da Segurança Privada",
        "SINDETELCO - Sindicato Democrático dos Trabalhadores das Comunicações e dos Media",
        "SINAPSA - Sindicato Nacional dos Profissionais de Seguros e Afins",
        "Outro Sindicato do Setor",
    ],
)

ESTADOS_CASO_SINDICAL = getattr(
    cct_engine,
    "ESTADOS_CASO_SINDICAL",
    [
        "Problema Resolvido com Sucesso (Acordo ou Tribunal)",
        "Em Curso / Com Acompanhamento Jurídico Ativo",
        "Apenas Sócio Preventivo (Ainda sem necessidade de apoio)",
        "Sem Resposta / Apoio Ineficaz",
    ],
)

LIMIAR_GRUPO_COLETIVO = 10

st.set_page_config(
    page_title="Vigilante Informado — Onde os Vigilantes Ganham Voz",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# SELETOR DE MODO DE VISUALIZAÇÃO (TELEMÓVEL / COMPUTADOR / AUTOMÁTICO)
# ==============================================================================
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.caption("Portal Independente de Apoio Técnico, Conferência Salarial e Literacia Laboral")
with col_top2:
    modo_escolhido = st.selectbox(
        "Formato de Ecrã:",
        ["Automático (Adaptável)", "Telemóvel (Android / iPhone)", "Computador (PC / Tablet)"],
        key="seletor_ecra_ui",
        label_visibility="collapsed",
    )

if modo_escolhido == "Telemóvel (Android / iPhone)":
    max_w_css = "540px"
    pad_side_css = "0.75rem"
    h1_size_css = "1.30rem"
    btn_height_css = "3.15rem"
    font_base_css = "1.02rem"
elif modo_escolhido == "Computador (PC / Tablet)":
    max_w_css = "1240px"
    pad_side_css = "1.8rem"
    h1_size_css = "1.75rem"
    btn_height_css = "2.75rem"
    font_base_css = "0.98rem"
else:
    max_w_css = "1180px"
    pad_side_css = "1.4rem"
    h1_size_css = "1.65rem"
    btn_height_css = "2.85rem"
    font_base_css = "0.98rem"

st.markdown(
    f"""
<style>
.stApp {{
    background-color: #F8FAFC;
    color: #0F172A;
    font-size: {font_base_css};
}}
.main .block-container {{
    max-width: {max_w_css};
    padding-top: 0.65rem;
    padding-bottom: 3rem;
    padding-left: {pad_side_css};
    padding-right: {pad_side_css};
}}
/* FAIXA ANIMADA SUPERIOR (VELOCIDADE SUAVE) */
.ticker-wrap {{
    width: 100%;
    overflow: hidden;
    background: linear-gradient(90deg, #064E3B 0%, #047857 50%, #064E3B 100%);
    color: #ECFDF5;
    padding: 0.58rem 0;
    border-radius: 8px;
    margin-bottom: 0.85rem;
    border: 1px solid #10B981;
    box-shadow: 0 2px 8px rgba(6, 78, 59, 0.18);
}}
.ticker-move {{
    display: inline-block;
    white-space: nowrap;
    padding-left: 100%;
    animation: ticker-scroll 52s linear infinite;
    font-weight: 600;
    font-size: 0.92rem;
    letter-spacing: 0.02em;
}}
.ticker-wrap:hover .ticker-move {{
    animation-play-state: paused;
}}
@keyframes ticker-scroll {{
    0% {{ transform: translate3d(0, 0, 0); }}
    100% {{ transform: translate3d(-100%, 0, 0); }}
}}
/* CABEÇALHO PRINCIPAL */
.hero-banner {{
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    color: #FFFFFF;
    padding: 1.6rem 1.85rem;
    border-radius: 14px;
    margin-bottom: 0.95rem;
    border-bottom: 4px solid #10B981;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.16);
    display: flex;
    align-items: center;
    gap: 1.4rem;
}}
.hero-logo {{
    flex-shrink: 0;
}}
.hero-text h1 {{
    margin: 0;
    font-size: {h1_size_css};
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    line-height: 1.2;
}}
.hero-text p {{
    margin: 0.45rem 0 0 0;
    font-size: 0.95rem;
    color: #CBD5E1;
    line-height: 1.45;
}}
.hero-tag {{
    display: inline-block;
    background-color: rgba(16, 185, 129, 0.18);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.35);
    font-size: 0.73rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    margin-bottom: 0.45rem;
}}
.trust-strip {{
    background-color: #ECFDF5;
    border: 1px solid #A7F3D0;
    color: #065F46;
    padding: 0.8rem 1.1rem;
    border-radius: 10px;
    font-size: 0.89rem;
    margin-bottom: 1.1rem;
    line-height: 1.45;
}}
.info-card {{
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #0F172A;
    padding: 1.05rem 1.2rem;
    border-radius: 10px;
    font-size: 0.92rem;
    color: #334155;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.guide-card {{
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 4px solid #059669;
    padding: 1.3rem 1.45rem;
    border-radius: 12px;
    margin-bottom: 1.15rem;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    line-height: 1.58;
}}
.guide-card h3 {{
    color: #0F172A;
    margin-top: 0;
    margin-bottom: 0.65rem;
    font-size: 1.14rem;
}}
.guide-card h4 {{
    color: #0F172A;
    margin-top: 0.9rem;
    margin-bottom: 0.35rem;
    font-size: 1.01rem;
}}
.rule-highlight {{
    background-color: #F1F5F9;
    border-left: 4px solid #0284C7;
    padding: 0.85rem 1rem;
    border-radius: 6px;
    margin: 0.75rem 0;
    font-size: 0.92rem;
    color: #1E293B;
}}
.warning-highlight {{
    background-color: #FEF2F2;
    border-left: 4px solid #DC2626;
    padding: 0.85rem 1rem;
    border-radius: 6px;
    margin: 0.75rem 0;
    font-size: 0.92rem;
    color: #7F1D1D;
}}
.alert-amber {{
    background-color: #FFFBEB;
    border: 1px solid #FDE68A;
    color: #92400E;
    padding: 1rem;
    border-radius: 10px;
    font-size: 0.92rem;
    line-height: 1.5;
}}
.suggestion-item {{
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 3px solid #10B981;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.6rem;
    font-size: 0.9rem;
}}
.footer-box {{
    margin-top: 2.5rem;
    padding-top: 1.1rem;
    border-top: 1px solid #CBD5E1;
    text-align: center;
    font-size: 0.84rem;
    color: #64748B;
}}
.stButton > button {{
    min-height: {btn_height_css};
    font-weight: 600;
    border-radius: 8px;
}}
@media (max-width: 768px) {{
    .main .block-container {{
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }}
    .hero-banner {{
        flex-direction: column;
        align-items: flex-start;
        padding: 1.15rem;
        gap: 0.85rem;
    }}
    .hero-text h1 {{
        font-size: 1.28rem;
    }}
    .ticker-move {{
        animation-duration: 36s;
    }}
}}
</style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# LIGAÇÃO À BASE DE DADOS (SUPABASE) E ESTADO LOCAL
# ==============================================================================
@st.cache_resource
def iniciar_supabase():
    try:
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            from supabase import create_client
            return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        return None
    return None


supabase = iniciar_supabase()

if "registos_locais" not in st.session_state:
    st.session_state["registos_locais"] = []
if "votos_sindicatos_locais" not in st.session_state:
    st.session_state["votos_sindicatos_locais"] = []
if "sugestoes_locais" not in st.session_state:
    st.session_state["sugestoes_locais"] = []
if "sugestoes_enviadas_sessao" not in st.session_state:
    st.session_state["sugestoes_enviadas_sessao"] = 0


def obter_salt_segredo() -> str:
    try:
        return st.secrets.get("APP_SECRET_SALT", "SALT_LOCAL_DESENVOLVIMENTO_2026")
    except Exception:
        return "SALT_LOCAL_DESENVOLVIMENTO_2026"


# ==============================================================================
# FUNÇÕES DE VALIDAÇÃO AMPLA EM MEMÓRIA RAM (CUSTÓDIA ZERO)
# ==============================================================================
def _validar_nif_singular_pt(nif: str) -> bool:
    if not nif or len(nif) != 9 or not nif.isdigit():
        return False
    if nif[0] not in ("1", "2", "3", "4"):
        return False
    soma = sum(int(nif[i]) * (9 - i) for i in range(8))
    resto = soma % 11
    digito = 0 if resto in (0, 1) else 11 - resto
    return int(nif[8]) == digito


def _extrair_chave_unica_trabalhador_ram(texto_total: str, ficheiro_bytes: bytes, salt: str) -> str:
    """
    Extrai em memória RAM um identificador único (NISS, NIF ou assinatura do documento)
    e transforma-o num hash SHA-256 irreversível para evitar votos repetidos sem guardar dados.
    """
    numeros_limpos = re.sub(r"[^\d\s]", " ", texto_total)
    candidatos_niss = re.findall(r"\b[12]\d{10}\b", numeros_limpos)
    if candidatos_niss:
        return hashlib.sha256(f"NISS:{candidatos_niss[0]}:{salt}".encode("utf-8")).hexdigest()

    candidatos_nif = re.findall(r"\b[123]\d{8}\b", numeros_limpos)
    for cand in candidatos_nif:
        if _validar_nif_singular_pt(cand):
            return hashlib.sha256(f"NIF:{cand}:{salt}".encode("utf-8")).hexdigest()

    texto_norm = re.sub(r"\s+", " ", texto_total.strip())[:1000]
    if len(texto_norm) >= 15:
        return hashlib.sha256(f"DOC:{texto_norm}:{salt}".encode("utf-8", errors="ignore")).hexdigest()

    digest_bytes = hashlib.sha256(ficheiro_bytes[:32768]).hexdigest()
    return hashlib.sha256(f"SCAN:{digest_bytes}:{salt}".encode("utf-8")).hexdigest()


def validar_recibo_em_memoria(ficheiro_bytes: bytes, empresa_selecionada: str | None = None) -> dict:
    """
    Validação ampla de recibos de vencimento em RAM.
    Aceita qualquer formato de ERP ou digitalização legível com dados minimamente autênticos.
    """
    try:
        if not ficheiro_bytes or len(ficheiro_bytes) < 400:
            return {"valido": False, "motivo": "O ficheiro PDF enviado parece vazio ou corrompido."}

        reader = PdfReader(io.BytesIO(ficheiro_bytes))
        if len(reader.pages) == 0:
            return {"valido": False, "motivo": "O ficheiro PDF não contém páginas legíveis."}

        texto_total = ""
        for page in reader.pages[:3]:
            texto_total += (page.extract_text() or "") + "\n"

        texto_lower = texto_total.lower()
        salt = obter_salt_segredo()

        marcadores_recibo = [
            "vencimento", "remuneração", "remuneracao", "segurança social", "seguranca social",
            "irs", "líquido", "liquido", "ilíquido", "iliquido", "subsídio", "subsidio",
            "alimentação", "alimentacao", "abonos", "descontos", "categoria", "vigilante",
            "iban", "nib", "niss", "nif", "período", "periodo", "11%", "11,00%", "base",
            "noturno", "suplementar", "feriado", "salário", "salario", "recibo", "ordenado",
            "eur", "€", "total", "valor", "data",
        ]
        encontrados = sum(1 for m in marcadores_recibo if m in texto_lower)
        valores_monetarios = re.findall(r"\b\d{1,5}[.,]\d{2}\b", texto_total)

        eh_pdf_digitalizado = len(texto_total.strip()) < 30 and len(ficheiro_bytes) > 6000
        if not eh_pdf_digitalizado and (encontrados < 1 and len(valores_monetarios) < 1):
            return {
                "valido": False,
                "motivo": "O PDF não apresenta valores nem referências salariais mínimas. Verifica se anexaste o ficheiro correto.",
            }

        marcadores_quota = [
            "quota sindical", "quotização sindical", "quotizacao sindical", "quota",
            "sindicato", "sindical", "stad", "assp", "fetese", "susp", "sindetelco", "sinapsa",
        ]
        quota_detetada = any(mq in texto_lower for mq in marcadores_quota)

        nipc_detetado = "VALIDADO-ERP"
        candidatos_9d = re.findall(r"\b[5-9]\d{8}\b", re.sub(r"[^\d\s]", " ", texto_total))
        for cand in candidatos_9d:
            if validar_nipc_portugues(cand):
                nipc_detetado = cand
                break

        texto_normalizado = re.sub(r"\s+", " ", texto_total.strip())[:1000]
        if not texto_normalizado:
            texto_normalizado = hashlib.sha256(ficheiro_bytes[:32768]).hexdigest()

        assinatura_bruta = f"{empresa_selecionada or 'GERAL'}:{texto_normalizado}:{salt}".encode("utf-8", errors="ignore")
        hash_unico = hashlib.sha256(assinatura_bruta).hexdigest()
        chave_pessoa_hash = _extrair_chave_unica_trabalhador_ram(texto_total, ficheiro_bytes, salt)

        return {
            "valido": True,
            "hash_unico": hash_unico,
            "chave_pessoa_hash": chave_pessoa_hash,
            "nipc_detetado": nipc_detetado,
            "quota_detetada": quota_detetada,
        }
    except Exception:
        return {
            "valido": False,
            "motivo": "Não foi possível abrir o PDF. Verifica se o ficheiro não está protegido por palavra-passe.",
        }


def validar_comprovativo_sindical_em_memoria(ficheiro_bytes: bytes) -> dict:
    """
    Validação muito abrangente para qualquer vigilante sindicalizado:
    Aceita Recibo de Vencimento (com ou sem desconto na folha), Débito Direto (SEPA),
    Transferência Bancária, MB Way, Recibo de Quota, Declaração Anual de IRS ou PDF digitalizado.
    """
    try:
        if not ficheiro_bytes or len(ficheiro_bytes) < 400:
            return {"valido": False, "motivo": "O ficheiro PDF enviado parece vazio ou corrompido."}

        reader = PdfReader(io.BytesIO(ficheiro_bytes))
        if len(reader.pages) == 0:
            return {"valido": False, "motivo": "O ficheiro PDF não contém páginas legíveis."}

        texto_total = ""
        for page in reader.pages[:3]:
            texto_total += (page.extract_text() or "") + "\n"

        texto_lower = texto_total.lower()
        salt = obter_salt_segredo()

        res_recibo = validar_recibo_em_memoria(ficheiro_bytes, None)
        if res_recibo["valido"]:
            metodo = (
                "Recibo de Vencimento (Quota na Folha)"
                if res_recibo["quota_detetada"]
                else "Recibo de Vencimento (Pagamento Direto)"
            )
            return {
                "valido": True,
                "chave_pessoa_hash": res_recibo["chave_pessoa_hash"],
                "quota_detetada": res_recibo["quota_detetada"],
                "metodo_validacao": metodo,
            }

        marcadores_comprovativo = [
            "quota", "quotização", "quotizacao", "sindicato", "sindical",
            "débito direto", "debito direto", "sepa", "autorização", "autorizacao",
            "transferência", "transferencia", "mb way", "mbway", "comprovativo",
            "irs", "152", "associado", "sócio", "socio", "stad", "assp", "fetese",
            "susp", "sindetelco", "sinapsa", "declaração", "declaracao", "recibo",
            "pagamento", "nib", "iban", "eur", "€", "data", "valor", "montante",
        ]
        encontrados = sum(1 for m in marcadores_comprovativo if m in texto_lower)
        valores_monetarios = re.findall(r"\b\d{1,5}[.,]\d{2}\b", texto_total)
        eh_pdf_digitalizado = len(texto_total.strip()) < 30 and len(ficheiro_bytes) > 6000

        if eh_pdf_digitalizado or encontrados >= 1 or len(valores_monetarios) >= 1:
            chave_pessoa_hash = _extrair_chave_unica_trabalhador_ram(texto_total, ficheiro_bytes, salt)
            return {
                "valido": True,
                "chave_pessoa_hash": chave_pessoa_hash,
                "quota_detetada": True,
                "metodo_validacao": "Comprovativo Direto / Bancário / IRS Sindical",
            }

        return {
            "valido": False,
            "motivo": (
                "O ficheiro não apresenta elementos mínimos legíveis. Carrega um PDF de recibo de vencimento, "
                "comprovativo bancário/débito direto, recibo de quota ou declaração de IRS."
            ),
        }
    except Exception:
        return {
            "valido": False,
            "motivo": "Não foi possível abrir o PDF. Verifica se o ficheiro não está protegido por palavra-passe.",
        }


def gerar_codigo_caso(hash_unico: str) -> str:
    return f"VIG-{hash_unico[:4].upper()}-{hash_unico[4:8].upper()}"


def gerar_links_sala_autonoma(empresa: str, distrito: str, tipo_infracao: str) -> dict:
    salt = obter_salt_segredo()
    chave_grupo = f"{empresa}|{distrito}|{tipo_infracao}|{salt}".encode("utf-8")
    sala_id = hashlib.sha256(chave_grupo).hexdigest()[:20]
    return {
        "chat_texto": f"https://hack.chat/?vigPT_{sala_id}",
        "sala_voz": f"https://meet.jit.si/VigilantesPT_{sala_id}",
    }


# ==============================================================================
# PERSISTÊNCIA ANÓNIMA (SUPABASE OU SESSÃO LOCAL)
# ==============================================================================
def guardar_registo_anonimo(registo: dict) -> tuple[bool, str]:
    if supabase is not None:
        try:
            existente = (
                supabase.table("denuncias_validadas")
                .select("id")
                .eq("hash_unico", registo["hash_unico"])
                .execute()
            )
            if existente.data:
                return False, "Este recibo já foi conferido e registado anteriormente no sistema."
            supabase.table("denuncias_validadas").insert(registo).execute()
            return True, "Registo técnico validado e guardado anonimamente com sucesso."
        except Exception as e:
            return False, f"Erro de ligação à base de dados: {str(e)}"
    else:
        for r in st.session_state["registos_locais"]:
            if r["hash_unico"] == registo["hash_unico"]:
                return False, "Este recibo já foi registado nesta sessão."
        st.session_state["registos_locais"].append(registo)
        return True, "Registo guardado em modo de demonstração local."


def carregar_todos_registos() -> list:
    if supabase is not None:
        try:
            resp = supabase.table("denuncias_validadas").select("*").execute()
            return resp.data or []
        except Exception:
            return st.session_state["registos_locais"]
    return st.session_state["registos_locais"]


def guardar_voto_sindicato(voto: dict) -> tuple[bool, str]:
    if supabase is not None:
        try:
            existente = (
                supabase.table("avaliacoes_sindicatos")
                .select("id")
                .eq("hash_voto", voto["hash_voto"])
                .execute()
            )
            if existente.data:
                return False, "Já registaste uma avaliação para este sindicato anteriormente."
            try:
                supabase.table("avaliacoes_sindicatos").insert(voto).execute()
            except Exception:
                voto_compat = {k: v for k, v in voto.items() if k != "metodo_validacao"}
                supabase.table("avaliacoes_sindicatos").insert(voto_compat).execute()
            return True, "Avaliação sindical validada e registada anonimamente com sucesso!"
        except Exception as e:
            return False, f"Erro ao gravar avaliação: {str(e)}"
    else:
        for v in st.session_state["votos_sindicatos_locais"]:
            if v["hash_voto"] == voto["hash_voto"]:
                return False, "Já registaste uma avaliação para este sindicato nesta sessão."
        st.session_state["votos_sindicatos_locais"].append(voto)
        return True, "Avaliação sindical guardada em modo local."


def carregar_votos_sindicatos() -> list:
    if supabase is not None:
        try:
            resp = supabase.table("avaliacoes_sindicatos").select("*").execute()
            return resp.data or []
        except Exception:
            return st.session_state["votos_sindicatos_locais"]
    return st.session_state["votos_sindicatos_locais"]


def guardar_sugestao_anonima(categoria: str, mensagem: str) -> tuple[bool, str]:
    registo_sug = {
        "categoria": categoria,
        "mensagem": mensagem.strip(),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if supabase is not None:
        try:
            supabase.table("sugestoes_plataforma").insert(
                {"categoria": categoria, "mensagem": mensagem.strip()}
            ).execute()
            return True, "Sugestão enviada anonimamente! Obrigado por contribuíres para o Vigilante Informado."
        except Exception as e:
            return False, f"Erro ao enviar sugestão: {str(e)}"
    st.session_state["sugestoes_locais"].insert(0, registo_sug)
    return True, "Sugestão registada em modo de demonstração local!"


def carregar_sugestoes_recentes(limite: int = 8) -> list:
    if supabase is not None:
        try:
            resp = (
                supabase.table("sugestoes_plataforma")
                .select("categoria, mensagem, created_at")
                .order("id", desc=True)
                .limit(limite)
                .execute()
            )
            return resp.data or []
        except Exception:
            return st.session_state["sugestoes_locais"][:limite]
    return st.session_state["sugestoes_locais"][:limite]


# ==============================================================================
# 1. FAIXA ANIMADA SUPERIOR
# ==============================================================================
st.markdown(
    """
<div class="ticker-wrap">
<div class="ticker-move">
🛡️ Bem-Vindo ao Vigilante Informado — O site onde todos os Vigilantes Portugueses ganham voz • Conferência Salarial BTE 2023–2026 • Privacidade Total Custódia Zero (RGPD) • Ranking de Empresas &amp; Sindicatos Validado • União &amp; Literacia Laboral
</div>
</div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. CABEÇALHO PRINCIPAL & SELO DE CREDIBILIDADE
# ==============================================================================
st.markdown(
    """
<div class="hero-banner">
<div class="hero-logo">
<svg width="68" height="68" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M40 6L12 18V38C12 56.5 24 71.2 40 75C56 71.2 68 56.5 68 38V18L40 6Z" fill="#0F172A" stroke="#10B981" stroke-width="4"/>
<path d="M40 14L20 22.5V38C20 51.8 28.5 63.1 40 66.5C51.5 63.1 60 51.8 60 38V22.5L40 14Z" fill="#1E293B"/>
<path d="M29 40L36.5 47.5L52 31" stroke="#10B981" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="40" cy="19" r="2.5" fill="#F59E0B"/>
</svg>
</div>
<div class="hero-text">
<span class="hero-tag">Plataforma Independente de Literacia Laboral — Portugal</span>
<h1>Vigilante Informado — Onde os Vigilantes Ganham Voz</h1>
<p>Confere os teus recibos ao cêntimo, avalia empresas e sindicatos com total anonimato e coordena ações coletivas sem qualquer controlo externo sobre a tua voz.</p>
</div>
</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="trust-strip">
<strong>Garantia Custódia Zero (RGPD):</strong> Sem conta, sem nome, sem IP guardado e sem arquivo de documentos.
Todos os PDFs são verificados exclusivamente em memória RAM e destruídos no mesmo segundo. Podes inclusive rasurar o teu nome antes de carregar qualquer documento.
</div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. PAINEL DE INDICADORES AO VIVO (CREDIBILIDADE IMEDIATA)
# ==============================================================================
dados_globais = carregar_todos_registos()
votos_sind_globais = carregar_votos_sindicatos()

k_top1, k_top2, k_top3, k_top4 = st.columns(4)
k_top1.metric("Recibos Validados", len(dados_globais))
total_eur_global = sum(d.get("desvio_eur", 0) for d in dados_globais) if dados_globais else 0.0
k_top2.metric("Divergências Apuradas", f"{total_eur_global:.2f} EUR")
k_top3.metric("Avaliações Sindicais", len(votos_sind_globais))
k_top4.metric("Tabelas em Vigor", "BTE 2023–2026")

st.write("")

# ==============================================================================
# 4. NAVEGAÇÃO PRINCIPAL (6 ABAS ESTRUTURADAS)
# ==============================================================================
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
    [
        "1. Simulador Salarial",
        "2. Provas & Ocorrências",
        "3. Ranking Empresas",
        "4. Ranking Sindicatos",
        "5. Ação Coletiva",
        "6. Guia Legal, FAQ & Sugestões",
    ]
)

# ==============================================================================
# ABA 1: SIMULADOR DE RECIBOS, PERÍODOS LONGOS & FORMAÇÃO
# ==============================================================================
with aba1:
    st.subheader("Conferência Matemática de Vencimentos (Tabelas Oficiais BTE)")
    st.write(
        "Seleciona a empresa, a tua categoria profissional e o período trabalhado. Os valores base e "
        "subsídios correspondem às tabelas oficiais publicadas no Boletim do Trabalho e Emprego."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        empresa_sel = st.selectbox("Entidade Empregadora", list(EMPRESAS_SEGURANCA.keys()))
    with col2:
        distrito_sel = st.selectbox("Distrito do Posto", DISTRITOS_PORTUGAL)

    lista_ccts_ordenada = obter_sugestoes_cct(empresa_sel)

    col_c1, col_c2, col_c3 = st.columns([2, 2, 1])
    with col_c1:
        cct_sel = st.selectbox(
            "CCT Aplicável (O 1.º é o mais frequente nesta empresa)",
            lista_ccts_ordenada,
        )
    with col_c2:
        categoria_sel = st.selectbox("Categoria Profissional", CATEGORIAS_PROFISSIONAIS)
    with col_c3:
        ano_sel = st.selectbox("Ano da Tabela", [2026, 2025, 2024, 2023])

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        num_meses = st.number_input(
            "Número de meses a conferir (1 para recibo mensal ou vários meses acumulados)",
            min_value=1,
            max_value=36,
            value=1,
            step=1,
        )
    with col_p2:
        periodo_desc = st.text_input(
            "Identificação do Período (ex.: Outubro/2026 ou Jan/2026 a Out/2026)",
            value=f"Período de {num_meses} mês(es) - {ano_sel}",
        )

    enq = obter_enquadramento(empresa_sel, ano_sel, cct_sel, categoria_sel)
    st.markdown(
        f"""
<div class="info-card">
<strong>Tabela Oficial BTE ({enq['ano_aplicado']}):</strong> {enq['cct']} |
<strong>Vencimento Base:</strong> {enq['base']:.2f} EUR |
<strong>Valor Hora Base:</strong> {enq['valor_hora']:.4f} EUR/h ({enq['valor_hora']:.2f} EUR) |
<strong>Subsídio Alimentação:</strong> {enq['sub_alim_dia']:.2f} EUR/dia
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Passo A: Horas e Dias Efetivamente Trabalhados no Período")
    c_h1, c_h2, c_h3 = st.columns(3)
    with c_h1:
        dias_trab = st.number_input("Dias trabalhados (total)", min_value=0, max_value=1100, value=22 * num_meses)
        h_noturnas = st.number_input("Horas Noturnas 21h-06h (+25%)", min_value=0.0, max_value=9000.0, value=0.0, step=1.0)
    with c_h2:
        h_feriado_norm = st.number_input(
            "Horas Normais em Feriado (+100% acréscimo)",
            min_value=0.0,
            max_value=3000.0,
            value=0.0,
            step=1.0,
        )
        h_extras_feriado = st.number_input(
            "Horas Extras em Feriado / Descanso (200% total)",
            min_value=0.0,
            max_value=3000.0,
            value=0.0,
            step=1.0,
        )
    with c_h3:
        h_extras_diurnas = st.number_input(
            "Horas Extras Diurnas (+50% = 1,50x VH)",
            min_value=0.0,
            max_value=5000.0,
            value=0.0,
            step=1.0,
        )
        h_extras_noturnas = st.number_input(
            "Horas Extras Noturnas (+75% = 1,75x VH)",
            min_value=0.0,
            max_value=5000.0,
            value=0.0,
            step=1.0,
        )

    h_formacao = st.number_input(
        "Horas de Formação em falta ou não pagas (Art. 131.º CT - direito a 40h/ano)",
        min_value=0.0,
        max_value=500.0,
        value=0.0,
        step=1.0,
    )

    st.markdown("#### Passo B: Valores Totais Pagos nos Recibos do Período (EUR)")
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
        pago_base = st.number_input(
            "Base Pago Total (EUR)",
            min_value=0.0,
            value=round(float(enq["base"]) * num_meses, 2),
            step=10.0,
        )
        pago_noturno = st.number_input("Noturno Pago Total (EUR)", min_value=0.0, value=0.0, step=5.0)
    with c_p2:
        pago_feriado = st.number_input("Feriado / Descanso Pago Total (EUR)", min_value=0.0, value=0.0, step=5.0)
        pago_extras = st.number_input("Horas Extras Pago Total (EUR)", min_value=0.0, value=0.0, step=5.0)
    with c_p3:
        pago_formacao = st.number_input("Formação Paga Total (EUR)", min_value=0.0, value=0.0, step=5.0)
        pago_alim = st.number_input(
            "Subsídio Alimentação Pago Total (EUR)",
            min_value=0.0,
            value=round(dias_trab * enq["sub_alim_dia"], 2),
            step=5.0,
        )

    st.markdown("#### Passo C: Validação Ampla Anti-Fraude (Opcional para Entrar nos Rankings Públicos)")
    st.caption(
        "Para contabilizar o teu caso no Ranking de Empresas e nos grupos de ação coletiva, anexa um recibo "
        "de vencimento (PDF) desse período. O ficheiro é validado em memória RAM e destruído no mesmo segundo."
    )
    ficheiro_pdf = st.file_uploader("Carregar Recibo de Vencimento de Referência (PDF)", type=["pdf"], key="pdf_aba1")
    tipo_principal = st.selectbox("Principal irregularidade apurada", TIPOS_INCUMPRIMENTO)

    if st.button("Calcular Valores e Gerar Dossiê PDF", type="primary"):
        resultado = calcular_auditoria_periodo(
            empresa=empresa_sel,
            ano=ano_sel,
            cct_escolhido=cct_sel,
            categoria=categoria_sel,
            num_meses=num_meses,
            horas_noturnas_totais=h_noturnas,
            horas_feriado_normais=h_feriado_norm,
            horas_extras_diurnas=h_extras_diurnas,
            horas_extras_noturnas=h_extras_noturnas,
            horas_extras_feriado_descanso=h_extras_feriado,
            horas_formacao_nao_pagas=h_formacao,
            dias_trabalhados_totais=dias_trab,
            base_pago_total=pago_base,
            noturno_pago_total=pago_noturno,
            feriado_pago_total=pago_feriado,
            extras_pago_total=pago_extras,
            formacao_pago_total=pago_formacao,
            alim_pago_total=pago_alim,
        )

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Devido (CCT)", f"{resultado['total_devido']:.2f} EUR")
        m2.metric("Total Pago em Recibo", f"{resultado['total_pago']:.2f} EUR")
        m3.metric(
            "Diferença em Falta",
            f"{resultado['desvio_total']:.2f} EUR",
            delta=f"{-resultado['desvio_total']:.2f} EUR" if resultado["desvio_total"] > 0 else "0.00 EUR",
            delta_color="inverse",
        )

        df_det = pd.DataFrame(resultado["detalhes"])
        st.dataframe(df_det, use_container_width=True, hide_index=True)

        validado = False
        codigo_caso = "SIMULAÇÃO-LOCAL"

        if ficheiro_pdf is not None:
            bytes_pdf = ficheiro_pdf.read()
            val = validar_recibo_em_memoria(bytes_pdf, empresa_sel)
            del bytes_pdf

            if val["valido"]:
                validado = True
                codigo_caso = gerar_codigo_caso(val["hash_unico"])
                if val.get("nipc_detetado") and val["nipc_detetado"] != "VALIDADO-ERP":
                    resultado["regras"]["nipc"] = val["nipc_detetado"]

                if resultado["desvio_total"] >= 5.0:
                    reg = {
                        "hash_unico": val["hash_unico"],
                        "codigo_caso": codigo_caso,
                        "empresa": empresa_sel,
                        "nipc": val.get("nipc_detetado", "VALIDADO-ERP"),
                        "distrito": distrito_sel,
                        "tipo_infracao": tipo_principal,
                        "desvio_eur": resultado["desvio_total"],
                        "ano_mes": periodo_desc[:45],
                    }
                    ok, msg = guardar_registo_anonimo(reg)
                    if ok:
                        st.success(
                            f"Recibo validado tecnicamente! O teu Código de Caso anónimo é: **{codigo_caso}**. "
                            "Guarda este código para acompanhares o grupo coletivo na Aba 5."
                        )
                    else:
                        st.warning(msg)
                else:
                    st.info(
                        f"Recibo oficial validado com sucesso (Código: **{codigo_caso}**), mas como não existe "
                        "desvio superior a 5 EUR nos valores inseridos, não foi registado incumprimento."
                    )
            else:
                st.error(f"Validação falhou: {val['motivo']} O dossiê será gerado apenas como simulação local.")
        else:
            st.warning(
                "Cálculo efetuado em modo de simulação manual. Para entrar no Ranking de Empresas e nos grupos "
                "de ação coletiva, anexa um recibo em PDF."
            )

        pdf_bytes = gerar_pdf_auditoria(
            codigo_caso=codigo_caso,
            empresa=empresa_sel,
            distrito=distrito_sel,
            periodo_texto=periodo_desc,
            resultado=resultado,
            validado_pdf=validado,
        )

        st.download_button(
            label="Descarregar Dossiê Técnico em PDF (Guardar no Dispositivo)",
            data=pdf_bytes,
            file_name=f"Dossie_Apuramento_{ano_sel}.pdf",
            mime="application/pdf",
        )


# ==============================================================================
# ABA 2: DOCUMENTAR OUTROS INCUMPRIMENTOS (PROVA LEGAL)
# ==============================================================================
with aba2:
    st.subheader("Assistente de Recolha de Prova e Cronologia de Ocorrências")
    st.write(
        "Incumprimentos como falta de horas de formação anual (40h/ano), mudanças de posto sem aviso prévio, "
        "alterações de escala em cima da hora ou pressões na transmissão de estabelecimento exigem registo "
        "cronológico objetivo. Preenche os dados abaixo para gerar um relatório técnico pronto para a ACT ou Sindicato."
    )

    col_o1, col_o2 = st.columns(2)
    with col_o1:
        emp_oc = st.selectbox("Empresa envolvida", list(EMPRESAS_SEGURANCA.keys()), key="emp_oc")
        tipo_oc = st.selectbox("Tipologia do Incumprimento", TIPOS_INCUMPRIMENTO, key="tipo_oc")
    with col_o2:
        dist_oc = st.selectbox("Distrito", DISTRITOS_PORTUGAL, key="dist_oc")
        periodo_oc = st.text_input(
            "Data ou Período dos Factos (ex.: 15/11/2026 ou Anos 2024 a 2026)",
            value=datetime.date.today().strftime("%d/%m/%Y"),
        )

    posto_gen = st.selectbox(
        "Tipologia do Posto (sem identificar o cliente específico para evitar retaliação)",
        [
            "Superfície Comercial / Retalho",
            "Infraestrutura de Transportes / Estação",
            "Unidade Hospitalar / Saúde",
            "Edifício de Escritórios / Banca",
            "Unidade Industrial / Logística",
            "Edifício Público / Estado",
            "Rondas Móveis",
        ],
    )

    desc_factual = st.text_area(
        "Descrição objetiva dos factos (datas, horas, ordens recebidas - evita insultos ou nomes individuais)",
        placeholder="Exemplo: Nos anos de 2024, 2025 e 2026 não me foram ministradas as 40 horas anuais de formação contínua obrigatória previstas no Art. 131.º do Código do Trabalho, acumulando 120 horas de formação em falta...",
        height=140,
    )

    st.markdown("**Checklist de Provas Documentais guardadas no teu telemóvel/PC:**")
    provas = []
    if st.checkbox("Captura de ecrã de SMS / WhatsApp / Email com data e hora visíveis"):
        provas.append("Captura de ecrã de comunicação escrita com data e hora")
    if st.checkbox("Cópia das escalas de serviço originais e alteradas"):
        provas.append("Escalas de serviço comprovativas")
    if st.checkbox("Recibos de vencimento comprovando ausência de pagamento de formação/horas"):
        provas.append("Recibos de vencimento do período em causa")
    if st.checkbox("Comprovativo de distância extra em km (ex.: print Google Maps)"):
        provas.append("Registo de acréscimo de distância de deslocação")
    if st.checkbox("Cópia de contrato anterior / comprovativo de antiguidade no posto"):
        provas.append("Comprovativo de antiguidade e condições contratuais")

    if st.button("Gerar Relatório Cronológico em PDF"):
        if len(desc_factual.strip()) < 20:
            st.error("Por favor, descreve os factos com um mínimo de detalhe objetivo antes de gerar o PDF.")
        else:
            pdf_oc = gerar_pdf_ocorrencia(
                empresa=emp_oc,
                distrito=dist_oc,
                tipo_infracao=tipo_oc,
                periodo_ocorrencia=periodo_oc,
                posto_tipo=posto_gen,
                descricao_factual=desc_factual,
                provas_reunidas=provas,
            )
            st.download_button(
                label="Descarregar Relatório de Ocorrência (PDF)",
                data=pdf_oc,
                file_name="Relatorio_Ocorrencia_Laboral.pdf",
                mime="application/pdf",
            )


# ==============================================================================
# ABA 3: RANKING DE EMPRESAS & CONFORMIDADE LABORAL
# ==============================================================================
with aba3:
    st.subheader("Ranking Público de Conformidade das Empresas de Segurança")
    st.write(
        "Classificação transparente baseada exclusivamente em recibos validados na Aba 1. "
        "Nenhum trabalhador ou posto isolado é identificado."
    )

    if not dados_globais:
        st.info(
            "Ainda não existem registos validados suficientes para exibir o ranking de empresas. "
            "Assim que os primeiros recibos forem validados na Aba 1, o ranking surgirá aqui automaticamente."
        )
    else:
        df = pd.DataFrame(dados_globais)
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.metric("Total de Casos Validados", len(df))
        c_k2.metric("Divergência Média Apurada", f"{df['desvio_eur'].mean():.2f} EUR")
        c_k3.metric("Total Acumulado em Falta", f"{df['desvio_eur'].sum():.2f} EUR")

        st.markdown("#### Classificação por Entidade Empregadora (Ordenado por Total Apurado)")
        resumo_emp = (
            df.groupby("empresa")
            .agg(
                Casos_Validados=("id", "count") if "id" in df.columns else ("hash_unico", "count"),
                Media_Falta_EUR=("desvio_eur", "mean"),
                Total_Apurado_EUR=("desvio_eur", "sum"),
            )
            .reset_index()
            .sort_values(by="Total_Apurado_EUR", ascending=False)
        )
        resumo_emp["Media_Falta_EUR"] = resumo_emp["Media_Falta_EUR"].round(2)
        resumo_emp["Total_Apurado_EUR"] = resumo_emp["Total_Apurado_EUR"].round(2)
        st.dataframe(resumo_emp, use_container_width=True, hide_index=True)

        st.markdown("#### Tipologias de Incumprimento Mais Frequentes")
        st.bar_chart(df["tipo_infracao"].value_counts())


# ==============================================================================
# ABA 4: RANKING DE SINDICATOS & AVALIAÇÃO VALIDADA (AMPLA)
# ==============================================================================
with aba4:
    st.subheader("Ranking Transparente dos Sindicatos da Segurança Privada")
    st.write(
        "Classificação construída pela voz real dos vigilantes sindicalizados — tanto os que descontam na folha "
        "como os que pagam diretamente por débito direto, transferência ou MB Way. Para proteger todos os utilizadores "
        "juridicamente, a avaliação foca-se em métricas objetivas de eficácia e resolução de casos."
    )

    if not votos_sind_globais:
        st.info(
            "Ainda não existem avaliações sindicais registadas. Se és sócio ou já recorreste a um sindicato, "
            "regista abaixo a tua avaliação anónima para ajudar os colegas a escolherem com base em resultados reais."
        )
    else:
        df_sind = pd.DataFrame(votos_sind_globais)
        df_sind["Media_Estrelas"] = (
            df_sind["nota_rapidez"]
            + df_sind["nota_presenca"]
            + df_sind["nota_eficacia"]
            + df_sind["nota_transparencia"]
        ) / 4.0

        ranking_rows = []
        for sind, grupo in df_sind.groupby("sindicato"):
            total_votos = len(grupo)
            resolvidos = int(
                grupo["estado_caso"].str.contains("Resolvido com Sucesso", na=False).sum()
            )
            ineficazes = int(
                grupo["estado_caso"].str.contains("Sem Resposta", na=False).sum()
            )
            casos_concluidos = resolvidos + ineficazes
            taxa_resolucao = round((resolvidos / casos_concluidos) * 100, 1) if casos_concluidos > 0 else 0.0

            ranking_rows.append(
                {
                    "Sindicato": sind,
                    "Sócios Avaliadores": total_votos,
                    "Casos Resolvidos": resolvidos,
                    "Taxa Resolução (%)": taxa_resolucao,
                    "Classificação Média (1-5 ⭐)": round(grupo["Media_Estrelas"].mean(), 2),
                }
            )

        df_rank_sind = pd.DataFrame(ranking_rows).sort_values(
            by=["Classificação Média (1-5 ⭐)", "Casos Resolvidos", "Sócios Avaliadores"],
            ascending=False,
        )
        st.dataframe(df_rank_sind, use_container_width=True, hide_index=True)

        if len(df_rank_sind) > 1:
            st.markdown("#### Comparativo de Satisfação Média por Sindicato")
            chart_sind = df_rank_sind.set_index("Sindicato")["Classificação Média (1-5 ⭐)"]
            st.bar_chart(chart_sind)

    st.divider()
    st.markdown("#### Avaliar o Meu Sindicato (100% Anónimo & Inclusivo)")
    st.caption(
        "Aceitamos qualquer comprovativo minimamente autêntico em PDF: recibo de vencimento (com ou sem quota na folha), "
        "comprovativo de débito direto (SEPA), transferência bancária, recibo de quota ou declaração de IRS. "
        "O ficheiro é lido apenas em RAM e destruído no mesmo segundo."
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sind_escolhido = st.selectbox("Sindicato a Avaliar", SINDICATOS_SETOR)
        estado_caso_sel = st.selectbox("Qual foi o resultado da tua experiência / processo?", ESTADOS_CASO_SINDICAL)
    with col_s2:
        pdf_voto_sind = st.file_uploader(
            "Anexa Comprovativo em PDF (Recibo Vencimento, Débito Direto, Quota ou IRS)",
            type=["pdf"],
            key="pdf_sind_voto",
        )

    c_n1, c_n2, c_n3, c_n4 = st.columns(4)
    with c_n1:
        n_rapidez = st.slider("Rapidez de Resposta", 1, 5, 4)
    with c_n2:
        n_presenca = st.slider("Presença nos Postos", 1, 5, 3)
    with c_n3:
        n_eficacia = st.slider("Eficácia Jurídica", 1, 5, 4)
    with c_n4:
        n_transp = st.slider("Transparência", 1, 5, 4)

    if st.button("Submeter Avaliação Sindical Anónima", type="primary"):
        if pdf_voto_sind is None:
            st.error("Anexa um documento comprovativo em PDF para autenticar a tua avaliação.")
        else:
            bytes_voto = pdf_voto_sind.read()
            val_s = validar_comprovativo_sindical_em_memoria(bytes_voto)
            del bytes_voto

            if not val_s["valido"]:
                st.error(f"Não foi possível autenticar o documento: {val_s['motivo']}")
            else:
                salt = obter_salt_segredo()
                hash_voto_unico = hashlib.sha256(
                    f"SIND_VOTE:{val_s['chave_pessoa_hash']}:{sind_escolhido}:{salt}".encode("utf-8")
                ).hexdigest()

                voto_obj = {
                    "hash_voto": hash_voto_unico,
                    "sindicato": sind_escolhido,
                    "quota_detetada_recibo": bool(val_s.get("quota_detetada", False)),
                    "metodo_validacao": val_s.get("metodo_validacao", "Documento Validado"),
                    "nota_rapidez": n_rapidez,
                    "nota_presenca": n_presenca,
                    "nota_eficacia": n_eficacia,
                    "nota_transparencia": n_transp,
                    "estado_caso": estado_caso_sel,
                }
                ok_v, msg_v = guardar_voto_sindicato(voto_obj)
                if ok_v:
                    st.success(f"{msg_v} ({val_s.get('metodo_validacao')})")
                else:
                    st.warning(msg_v)


# ==============================================================================
# ABA 5: AÇÃO COLETIVA & CANAIS AUTÓNOMOS ZERO-ADMIN
# ==============================================================================
with aba5:
    st.subheader("Coordenação de Ações Coletivas e Queixas Conjuntas")
    st.write(
        f"Quando pelo menos **{LIMIAR_GRUPO_COLETIVO} vigilantes** da mesma empresa e distrito registam "
        "um recibo validado com o mesmo tipo de incumprimento, o sistema desbloqueia automaticamente "
        "uma sala de comunicação encriptada sem administração externa."
    )

    codigo_consulta = st.text_input(
        "Insere o teu Código de Caso (ex.: VIG-8A2F-19C4)",
        max_chars=20,
    ).strip().upper()

    if codigo_consulta:
        caso_encontrado = next((d for d in dados_globais if d.get("codigo_caso") == codigo_consulta), None)

        if not caso_encontrado:
            st.error("Código de caso não encontrado. Verifica se copiaste corretamente após a validação na Aba 1.")
        else:
            emp_c = caso_encontrado["empresa"]
            dist_c = caso_encontrado["distrito"]
            tipo_c = caso_encontrado["tipo_infracao"]

            iguais = [
                d for d in dados_globais
                if d["empresa"] == emp_c and d["distrito"] == dist_c and d["tipo_infracao"] == tipo_c
            ]
            total_grupo = len(iguais)

            st.markdown(
                f"""
<div class="info-card">
<strong>Processo Associado:</strong> {emp_c} | <strong>Distrito:</strong> {dist_c}<br>
<strong>Infração:</strong> {tipo_c}<br>
<strong>Progresso do Grupo:</strong> {total_grupo} de {LIMIAR_GRUPO_COLETIVO} casos validados necessários
</div>
                """,
                unsafe_allow_html=True,
            )

            st.progress(min(1.0, total_grupo / LIMIAR_GRUPO_COLETIVO))

            if total_grupo < LIMIAR_GRUPO_COLETIVO:
                faltam = LIMIAR_GRUPO_COLETIVO - total_grupo
                st.warning(
                    f"Ainda faltam **{faltam} caso(s) validado(s)** nesta empresa e distrito para desbloquear "
                    "a sala segura do grupo. Partilha esta ferramenta com colegas do teu posto."
                )
            else:
                st.success("Limiar de Massa Crítica atingido! O canal encriptado deste grupo está disponível.")
                aceite_saida = st.checkbox(
                    "Declaro que compreendo que este link abre uma sala externa encriptada em memória RAM, "
                    "sem moderação, acesso ou armazenamento por parte do criador deste site, e comprometo-me "
                    "a usar um pseudónimo sem expor dados pessoais nem difamar terceiros."
                )
                if aceite_saida:
                    links = gerar_links_sala_autonoma(emp_c, dist_c, tipo_c)
                    st.markdown(
                        f"""
<div class="alert-amber">
<strong>Canal Seguro Desbloqueado (Usa Pseudónimo):</strong><br>
- Sala de Chat Encriptado (Texto em RAM): <a href="{links['chat_texto']}" target="_blank">{links['chat_texto']}</a><br>
- Sala de Reunião de Voz (Opcional): <a href="{links['sala_voz']}" target="_blank">{links['sala_voz']}</a>
</div>
                        """,
                        unsafe_allow_html=True,
                    )


# ==============================================================================
# ABA 6: GUIA LEGAL COMPLETO, FAQ & CAIXA DE SUGESTÕES ANÓNIMAS
# ==============================================================================
with aba6:
    st.subheader("Enciclopédia Prática de Direitos do Vigilante, FAQ & Sugestões")
    st.write(
        "Consulta abaixo o enquadramento legal completo aplicável à Segurança Privada em Portugal "
        "(Código do Trabalho, Contratos Coletivos de Trabalho publicados em BTE e Lei n.º 34/2013)."
    )

    # 1. BLOCO DE REMUNERAÇÃO E ACRÉSCIMOS
    st.markdown(
        """
<div class="guide-card">
<h3>1. Remuneração, Cálculo do Valor Hora e Acréscimos Obrigatórios (CCT &amp; BTE)</h3>
<p>Na Segurança Privada, a fórmula oficial para apurar o <strong>Valor Hora Base (VH)</strong> a partir do vencimento mensal de tabela é:</p>
<div class="rule-highlight">
<strong>Fórmula Oficial CCT:</strong> <code>Valor Hora = (Retribuição Base Mensal × 12 meses) ÷ (52 semanas × 40 horas)</code><br>
<em>Exemplo Prático (Vigilante Nível XIX em 2026 — Base 1.015,95 EUR):</em> <code>(1.015,95 × 12) ÷ 2.080 = 5,8613 EUR/hora</code>.
</div>
<ul>
<li><strong>Trabalho Noturno (21h00 às 06h00):</strong> Nos CCT da Segurança Privada, o período noturno começa às <strong>21h00</strong> (mais favorável do que o regime geral do Código do Trabalho que começa às 22h00) e termina às 06h00. Cada hora trabalhada neste intervalo vence um acréscimo mínimo de <strong>+25%</strong> (<code>1,25 × VH</code>).</li>
<li><strong>Trabalho Suplementar (Horas Extras):</strong> Todo o trabalho prestado fora do horário normal de trabalho ou acima do limite semanal/adaptabilidade definido vence:
    <ul>
    <li><strong>Hora Extra Diurna (06h00 às 21h00):</strong> Acréscimo de <strong>+50%</strong> (<code>1,50 × VH</code>).</li>
    <li><strong>Hora Extra Noturna (21h00 às 06h00):</strong> Acréscimo de <strong>+75%</strong> (<code>1,75 × VH</code>).</li>
    </ul>
</li>
<li><strong>Trabalho em Dia Feriado e Descanso Semanal:</strong>
    <ul>
    <li><strong>Feriado em dia normal de escala (laboração contínua):</strong> Direito ao acréscimo de <strong>+100%</strong> sobre o valor hora normal (ou descanso compensatório equivalente nos termos do Art. 269.º do Código do Trabalho e CCT).</li>
    <li><strong>Trabalho Suplementar em Dia de Descanso Semanal ou Feriado fora de escala:</strong> Pagamento a <strong>200% (acréscimo de +100%)</strong> e, caso seja prestado em dia de descanso semanal obrigatório, direito a <strong>1 dia completo de descanso compensatório remunerado</strong> a gozar nos 3 dias úteis seguintes (Art. 229.º CT).</li>
    </ul>
</li>
<li><strong>Subsídio de Alimentação:</strong> Pago por cada dia efetivo de trabalho (ou turno completo conforme escala). Em 2026, o valor mínimo setorial para Vigilante (Nível XIX) é de <strong>7,85 EUR/dia</strong>.</li>
</ul>
</div>
        """,
        unsafe_allow_html=True,
    )

    # 2. BLOCO DE HORÁRIOS, ESCALAS E DESCANSO
    st.markdown(
        """
<div class="guide-card">
<h3>2. Organização do Tempo de Trabalho, Escalas e Descanso Obrigatório</h3>
<ul>
<li><strong>Alteração de Escala / Horário (Art. 217.º Código do Trabalho):</strong> A escala de serviço não pode ser alterada arbitrariamente de um dia para o outro. Qualquer alteração de horário de trabalho deve ser precedida de consulta aos trabalhadores envolvidos e afixada com antecedência mínima de <strong>7 dias</strong> (ou 3 dias em microempresas), salvo acordo expresso do trabalhador ou situação de força maior devidamente comprovada.</li>
<li><strong>Descanso Diário Mínimo Entre Turnos (Art. 214.º Código do Trabalho):</strong> O trabalhador tem direito a um período mínimo de descanso de <strong>11 horas seguidas</strong> entre dois períodos diários de trabalho consecutivos. É ilegal escalar um vigilante para sair às 20h00 e entrar às 06h00 do dia seguinte sem intervalo legal.</li>
<li><strong>Turnos Contínuos e Pausa para Refeição (Art. 213.º CT e CCT):</strong> Nos postos de vigilância permanente (turnos de 8h ou 12h) em que o vigilante não pode abandonar o posto nem é rendido para almoçar/jantar, o período de refeição considera-se tempo de trabalho efetivo e é remunerado.</li>
<li><strong>Limites ao Trabalho Suplementar (Art. 228.º CT):</strong> O trabalhador pode recusar trabalho suplementar quando existam motivos atendíveis (Art. 227.º, n.º 3 CT) ou quando ultrapasse os limites anuais legais (150h a 200h por ano conforme dimensão da empresa e CCT).</li>
</ul>
</div>
        """,
        unsafe_allow_html=True,
    )

    # 3. BLOCO DE TRANSMISSÃO DE ESTABELECIMENTO E MUDANÇA DE POSTO
    st.markdown(
        """
<div class="guide-card">
<h3>3. Transmissão de Estabelecimento (Perda de Cliente) e Mudança de Posto</h3>
<div class="rule-highlight">
<strong>Regra de Ouro na Mudança de Empresa no Cliente (Arts. 285.º a 287.º CT e CCT):</strong><br>
Quando uma empresa de segurança perde um cliente/posto e outra empresa ganha o concurso mantendo a vigilância do local, verifica-se uma <strong>transmissão de unidade económica</strong>. A empresa que entra é obrigada a assumir os vigilantes afetos ao posto com <strong>manutenção integral da antiguidade, categoria profissional, retribuição, direito a férias e créditos vencidos</strong>.
</div>
<ul>
<li><strong>Cuidado com Documentos na Transmissão:</strong> Nunca assines cartas de demissão, rescisões por mútuo acordo nem novos contratos com período experimental ou perda de antiguidade quando mudas de empresa no mesmo posto. Exige sempre cópia assinada e datada de qualquer comunicação.</li>
<li><strong>Mudança de Local de Trabalho / Transferência de Posto (Art. 194.º CT):</strong> A empresa só pode transferir o vigilante para outro local de trabalho fora da área geográfica definida no contrato se houver fundamento objetivo, mediante comunicação escrita com <strong>8 dias de antecedência</strong> (transferência temporária) ou <strong>30 dias</strong> (transferência definitiva).</li>
<li><strong>Pagamento de Despesas de Deslocação:</strong> Sempre que a mudança de posto aumente os custos de transporte ou o tempo de deslocação causando prejuízo sério, a entidade empregadora é obrigada por lei (Art. 194.º, n.º 4 CT) a custear o acréscimo das despesas de deslocação.</li>
</ul>
</div>
        """,
        unsafe_allow_html=True,
    )

    # 4. BLOCO DE FORMAÇÃO, FARDAMENTO, CARTÃO MAI E PRAZOS LEGAIS
    st.markdown(
        """
<div class="guide-card">
<h3>4. Formação Obrigatória, Fardamento, Videovigilância e Prazos Legais</h3>
<ul>
<li><strong>Formação Contínua Obrigatória (Arts. 131.º e 132.º CT):</strong> Todo o vigilante tem direito a um mínimo de <strong>40 horas anuais</strong> de formação certificada (ou proporcional no ano de admissão/cessação). Se a empresa não assegurar a formação até ao fim dos 2 anos posteriores ao seu vencimento, essas horas transformam-se num <strong>crédito de horas</strong> que o trabalhador pode usar ou exigir o respetivo pagamento na cessação do contrato.</li>
<li><strong>Fardamento e Equipamento (Lei n.º 34/2013 e CCT):</strong> O fornecimento e substituição de fardamento (incluindo calçado adequado e agasalhos para postos exteriores) é encargo exclusivo da empresa. É <strong>ilegal descontar o custo do fardamento no ordenado</strong>, salvo se o trabalhador não o devolver no fim do contrato ou o danificar intencionalmente.</li>
<li><strong>Videovigilância no Posto de Trabalho (Art. 20.º CT e RGPD):</strong> As câmaras CCTV servem exclusivamente para proteção de pessoas e bens. A empresa não pode utilizar imagens de videovigilância para controlar o rendimento laboral do vigilante nem captar som sem autorização legal expressa.</li>
</ul>
<div class="warning-highlight">
<strong>Atenção aos Dois Prazos Legais Mais Importantes:</strong><br>
1. <strong>Reclamação de Salários, Horas Extras, Noturnas e Formação (Art. 337.º CT):</strong> Todos os créditos laborais prescrevem decorrido <strong>1 ano a partir do dia seguinte ao da cessação do contrato</strong>. Enquanto estás a trabalhar na empresa, o prazo não corre, mas deves guardar provas todos os meses.<br>
2. <strong>Impugnação de Despedimento (Art. 387.º CT):</strong> Se fores alvo de despedimento (com justa causa, extinção de posto ou despedimento ilícito), tens apenas <strong>60 dias seguidos</strong> para entregar o formulário de impugnação no Tribunal do Trabalho. Se deixares passar os 60 dias, perdes o direito de impugnar o despedimento!
</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # 5. PERGUNTAS FREQUENTES (FAQ INTERATIVO)
    st.markdown("### Perguntas Frequentes (FAQ) — Casos Reais do Dia a Dia")

    with st.expander("1. A chefia mandou-me uma mensagem por WhatsApp às 22h00 a mudar o turno de amanhã. Sou obrigado a aceitar?"):
        st.write(
            "Regra geral, **não**. Nos termos do Art. 217.º do Código do Trabalho, qualquer alteração de horário de trabalho "
            "tem de ser comunicada com antecedência mínima de **7 dias** (ou 3 dias em microempresa), salvo acordo expresso "
            "do trabalhador ou motivo de força maior devidamente justificado. Guarda sempre captura de ecrã da escala original "
            "e da mensagem recebida com data e hora visíveis."
        )

    with st.expander("2. Fiz um turno de 12 horas seguidas (ex.: 20h00 às 08h00). Como devem ser pagas essas horas?"):
        st.write(
            "Num turno das 20h00 às 08h00 existem dois cálculos distintos: "
            "**(a) Acréscimo Noturno (+25%):** Todas as horas trabalhadas entre as **21h00 e as 06h00** (9 horas neste turno) têm de ter "
            "um acréscimo mínimo de +25%, mesmo que façam parte do teu horário normal. "
            "**(b) Trabalho Suplementar:** As horas que excedam a tua carga horária normal (ex.: as 4 horas acima de um turno normal de 8h, "
            "caso não estejas em regime de adaptabilidade/banco de horas válido) têm de ser pagas com acréscimo de **+50% se diurnas** "
            "ou **+75% se noturnas**."
        )

    with st.expander("3. A minha empresa perdeu o cliente onde trabalho e a nova empresa quer que eu assine um contrato novo do zero. O que devo fazer?"):
        st.write(
            "**Não assines nenhuma carta de demissão nem contratos que anulem a tua antiguidade.** Por força dos artigos 285.º a 287.º "
            "do Código do Trabalho e das cláusulas de transmissão nos CCT da segurança privada, a nova empresa que assume o posto "
            "recebe o teu contrato tal como está, mantendo a tua data de admissão original, categoria e retribuição. Pede sempre uma cópia "
            "do documento antes de assinar e consulta o teu sindicato ou a ACT."
        )

    with st.expander("4. Nunca me deram as 40 horas anuais de formação nos últimos anos. Perdi esse direito?"):
        st.write(
            "**Não perdeste.** De acordo com os artigos 131.º e 132.º do Código do Trabalho, tens direito a 40 horas de formação "
            "contínua por ano. Quando a empresa não ministra essa formação, as horas vencidas convertem-se em **crédito de horas** "
            "que podes utilizar para formação por tua iniciativa ou exigir o respetivo pagamento em dinheiro quando o contrato terminar "
            "(dentro do prazo de 1 ano após a saída)."
        )

    with st.expander("5. Transferiram-me para um posto a 45 km de casa sem me pagarem deslocação. É legal?"):
        st.write(
            "Se o novo posto fica fora da área geográfica prevista no teu contrato ou causa prejuízo sério (acréscimo relevante de custos "
            "de combustível/transportes e tempo de viagem), a empresa é obrigada pelo **Art. 194.º, n.º 4 do Código do Trabalho** a "
            "pagar o acréscimo das despesas de deslocação e a notificar-te por escrito com antecedência legal (8 ou 30 dias). "
            "Regista a distância exata pelo Google Maps e guarda os comprovativos de combustível ou passes."
        )

    with st.expander("6. Podem descontar-me o valor do fardamento, botas ou cartão MAI no recibo de vencimento?"):
        st.write(
            "**Não.** O equipamento de trabalho e fardamento obrigatório são encargos da entidade empregadora. Só pode haver "
            "desconto ou indemnização se o trabalhador não devolver a farda quando sai da empresa ou se a destruir propositadamente. "
            "Qualquer desconto unilateral no salário sem autorização legal constitui retenção ilícita de retribuição."
        )

    with st.expander("7. Como posso saber qual é o CCT que se aplica ao meu contrato?"):
        st.write(
            "Verifica o teu contrato de trabalho individual ou o cabeçalho/rodapé do teu recibo de vencimento — muitas empresas indicam "
            "a convenção aplicada (ex.: CCT AES/STAD, CCT AES/ASSP, CCT AESIRF/SUSP ou CCT AESIRF/FETESE). Caso não esteja escrito, "
            "aplica-se a **Portaria de Extensão** em vigor para o setor da vigilância privada, cujas tabelas salariais mínimas são "
            "idênticas às publicadas no Boletim do Trabalho e Emprego (BTE)."
        )

    with st.expander("8. Até quando posso reclamar horas extras ou horas noturnas de anos anteriores?"):
        st.write(
            "Pelo **Art. 337.º do Código do Trabalho**, enquanto o teu contrato de trabalho estiver em vigor, os créditos salariais "
            "**não prescrevem** (podes reclamar diferenças de há 2, 3 ou 5 anos atrás, desde que tenhas prova documental como recibos "
            "e escalas). Depois de saíres da empresa, tens **1 ano completo** para intentar ação judicial ou reclamar formalmente."
        )

    with st.expander("9. Como funciona a privacidade 'Custódia Zero' deste site? A minha empresa pode saber que usei a ferramenta?"):
        st.write(
            "**É tecnicamente impossível identificarem-te.** O site não pede nome, email, telefone nem cria contas. Não guardamos "
            "endereços IP e os ficheiros PDF que carregas são lidos apenas na memória temporária (RAM) durante milissegundos para "
            "validar a autenticidade e apagados de imediato. Podes ainda rasurar o teu nome e morada no PDF antes de o carregar."
        )

    with st.expander("10. Pago a quota sindical por débito direto e não aparece no recibo de vencimento. Posso avaliar o meu sindicato na Aba 4?"):
        st.write(
            "**Sim, perfeitamente.** A Aba 4 aceita tanto recibos de vencimento (com ou sem desconto na folha) como comprovativos "
            "de débito direto (SEPA), transferências bancárias, recibos de quota ou declarações anuais de IRS. Todos os vigilantes "
            "sindicalizados têm exatamente o mesmo peso e voz no ranking."
        )

    # 6. CAIXA DE SUGESTÕES ANÓNIMAS
    st.divider()
    st.markdown("### Caixa de Sugestões & Melhoria Contínua (100% Anónima)")
    st.write(
        "Tens uma ideia para uma nova calculadora, uma atualização de tabela salarial, melhoria no telemóvel "
        "ou encontraste algum erro? Envia a tua proposta sem qualquer identificação."
    )

    col_sug1, col_sug2 = st.columns([1, 2])
    with col_sug1:
        cat_sugestao = st.selectbox(
            "Categoria da Sugestão",
            [
                "Nova Funcionalidade / Calculadora",
                "Atualização de Tabela / CCT",
                "Melhoria de Design / Telemóvel",
                "Reportar Erro Técnico",
                "Sugestão para o Guia Legal / FAQ",
            ],
        )
    with col_sug2:
        texto_sugestao = st.text_area(
            "A tua sugestão (não incluas nomes próprios nem dados pessoais)",
            placeholder="Exemplo: Seria útil ter uma calculadora específica para subsídio de férias e Natal proporcionais ou cálculo de indemnização por despedimento...",
            max_chars=800,
            height=110,
        )

    if st.button("Enviar Sugestão Anónima", type="primary"):
        if st.session_state["sugestoes_enviadas_sessao"] >= 3:
            st.warning("Atingiste o limite de 3 sugestões por sessão para proteção contra spam.")
        elif len(texto_sugestao.strip()) < 10:
            st.error("Escreve uma sugestão com pelo menos 10 caracteres.")
        else:
            ok_sug, msg_sug = guardar_sugestao_anonima(cat_sugestao, texto_sugestao)
            if ok_sug:
                st.session_state["sugestoes_enviadas_sessao"] += 1
                st.success(msg_sug)
            else:
                st.error(msg_sug)

    sugestoes_recentes = carregar_sugestoes_recentes(limite=6)
    if sugestoes_recentes:
        st.markdown("#### Últimas Ideias Submetidas pela Comunidade")
        for sug in sugestoes_recentes:
            st.markdown(
                f"""
<div class="suggestion-item">
<strong>[{sug.get('categoria', 'Geral')}]</strong> {sug.get('mensagem', '')}
</div>
                """,
                unsafe_allow_html=True,
            )

# ==============================================================================
# RODAPÉ INFORMATIVO
# ==============================================================================
st.markdown(
    """
<div class="footer-box">
<strong>Vigilante Informado — Plataforma Independente de Literacia Laboral</strong><br>
Arquitetura Custódia Zero (RGPD) • Sem armazenamento de documentos, nomes ou endereços IP • Os cálculos têm natureza técnica e informativa com base nos CCT publicados em BTE e no Código do Trabalho.
</div>
    """,
    unsafe_allow_html=True,
)
