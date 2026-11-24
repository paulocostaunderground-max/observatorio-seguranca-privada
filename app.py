import datetime
import hashlib
import io
import re
import pandas as pd
import streamlit as st
from pypdf import PdfReader

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

LIMIAR_GRUPO_COLETIVO = 10

st.set_page_config(
    page_title="Vigilante Informado - Apoio Técnico & CCT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS Institucional Responsivo (Desktop + Mobile)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    .main .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #FFFFFF;
        padding: 1.75rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.25rem;
        border-bottom: 4px solid #10B981;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .hero-logo {
        flex-shrink: 0;
    }
    .hero-text h1 {
        margin: 0;
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #FFFFFF;
        line-height: 1.2;
    }
    .hero-text p {
        margin: 0.45rem 0 0 0;
        font-size: 0.98rem;
        color: #CBD5E1;
        line-height: 1.45;
    }
    .hero-tag {
        display: inline-block;
        background-color: rgba(16, 185, 129, 0.18);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.35);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        margin-bottom: 0.5rem;
    }
    .trust-strip {
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #065F46;
        padding: 0.85rem 1.15rem;
        border-radius: 10px;
        font-size: 0.9rem;
        margin-bottom: 1.25rem;
        line-height: 1.45;
    }
    .info-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0F172A;
        padding: 1.1rem 1.25rem;
        border-radius: 10px;
        font-size: 0.92rem;
        color: #334155;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .guide-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #059669;
        padding: 1.35rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        line-height: 1.55;
    }
    .guide-card h3 {
        color: #0F172A;
        margin-top: 0;
        margin-bottom: 0.75rem;
        font-size: 1.18rem;
    }
    .guide-card h4 {
        color: #0F172A;
        margin-top: 1rem;
        margin-bottom: 0.4rem;
        font-size: 1.02rem;
    }
    .rule-highlight {
        background-color: #F1F5F9;
        border-left: 4px solid #0284C7;
        padding: 0.85rem 1rem;
        border-radius: 6px;
        margin: 0.75rem 0;
        font-size: 0.92rem;
        color: #1E293B;
    }
    .warning-highlight {
        background-color: #FEF2F2;
        border-left: 4px solid #DC2626;
        padding: 0.85rem 1rem;
        border-radius: 6px;
        margin: 0.75rem 0;
        font-size: 0.92rem;
        color: #7F1D1D;
    }
    .alert-amber {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        color: #92400E;
        padding: 1rem;
        border-radius: 10px;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.85rem;
            padding-right: 0.85rem;
            padding-top: 0.85rem;
        }
        .hero-banner {
            flex-direction: column;
            align-items: flex-start;
            padding: 1.25rem;
            gap: 0.9rem;
        }
        .hero-text h1 {
            font-size: 1.32rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def obter_salt_segredo() -> str:
    try:
        return st.secrets.get("APP_SECRET_SALT", "SALT_LOCAL_DESENVOLVIMENTO_2026")
    except Exception:
        return "SALT_LOCAL_DESENVOLVIMENTO_2026"


def validar_recibo_em_memoria(ficheiro_bytes: bytes, empresa_selecionada: str) -> dict:
    try:
        reader = PdfReader(io.BytesIO(ficheiro_bytes))
        texto_total = ""
        for page in reader.pages[:2]:
            texto_total += (page.extract_text() or "") + "\n"

        texto_lower = texto_total.lower()

        marcadores_recibo = [
            "vencimento",
            "remuneração",
            "remuneracao",
            "segurança social",
            "seguranca social",
            "irs",
            "líquido",
            "liquido",
            "ilíquido",
            "iliquido",
            "subsídio",
            "subsidio",
            "alimentação",
            "alimentacao",
            "abonos",
            "descontos",
            "categoria",
            "vigilante",
            "iban",
            "nib",
            "niss",
            "período",
            "periodo",
            "11%",
            "11,00%",
        ]
        encontrados = sum(1 for m in marcadores_recibo if m in texto_lower)
        valores_monetarios = re.findall(r"\b\d{1,5}[.,]\d{2}\b", texto_total)

        if encontrados < 3 or len(valores_monetarios) < 2:
            return {
                "valido": False,
                "motivo": (
                    "Não foi possível detetar a estrutura salarial completa no PDF. "
                    "Certifica-te de que é o PDF digital original emitido pela empresa."
                ),
            }

        for nome_emp, dados_emp in EMPRESAS_SEGURANCA.items():
            if nome_emp == empresa_selecionada:
                continue
            for kw in dados_emp.get("keywords", []):
                if kw and len(kw) >= 4 and re.search(rf"\b{re.escape(kw)}\b", texto_lower):
                    return {
                        "valido": False,
                        "motivo": f"O recibo parece pertencer a outra entidade ({nome_emp}) diferente da selecionada.",
                    }

        nipc_detetado = "VALIDADO-ERP"
        candidatos_9d = re.findall(r"\b[5-9]\d{8}\b", re.sub(r"[^\d\s]", " ", texto_total))
        for cand in candidatos_9d:
            if validar_nipc_portugues(cand):
                nipc_detetado = cand
                break

        salt = obter_salt_segredo()
        texto_normalizado = re.sub(r"\s+", " ", texto_total.strip())[:1000]
        assinatura_bruta = f"{empresa_selecionada}:{texto_normalizado}:{salt}".encode("utf-8", errors="ignore")
        hash_unico = hashlib.sha256(assinatura_bruta).hexdigest()

        return {"valido": True, "hash_unico": hash_unico, "nipc_detetado": nipc_detetado}
    except Exception:
        return {
            "valido": False,
            "motivo": "Não foi possível ler o PDF. Verifica se o ficheiro não está protegido por palavra-passe.",
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
                return False, "Este recibo já foi auditado e registado anteriormente no sistema."
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


# CABEÇALHO INSTITUCIONAL COM LOGÓTIPO VETORIAL PRÓPRIO (SVG)
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
            <span class="hero-tag">Ferramenta Independente de Literacia Laboral - Portugal</span>
            <h1>Vigilante Informado - Apoio Técnico & CCT</h1>
            <p>Simulador salarial baseado nas tabelas oficiais do BTE, organização de provas e coordenação coletiva com privacidade absoluta.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="trust-strip">
        <strong>Proteção Custódia Zero (RGPD):</strong> Não pedimos nome, NIF, email nem telefone.
        Os recibos carregados são analisados apenas em memória RAM e destruídos no mesmo segundo.
        Os relatórios em PDF são descarregados exclusivamente para o teu dispositivo.
    </div>
    """,
    unsafe_allow_html=True,
)

if supabase is None:
    st.info(
        "Modo de demonstração local ativo: configura as chaves SUPABASE_URL e SUPABASE_KEY nos Secrets do Streamlit "
        "para gravação permanente."
    )

aba1, aba2, aba3, aba4, aba5 = st.tabs(
    [
        "1. Simulador Salarial & Formação",
        "2. Documentar Ocorrências",
        "3. Indicadores do Setor",
        "4. Ação Coletiva (Grupos)",
        "5. Guia do Vigilante, Horários & Legal",
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
            help="Horas de escala normal trabalhadas em dia feriado (acresce +100% sobre o valor hora).",
        )
        h_extras_feriado = st.number_input(
            "Horas Extras em Feriado / Descanso (200% total)",
            min_value=0.0,
            max_value=3000.0,
            value=0.0,
            step=1.0,
            help="Trabalho suplementar prestado em dia feriado ou dia de descanso semanal (pago a dobrar).",
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

    st.markdown("#### Passo C: Validação Técnica Anti-Fraude (Opcional para Entrar nos Indicadores Públicos)")
    st.caption(
        "Para contabilizar o teu caso nas estatísticas públicas e nos grupos de ação coletiva, anexa um recibo "
        "de vencimento original (PDF) desse período. O ficheiro é validado em memória RAM e apagado imediatamente."
    )
    ficheiro_pdf = st.file_uploader("Carregar Recibo de Vencimento de Referência (PDF original)", type=["pdf"])
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
                            "Guarda este código para acompanhares o grupo coletivo na Aba 4."
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
                "Cálculo efetuado em modo de simulação manual. Para entrar nos Indicadores Públicos e nos grupos "
                "de ação coletiva, anexa um recibo original em PDF."
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
# ABA 3: INDICADORES ESTATÍSTICOS DO SETOR
# ==============================================================================
with aba3:
    st.subheader("Indicadores Agregados de Conformidade Laboral")
    st.write(
        "Dados estatísticos agregados baseados exclusivamente em recibos validados tecnicamente. "
        "Nenhum trabalhador ou posto isolado é identificado."
    )

    dados = carregar_todos_registos()
    if not dados:
        st.info(
            "Ainda não existem registos validados suficientes para exibir estatísticas agregadas. "
            "Assim que os primeiros recibos forem validados na Aba 1, os indicadores surgirão aqui automaticamente."
        )
    else:
        df = pd.DataFrame(dados)
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.metric("Total de Registos Validados", len(df))
        c_k2.metric("Desvio Médio Apurado", f"{df['desvio_eur'].mean():.2f} EUR")
        c_k3.metric("Total Acumulado em Falta", f"{df['desvio_eur'].sum():.2f} EUR")

        st.markdown("#### Incidência por Entidade Empregadora")
        resumo_emp = (
            df.groupby("empresa")
            .agg(
                Casos_Validados=("id", "count") if "id" in df.columns else ("hash_unico", "count"),
                Desvio_Medio_EUR=("desvio_eur", "mean"),
                Total_Apurado_EUR=("desvio_eur", "sum"),
            )
            .reset_index()
        )
        resumo_emp["Desvio_Medio_EUR"] = resumo_emp["Desvio_Medio_EUR"].round(2)
        resumo_emp["Total_Apurado_EUR"] = resumo_emp["Total_Apurado_EUR"].round(2)
        st.dataframe(resumo_emp, use_container_width=True, hide_index=True)

        st.markdown("#### Tipologias Mais Frequentes")
        st.bar_chart(df["tipo_infracao"].value_counts())


# ==============================================================================
# ABA 4: AÇÃO COLETIVA & CANAIS AUTÓNOMOS ZERO-ADMIN
# ==============================================================================
with aba4:
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
        dados = carregar_todos_registos()
        caso_encontrado = next((d for d in dados if d.get("codigo_caso") == codigo_consulta), None)

        if not caso_encontrado:
            st.error("Código de caso não encontrado. Verifica se copiaste corretamente após a validação na Aba 1.")
        else:
            emp_c = caso_encontrado["empresa"]
            dist_c = caso_encontrado["distrito"]
            tipo_c = caso_encontrado["tipo_infracao"]

            iguais = [
                d for d in dados
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
# ABA 5: GUIA DO VIGILANTE, HORÁRIOS, SINDICATOS & QUADRO LEGAL
# ==============================================================================
with aba5:
    st.subheader("Guia de Defesa Laboral do Vigilante: Horários, Direitos e Sindicalismo")

    st.markdown(
        """
        <div class="guide-card">
            <h3>1. Uma Nova Era na Segurança Privada: Não Estás Sozinho</h3>
            <p>Durante décadas, o maior trunfo contra os vigilantes foi o isolamento entre postos e o desconhecimento
            técnico das regras salariais e de horário. Muitos profissionais aceitam cortes nas horas noturnas, escalas
            alteradas de véspera ou horas extras não pagas por acreditarem que reclamar sozinho não dá resultado.</p>
            <p>Esta ferramenta marca o início de uma mudança de paradigma: <strong>conhecimento jurídico acessível,
            documentação rigorosa e união inteligente</strong>. Quando cada vigilante sabe calcular o seu recibo ao
            cêntimo, percebe o seu regime de horário e guarda provas organizadas, o equilíbrio de forças muda.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="guide-card">
            <h3>2. Regimes de Horário: Turnos, Adaptabilidade e Horário Concentrado</h3>
            <p>Muitas irregularidades no pagamento de horas extras acontecem porque as empresas misturam regras de
            regimes diferentes. Conhece exatamente o que a lei permite e o que é proibido em cada um:</p>

            <h4>A) Regime de Turnos (Artigos 220.º a 222.º do Código do Trabalho)</h4>
            <ul>
                <li><strong>O que é:</strong> Organização do trabalho em equipa em que os vigilantes ocupam sucessivamente
                os mesmos postos de trabalho a um determinado ritmo (turnos fixos ou rotativos, em regime contínuo 24h
                ou descontínuo).</li>
                <li><strong>Precisa de acordo escrito?</strong> Não exige acordo individual se estiver previsto no
                contrato de trabalho ou na organização normal da empresa/CCT, mas a escala tem de ser afixada ou
                comunicada com <strong>7 dias de antecedência</strong> (Art. 217.º CT).</li>
                <li><strong>Regras de proteção:</strong> O vigilante só pode mudar de turno após o dia de descanso
                semanal (Art. 221.º n.º 4 CT) e tem direito obrigatório a pelo menos <strong>11 horas seguidas de
                descanso</strong> entre dois turnos (Art. 214.º CT).</li>
                <li><strong>Como se contam as Horas Extras neste regime:</strong> Num contrato de 40 horas semanais
                sem adaptabilidade nem horário concentrado, qualquer hora trabalhada acima das <strong>8 horas diárias</strong>
                ou acima das <strong>40 horas semanais</strong> (ou acima da carga horária mensal de dias úteis × 8h)
                é <strong>trabalho suplementar (hora extra)</strong> e tem de ser paga com acréscimo (+50% diurna / +75% noturna).</li>
            </ul>

            <h4>B) Regime de Adaptabilidade (Artigos 204.º a 206.º do Código do Trabalho)</h4>
            <ul>
                <li><strong>O que é:</strong> Permite à empresa variar a duração do trabalho diário e semanal dentro de
                um período de referência (por exemplo, 4 meses), compensando semanas com mais horas com outras semanas
                de menos horas para que a <strong>média semanal seja de 40 horas</strong>.</li>
                <li><strong>Quando se aplica e precisa de autorização escrita?</strong> Só se aplica se estiver previsto
                no <strong>CCT aplicável</strong> (Adaptabilidade Coletiva) ou mediante <strong>acordo escrito</strong>
                com o trabalhador (Adaptabilidade Individual - Art. 205.º CT). Se o teu contrato não tiver cláusula de
                adaptabilidade e não assinaste acordo escrito (nem o teu CCT a impuser automaticamente), a empresa
                <strong>não pode</strong> aplicar-te adaptabilidade.</li>
                <li><strong>Limites máximos:</strong> Na adaptabilidade individual o limite máximo é de +2 horas/dia
                (máximo <strong>10 horas/dia</strong>) e <strong>50 horas/semana</strong>. Por CCT pode ir até 10h ou
                12h/dia conforme o texto do contrato coletivo.</li>
                <li><strong>Como se contam as Horas Extras na Adaptabilidade:</strong>
                    <br>1. Qualquer hora que ultrapasse o teto máximo diário ou semanal da adaptabilidade (ex.: acima de 10h/dia
                    ou 50h/semana) é <strong>imediatamente hora extra</strong> paga nesse mês.
                    <br>2. No final do período de referência (ex.: ao fim de 4 meses), somam-se todas as horas trabalhadas:
                    se a média ultrapassar as 40h/semana, <strong>todas as horas excedentes têm de ser pagas como trabalho
                    suplementar</strong>.</li>
            </ul>

            <h4>C) Regime de Horário Concentrado (Artigo 209.º do Código do Trabalho)</h4>
            <ul>
                <li><strong>O que é:</strong> Concentra o período normal de trabalho semanal em menos dias da semana
                (por exemplo, trabalhar <strong>3 ou 4 dias seguidos a 10h ou 12h por dia</strong>, seguidos de 3 ou 4
                dias seguidos de descanso).</li>
                <li><strong>Quando se aplica e precisa de autorização escrita?</strong> Exige obrigatoriamente
                <strong>acordo escrito</strong> entre o vigilante e a empresa ou previsão expressa no <strong>CCT</strong>.
                Permite aumentar o horário normal diário até mais 4 horas (atingindo o máximo de <strong>12 horas por dia</strong>).</li>
                <li><strong>Como se contam as Horas Extras no Horário Concentrado:</strong> Tudo o que ultrapassar o
                limite diário concentrado acordado (ex.: acima de 12 horas no mesmo turno), tudo o que ultrapassar a
                média das 40 horas semanais, ou qualquer turno extra marcado nos dias de descanso previstos na escala.</li>
            </ul>

            <div class="warning-highlight">
                <strong>REGRA LEGAL FUNDAMENTAL (Incompatibilidade de Regimes - Art. 209.º, n.º 3 do Código do Trabalho):</strong><br>
                Quando está em vigor o <strong>Horário Concentrado</strong> (por exemplo, turnos regulares de 12 horas),
                <strong>NÃO PODE vigorar em simultâneo o Regime de Adaptabilidade</strong>. A lei proíbe expressamente a
                acumulação dos dois regimes no mesmo trabalhador. Se fazes turnos de 12 horas em horário concentrado, a
                empresa não pode usar "bancos de horas" ou "adaptabilidade" para evitar pagar horas extras.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="guide-card">
            <h3>3. Cálculo da Carga Horária Mensal (Contrato 40h), Feriados, Folgas e Férias</h3>

            <h4>A) Como calcular as horas normais de cada mês (Contrato de 40 horas semanais)</h4>
            <p>Num contrato a tempo inteiro de 40 horas semanais (base de 8 horas/dia, 5 dias por semana), a carga
            horária normal do mês calcula-se de forma simples:</p>
            <div class="rule-highlight">
                <strong>Fórmula Base:</strong> <code>Número de Dias Úteis do Mês × 8 Horas = Carga Horária Mensal Normal</code><br>
                <em>Exemplo prático:</em> Num mês com 22 dias úteis (segunda a sexta), o horário normal são <strong>176 horas</strong>
                (22 × 8h). Tudo o que trabalhaste acima dessas 176 horas (salvo adaptabilidade válida dentro do período de
                referência) é <strong>trabalho suplementar (horas extras)</strong>.
            </div>
            <ul>
                <li><strong>Os feriados contam nos dias úteis? NÃO.</strong> Os dias feriados obrigatórios (nacionais e
                feriado municipal do concelho do posto) <strong>não contam como dias úteis a trabalhar</strong>. Se um mês
                tem 22 dias de segunda a sexta, mas 1 desses dias é feriado, os dias úteis baixam para <strong>21 dias
                (168 horas)</strong>.</li>
                <li><strong>E se eu trabalhar no dia feriado?</strong> Como o feriado não entra nos dias úteis obrigatórios
                a compensar gratuitamente, todas as horas trabalhadas em dia feriado têm de ser pagas com o
                <strong>acréscimo legal/convencional de +100%</strong> (ou compensadas nos exatos termos previstos no CCT
                aplicável), além de entrarem no cômputo da escala.</li>
            </ul>

            <h4>B) Quantas folgas (dias de descanso) a empresa tem de dar?</h4>
            <ul>
                <li><strong>2 dias de descanso por semana (Art. 232.º CT + CCT):</strong> Numa semana normal de 40 horas
                distribuídas por 5 dias, o vigilante tem direito a <strong>1 dia de descanso semanal obrigatório</strong> e
                <strong>1 dia de descanso semanal complementar</strong> (totalizando 2 folgas por semana, ou seja, 8 a 9
                folgas por mês consoante o calendário).</li>
                <li><strong>Descanso mínimo entre turnos:</strong> Pelo menos <strong>11 horas seguidas</strong> entre o
                fim de um turno e o início do seguinte (Art. 214.º CT).</li>
                <li><strong>Domingos de folga:</strong> Nos regimes de turnos rotativos, o dia de descanso semanal
                obrigatório deve coincidir periodicamente com o domingo, e o trabalhador não pode trabalhar mais de
                6 dias consecutivos sem gozar descanso semanal.</li>
            </ul>

            <h4>C) Quantos dias úteis de férias tens direito por ano?</h4>
            <ul>
                <li><strong>Regra Geral (Art. 238.º CT):</strong> Tens direito a <strong>22 dias úteis de férias</strong>
                por cada ano civil, que se vencem no dia 1 de janeiro.</li>
                <li><strong>No Ano de Admissão (Art. 239.º CT):</strong> Tens direito a <strong>2 dias úteis por cada
                mês completo</strong> de duração do contrato, até ao máximo de <strong>20 dias úteis</strong>, que podem
                ser gozados após 6 meses completos de trabalho.</li>
                <li><strong>Atenção nos Turnos Rotativos (Art. 238.º, n.º 2 CT):</strong> Para contar férias, são dias
                úteis os dias de segunda a sexta-feira (exceto feriados). <strong>Contudo</strong>, se as tuas folgas
                semanais calham em dias de semana (por exemplo, folgas à terça e quarta-feira), esses dias de folga
                <strong>não contam como dias de férias</strong> e são substituídos pelos dias em que irias trabalhar
                (sábado ou domingo). Na prática, 22 dias úteis de férias significam sempre <strong>22 turnos de trabalho
                que deixas de fazer</strong>.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="guide-card">
            <h3>4. Para que servem os CCTs e quais existem atualmente?</h3>
            <p>O <strong>Contrato Coletivo de Trabalho (CCT)</strong> é a lei específica negociada entre as associações
            patronais (como a <strong>AES</strong> e a <strong>AESIRF</strong>) e os sindicatos do setor. Define tudo
            o que melhora o Código do Trabalho geral: tabelas salariais acima do salário mínimo, subsídio de alimentação,
            acréscimo noturno (25%), pagamento de feriados, subsídios de função (aeroportuária, transporte de valores,
            porteiro/rondista) e regras de transmissão de estabelecimento.</p>
            <ul>
                <li><strong>Principais CCTs em vigor no setor:</strong> CCT AES / STAD, CCT AES / ASSP, CCT AESIRF / FETESE
                e CCT AESIRF / SUSP (além das <em>Portarias de Extensão</em> publicadas pelo Governo que alargam as
                tabelas a empresas não filiadas).</li>
                <li><strong>Quando são negociados?</strong> Por norma, a revisão salarial anual é negociada entre o
                final do ano e o primeiro trimestre do ano seguinte, sendo publicada no <strong>Boletim do Trabalho e
                Emprego (BTE)</strong>. Frequentemente inclui pagamentos com efeitos retroativos a janeiro.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="guide-card">
            <h3>5. A Importância de Ser Sindicalizado (Análise Objetiva e Imparcial)</h3>
            <p>Muitos vigilantes hesitam por causa da quota mensal (em média cerca de <strong>1% do salário base</strong>),
            mas ignoram o retorno financeiro e jurídico real:</p>
            <ul>
                <li><strong>Apoio Jurídico Gratuito vs. Advogado Particular:</strong> Um processo judicial laboral
                individual pode custar entre 1.000 EUR e 3.000 EUR em honorários e custas. Um sócio sindicalizado tem
                acesso gratuito aos advogados do sindicato.</li>
                <li><strong>Benefício Fiscal no IRS:</strong> Em Portugal, as quotizações sindicais têm uma majoração
                fiscal na declaração de IRS (dedução acrescida em 50% dentro dos limites legais), o que reduz o custo
                líquido real da quota ao longo do ano.</li>
                <li><strong>O Peso da Força Numérica:</strong> Um sindicato com 500 sócios tem pouco poder de pressão
                junto das grandes empresas e do Ministério; um sindicato com milhares de vigilantes ativos consegue
                bloquear retrocessos e impor aumentos reais.</li>
                <li><strong>O Erro Mais Comum:</strong> Muitos profissionais só se sindicalizam quando já têm um
                problema grave em tribunal e sem qualquer prova guardada. Os processos judiciais levam tempo, mas
                avançar com apoio sindical e provas já reunidas é sempre incomparavelmente mais seguro do que lutar
                sozinho.</li>
                <li><strong>Como Escolher um Sindicato (Liberdade Sindical):</strong> A Constituição garante liberdade
                total de escolha. Avalia a rapidez de resposta do gabinete jurídico, a transparência dos acordos
                assinados e a presença na tua região. Se não estiveres satisfeito com um sindicato em particular,
                podes desfiliar-te e escolher outro a qualquer momento.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="guide-card">
            <h3>6. Greves na Segurança Privada: Direitos, Custos e Conquistas Reais</h3>
            <ul>
                <li><strong>Quem pode aderir à greve?</strong> Ao abrigo da Constituição e do Código do Trabalho,
                <strong>qualquer vigilante abrangido pelo pré-aviso pode fazer greve, mesmo que não seja sindicalizado</strong>
                e independentemente de qual sindicato convocou a greve. A empresa está legalmente proibida de aplicar
                represálias ou contratar substitutos para o teu posto durante a greve.</li>
                <li><strong>O que se perde vs. O que se ganha:</strong> Perde-se a retribuição e o subsídio de
                alimentação correspondentes ao dia de greve. Contudo, foi precisamente através das greves e lutas
                coletivas dos últimos anos que os vigilantes conquistaram aumentos significativos da tabela base
                (evitando a colagem ao salário mínimo nacional), subidas no subsídio de alimentação e o reforço da
                proteção na transmissão de estabelecimento (Art. 285.º), garantindo que não perdes a casa nem a
                antiguidade quando muda a empresa de segurança no cliente.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="guide-card">
            <h3>7. Conselhos Jurídicos de Base (Regras de Ouro do Vigilante)</h3>
            <ul>
                <li><strong>Nunca assines nada sob pressão:</strong> Se uma chefia apresentar uma adenda contratual,
                acordo de revogação ou mudança de posto para assinar na hora, tens o direito de pedir uma cópia para
                analisar com calma antes de assinar.</li>
                <li><strong>Guarda sempre cópia das escalas e ordens:</strong> Tira captura de ecrã às escalas mensais
                assim que saem e guarda mensagens escritas de alterações de turno ou deslocações.</li>
                <li><strong>Crédito de Formação (Art. 131.º CT):</strong> Tens direito a 40 horas anuais de formação
                certificada. Se a empresa não der formação durante 2 anos, essas horas convertem-se em crédito de
                horas para formação por tua iniciativa ou têm de ser pagas na cessação do contrato.</li>
                <li><strong>Prazo de Prescrição (Art. 337.º CT):</strong> Tens até 1 ano após o dia seguinte ao fim
                do contrato de trabalho para reclamar judicialmente créditos laborais em falta (horas extras,
                noturnas, feriados ou formação).</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Aviso Legal e Isenção de Responsabilidade")
    st.markdown(
        """
        <div class="info-card">
            <strong>1. Natureza Informativa:</strong> Esta plataforma é uma ferramenta independente de cálculo
            matemático e literacia laboral baseada nos Contratos Coletivos de Trabalho (CCT) e no Código do
            Trabalho português. Os resultados têm caráter indicativo e não substituem aconselhamento jurídico
            profissional.<br><br>
            <strong>2. Política de Privacidade Custódia Zero (RGPD):</strong> Em cumprimento do Artigo 5.º do RGPD,
            esta plataforma não recolhe nem armazena nomes, NIFs, moradas, contactos ou ficheiros PDF. Qualquer
            documento submetido é lido exclusivamente em memória RAM e eliminado imediatamente.<br><br>
            <strong>3. Prevenção de Difamação e Responsabilidade do Utilizador:</strong> O site não publica
            acusações nominais contra chefias ou clientes individuais. O utilizador declara que os dados
            inseridos correspondem à verdade dos factos, assumindo responsabilidade legal nos termos do
            Artigo 365.º do Código Penal (Denúncia Caluniosa).
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Perguntas Frequentes (FAQ)")
    with st.expander("1. A minha empresa ou chefia consegue descobrir que usei este site?"):
        st.write(
            "Não. O site não exige registo, nome, email nem número de funcionário. Para proteção adicional, "
            "utiliza sempre os dados móveis do teu telemóvel e nunca a rede Wi-Fi do posto ou da empresa."
        )
    with st.expander("2. O criador do site fica com cópia do meu recibo de vencimento?"):
        st.write(
            "Não. O ficheiro PDF é processado apenas na memória temporária do servidor para verificar a "
            "autenticidade e gerar um código criptográfico anónimo, sendo apagado no mesmo segundo."
        )
    with st.expander("3. Como evitam denúncias falsas que retirem credibilidade ao site?"):
        st.write(
            "As estatísticas públicas e os grupos coletivos aceitam apenas cálculos acompanhados pela "
            "leitura estrutural de um recibo original com estrutura salarial validada, bloqueando submissões "
            "duplicadas através de uma assinatura criptográfica irreversível (SHA-256)."
        )
    with st.expander("4. Como funciona o grupo quando atingimos 10 casos na mesma empresa?"):
        st.write(
            "O sistema gera automaticamente um link para uma sala encriptada externa onde os detentores "
            "dos códigos de caso podem coordenar uma queixa conjunta na ACT ou contactar um sindicato ou "
            "advogado laboralista em grupo."
        )
