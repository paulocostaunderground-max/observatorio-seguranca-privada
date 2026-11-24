import datetime
import hashlib
import io
import re
import pandas as pd
import streamlit as st
from pypdf import PdfReader

from cct_engine import (
    DISTRITOS_PORTUGAL,
    EMPRESAS_SEGURANCA,
    TIPOS_INCUMPRIMENTO,
    calcular_auditoria_mensal,
    obter_enquadramento,
)
from pdf_generator import gerar_pdf_auditoria, gerar_pdf_ocorrencia

# Limiar minimo de casos unicos validados para desbloquear canal de acao coletiva
LIMIAR_GRUPO_COLETIVO = 10

st.set_page_config(
    page_title="Observatorio da Seguranca Privada PT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS Institucional (Trust-First UI + Mobile First)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }
    .header-box {
        background-color: #0F172A;
        color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        border-left: 6px solid #059669;
    }
    .header-box h1 {
        margin: 0;
        font-size: 1.55rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .header-box p {
        margin: 0.4rem 0 0 0;
        font-size: 0.95rem;
        color: #CBD5E1;
    }
    .trust-badge {
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #065F46;
        padding: 0.65rem 1rem;
        border-radius: 8px;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }
    .legal-box {
        background-color: #F1F5F9;
        border-left: 4px solid #334155;
        padding: 1rem;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #334155;
        margin-bottom: 0.8rem;
    }
    .alert-amber {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        color: #92400E;
        padding: 0.85rem;
        border-radius: 8px;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Ligacao opcional ao Supabase (UE) via st.secrets
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


def validar_recibo_em_memoria(ficheiro_bytes: bytes, nipc_esperado: str) -> dict:
    """
    Le o PDF apenas em memoria RAM, verifica estrutura real de recibo de vencimento,
    gera hash criptografico irreversivel para evitar duplicados e descarta o ficheiro.
    """
    try:
        reader = PdfReader(io.BytesIO(ficheiro_bytes))
        texto_total = ""
        for page in reader.pages[:2]:
            texto_total += page.extract_text() or ""

        texto_lower = texto_total.lower()
        marcadores_recibo = [
            "vencimento",
            "remuneracao",
            "remuneração",
            "seguranca social",
            "segurança social",
            "irs",
            "recibo",
            "liquido",
            "líquido",
        ]
        encontrados = sum(1 for m in marcadores_recibo if m in texto_lower)

        nipc_limpo = re.sub(r"\D", "", nipc_esperado)
        texto_numeros = re.sub(r"\D", "", texto_total)
        nipc_bate_certo = (nipc_limpo == "000000000") or (nipc_limpo in texto_numeros)

        if encontrados < 2:
            return {
                "valido": False,
                "motivo": "O ficheiro nao apresenta a estrutura textual de um recibo de vencimento processado.",
            }

        if not nipc_bate_certo:
            return {
                "valido": False,
                "motivo": "O NIPC detetado no PDF nao corresponde a empresa selecionada.",
            }

        # Gera assinatura unica do documento sem guardar dados pessoais
        salt = obter_salt_segredo()
        assinatura_bruta = f"{nipc_limpo}:{texto_total[:600]}:{salt}".encode("utf-8", errors="ignore")
        hash_unico = hashlib.sha256(assinatura_bruta).hexdigest()

        return {"valido": True, "hash_unico": hash_unico}
    except Exception:
        return {
            "valido": False,
            "motivo": "Nao foi possivel ler o PDF. Verifica se o ficheiro nao esta protegido por palavra-passe.",
        }


def gerar_codigo_caso(hash_unico: str) -> str:
    return f"VIG-{hash_unico[:4].upper()}-{hash_unico[4:8].upper()}"


def gerar_links_sala_autonoma(empresa: str, distrito: str, tipo_infracao: str) -> dict:
    """
    Gera deterministicamente links para salas encriptadas em RAM (Zero-Admin / Zero-Custody).
    Nenhuma sala e criada ou administrada pelo criador do site.
    """
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
                return False, "Este recibo ja foi auditado e registado anteriormente no sistema."
            supabase.table("denuncias_validadas").insert(registo).execute()
            return True, "Registo tecnico validado e guardado anonimamente com sucesso."
        except Exception as e:
            return False, f"Erro de ligacao a base de dados: {str(e)}"
    else:
        for r in st.session_state["registos_locais"]:
            if r["hash_unico"] == registo["hash_unico"]:
                return False, "Este recibo ja foi registado nesta sessao."
        st.session_state["registos_locais"].append(registo)
        return True, "Registo guardado em modo de demonstracao local (liga o Supabase para persistencia permanente)."


def carregar_todos_registos() -> list:
    if supabase is not None:
        try:
            resp = supabase.table("denuncias_validadas").select("*").execute()
            return resp.data or []
        except Exception:
            return st.session_state["registos_locais"]
    return st.session_state["registos_locais"]


# CABECALHO PRINCIPAL
st.markdown(
    """
    <div class="header-box">
        <h1>🛡️ Observatorio Tecnico da Seguranca Privada (Portugal)</h1>
        <p>Auditoria salarial baseada no CCT, documentacao de provas e coordenacao coletiva com privacidade total.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="trust-badge">
        <strong>Arquitetura Custodia Zero (RGPD):</strong> Nao pedimos nome, NIF, email nem telefone.
        Os recibos carregados sao lidos apenas em memoria RAM e destruidos no mesmo segundo.
        O dossie PDF fica guardado exclusivamente no teu telemovel.
    </div>
    """,
    unsafe_allow_html=True,
)

if supabase is None:
    st.info(
        "Modo de demonstracao ativo: os dados ficam apenas na memoria da sessao atual ate configurares "
        "as chaves SUPABASE_URL e SUPABASE_KEY nos Secrets do Streamlit."
    )

aba1, aba2, aba3, aba4, aba5 = st.tabs(
    [
        "1. Auditor de Recibos & CCT",
        "2. Documentar Ocorrencias",
        "3. Radar do Setor",
        "4. Acao Coletiva (Grupos)",
        "5. FAQ & Protecao Legal",
    ]
)

# ==============================================================================
# ABA 1: AUDITOR DE RECIBOS & CCT
# ==============================================================================
with aba1:
    st.subheader("Auditoria Matematica de Vencimento e Escala")
    st.write(
        "Seleciona a empresa e o periodo trabalhado. O sistema identifica automaticamente o "
        "Contrato Coletivo de Trabalho (CCT) aplicavel nesse periodo."
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        empresa_sel = st.selectbox("Entidade Empregadora", list(EMPRESAS_SEGURANCA.keys()))
    with col2:
        distrito_sel = st.selectbox("Distrito do Posto", DISTRITOS_PORTUGAL)
    with col3:
        ano_sel = st.selectbox("Ano do Recibo", [2026, 2025, 2024, 2023])

    mes_sel = st.selectbox(
        "Mes do Recibo",
        [
            "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ],
    )

    enq = obter_enquadramento(empresa_sel, ano_sel)
    st.markdown(
        f"""
        <div class="legal-box">
            <strong>Enquadramento Automatico Detetado:</strong> {enq['cct']} (Tabela {enq['ano_aplicado']}) |
            <strong>NIPC:</strong> {enq['nipc']} |
            <strong>Base Mensal:</strong> {enq['base']:.2f} EUR |
            <strong>Valor Hora Base:</strong> {enq['valor_hora']:.4f} EUR/h |
            <strong>Sub. Alimentacao:</strong> {enq['sub_alim_dia']:.2f} EUR/dia
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Passo A: Horas Efetivamente Trabalhadas na Tua Escala")
    c_h1, c_h2, c_h3, c_h4 = st.columns(4)
    with c_h1:
        dias_trab = st.number_input("Dias trabalhados no mes", min_value=0, max_value=31, value=22)
    with c_h2:
        h_noturnas = st.number_input("Horas Noturnas (21h-06h)", min_value=0.0, max_value=250.0, value=0.0, step=0.5)
    with c_h3:
        h_feriado = st.number_input("Horas em Dia Feriado", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    with c_h4:
        h_extras = st.number_input("Horas Extras (Suplementar)", min_value=0.0, max_value=150.0, value=0.0, step=0.5)

    st.markdown("#### Passo B: Valores Pagos no Teu Recibo de Vencimento (EUR)")
    c_p1, c_p2, c_p3, c_p4, c_p5 = st.columns(5)
    with c_p1:
        pago_base = st.number_input("Base Pago (EUR)", min_value=0.0, value=float(enq["base"]), step=10.0)
    with c_p2:
        pago_noturno = st.number_input("Noturno Pago (EUR)", min_value=0.0, value=0.0, step=5.0)
    with c_p3:
        pago_feriado = st.number_input("Feriado Pago (EUR)", min_value=0.0, value=0.0, step=5.0)
    with c_p4:
        pago_extras = st.number_input("Extras Pago (EUR)", min_value=0.0, value=0.0, step=5.0)
    with c_p5:
        pago_alim = st.number_input(
            "Sub. Alim. Pago (EUR)",
            min_value=0.0,
            value=round(dias_trab * enq["sub_alim_dia"], 2),
            step=5.0,
        )

    st.markdown("#### Passo C: Validacao Tecnica Anti-Fraude (Opcional para Entrar no Radar Publico)")
    st.caption(
        "Se quiseres que o teu desvio conte para as estatisticas publicas e desbloqueie grupos de acao "
        "coletiva, anexa o PDF original do recibo. O ficheiro e lido apenas em memoria RAM para confirmar "
        "que e autentico e apagado de imediato."
    )
    ficheiro_pdf = st.file_uploader("Carregar Recibo de Vencimento (PDF original)", type=["pdf"])

    tipo_principal = st.selectbox("Principal irregularidade detetada (se aplicavel)", TIPOS_INCUMPRIMENTO[:3] + [TIPOS_INCUMPRIMENTO[8]])

    if st.button("Calcular Auditoria e Gerar Dossie", type="primary"):
        resultado = calcular_auditoria_mensal(
            empresa=empresa_sel,
            ano=ano_sel,
            horas_noturnas_reais=h_noturnas,
            horas_feriado_reais=h_feriado,
            horas_extras_reais=h_extras,
            dias_trabalhados=dias_trab,
            base_pago=pago_base,
            noturno_pago=pago_noturno,
            feriado_pago=pago_feriado,
            extras_pago=pago_extras,
            alim_pago=pago_alim,
        )

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Devido (CCT)", f"{resultado['total_devido']:.2f} EUR")
        m2.metric("Total Pago em Recibo", f"{resultado['total_pago']:.2f} EUR")
        m3.metric(
            "Diferenca Apurada",
            f"{resultado['desvio_total']:.2f} EUR",
            delta=f"{-resultado['desvio_total']:.2f} EUR" if resultado["desvio_total"] > 0 else "0.00 EUR",
            delta_color="inverse",
        )

        df_det = pd.DataFrame(resultado["detalhes"])
        st.dataframe(df_det, use_container_width=True, hide_index=True)

        validado = False
        codigo_caso = "SIMULACAO-LOCAL"

        if ficheiro_pdf is not None:
            bytes_pdf = ficheiro_pdf.read()
            val = validar_recibo_em_memoria(bytes_pdf, enq["nipc"])
            del bytes_pdf  # Eliminacao explicita em memoria

            if val["valido"]:
                validado = True
                codigo_caso = gerar_codigo_caso(val["hash_unico"])
                if resultado["desvio_total"] >= 5.0:
                    reg = {
                        "hash_unico": val["hash_unico"],
                        "codigo_caso": codigo_caso,
                        "empresa": empresa_sel,
                        "nipc": enq["nipc"],
                        "distrito": distrito_sel,
                        "tipo_infracao": tipo_principal,
                        "desvio_eur": resultado["desvio_total"],
                        "ano_mes": f"{mes_sel}/{ano_sel}",
                    }
                    ok, msg = guardar_registo_anonimo(reg)
                    if ok:
                        st.success(
                            f"Recibo validado tecnicamente! O teu Codigo de Caso anonimo e: **{codigo_caso}**. "
                            f"Guarda este codigo no telemovel para acompanhares o grupo coletivo na Aba 4."
                        )
                    else:
                        st.warning(msg)
                else:
                    st.info("Recibo validado, mas como nao existe desvio superior a 5 EUR, nao foi registado incumprimento.")
            else:
                st.error(f"Validacao falhou: {val['motivo']} O dossie sera gerado apenas como simulacao local.")
        else:
            st.warning(
                "Calculo efetuado em modo de simulacao manual (sem PDF validado). Para entrar no Radar Publico "
                "e nos grupos de acao coletiva, carrega o PDF original do recibo."
            )

        pdf_bytes = gerar_pdf_auditoria(
            codigo_caso=codigo_caso,
            empresa=empresa_sel,
            distrito=distrito_sel,
            mes_ano=f"{mes_sel}/{ano_sel}",
            resultado=resultado,
            validado_pdf=validado,
        )

        st.download_button(
            label="Descarregar Dossie Tecnico em PDF (Guardar no Telemovel)",
            data=pdf_bytes,
            file_name=f"Dossie_Auditoria_{mes_sel}_{ano_sel}.pdf",
            mime="application/pdf",
        )


# ==============================================================================
# ABA 2: DOCUMENTAR OUTROS INCUMPRIMENTOS (PROVA LEGAL)
# ==============================================================================
with aba2:
    st.subheader("Assistente de Recolha de Prova e Cronologia de Ocorrencias")
    st.write(
        "Incumprimentos como mudancas de posto sem aviso previo, alteracoes de escala em cima da hora ou "
        "pressoes na transmissao de estabelecimento exigem registo cronologico objetivo. Preenche os dados "
        "abaixo para gerar um relatorio estruturado pronto para a ACT."
    )

    col_o1, col_o2 = st.columns(2)
    with col_o1:
        emp_oc = st.selectbox("Empresa envolvida", list(EMPRESAS_SEGURANCA.keys()), key="emp_oc")
        tipo_oc = st.selectbox("Tipologia do Incumprimento", TIPOS_INCUMPRIMENTO, key="tipo_oc")
    with col_o2:
        dist_oc = st.selectbox("Distrito", DISTRITOS_PORTUGAL, key="dist_oc")
        data_oc = st.date_input("Data da Ocorrencia", value=datetime.date.today())

    posto_gen = st.selectbox(
        "Tipologia do Posto (sem identificar o cliente especifico para evitar retalicao)",
        [
            "Superficie Comercial / Retalho",
            "Infraestrutura de Transportes / Estacao",
            "Unidade Hospitalar / Saude",
            "Edificio de Escritorios / Banca",
            "Unidade Industrial / Logistica",
            "Edificio Publico / Estado",
            "Rondas Moveis",
        ],
    )

    desc_factual = st.text_area(
        "Descricao objetiva dos factos (datas, horas, ordens recebidas - evita insultos ou nomes individuais)",
        placeholder="Exemplo: No dia 12/11/2026 as 19h30 recebi mensagem escrita a ordenar apresentacao noutro posto a 32 km de distancia no dia seguinte as 07h00, sem aviso previo de 8 dias nem justificacao escrita...",
        height=130,
    )

    st.markdown("**Checklist de Provas que ja tens guardadas no teu telemovel:**")
    provas = []
    if st.checkbox("Captura de ecrã de SMS / WhatsApp / Email com data e hora visiveis"):
        provas.append("Captura de ecrã de comunicacao escrita com data e hora")
    if st.checkbox("Copia da escala de servico original antes da alteracao"):
        provas.append("Escala de servico inicial comprovativa")
    if st.checkbox("Comprovativo de distancia extra em km (ex.: print Google Maps)"):
        provas.append("Registo de acrescimo de distancia de deslocacao")
    if st.checkbox("Copia de contrato anterior / comprovativo de antiguidade no posto"):
        provas.append("Comprovativo de antiguidade e condicoes contratuais")

    if st.button("Gerar Relatorio Cronologico em PDF"):
        if len(desc_factual.strip()) < 20:
            st.error("Por favor, descreve os factos com um minimo de detalhe objetivo antes de gerar o PDF.")
        else:
            pdf_oc = gerar_pdf_ocorrencia(
                empresa=emp_oc,
                distrito=dist_oc,
                tipo_infracao=tipo_oc,
                data_ocorrencia=data_oc.strftime("%d/%m/%Y"),
                posto_tipo=posto_gen,
                descricao_factual=desc_factual,
                provas_reunidas=provas,
            )
            st.download_button(
                label="Descarregar Relatorio de Ocorrencia (PDF)",
                data=pdf_oc,
                file_name=f"Relatorio_Ocorrencia_{data_oc.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
            )


# ==============================================================================
# ABA 3: RADAR ESTATISTICO DO SETOR (DADOS AGREGADOS PUBLICOS)
# ==============================================================================
with aba3:
    st.subheader("Radar Publico de Conformidade Laboral")
    st.write(
        "Indicadores agregados baseados exclusivamente em recibos auditados tecnicamente. "
        "Nenhum trabalhador ou posto isolado e identificado."
    )

    dados = carregar_todos_registos()
    if not dados:
        st.info(
            "Ainda nao existem registos validados suficientes para exibir estatisticas agregadas. "
            "Assim que os primeiros recibos forem auditados na Aba 1, os indicadores surgirao aqui automaticamente."
        )
    else:
        df = pd.DataFrame(dados)
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.metric("Total de Auditorias Validadas", len(df))
        c_k2.metric("Desvio Medio Apurado", f"{df['desvio_eur'].mean():.2f} EUR")
        c_k3.metric("Total Acumulado em Falta", f"{df['desvio_eur'].sum():.2f} EUR")

        st.markdown("#### Incidencia por Entidade Empregadora")
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
# ABA 4: ACAO COLETIVA & CANAIS AUTONOMOS ZERO-ADMIN
# ==============================================================================
with aba4:
    st.subheader("Coordenacao de Acoes Coletivas e Queixas Conjuntas")
    st.write(
        f"Quando pelo menos **{LIMIAR_GRUPO_COLETIVO} vigilantes** da mesma empresa e distrito registam "
        "um recibo validado com o mesmo tipo de incumprimento, o sistema desbloqueia automaticamente "
        "uma sala de comunicacao encriptada sem administracao externa."
    )

    codigo_consulta = st.text_input(
        "Insere o teu Codigo de Caso (ex.: VIG-8A2F-19C4)",
        max_chars=20,
    ).strip().upper()

    if codigo_consulta:
        dados = carregar_todos_registos()
        caso_encontrado = next((d for d in dados if d.get("codigo_caso") == codigo_consulta), None)

        if not caso_encontrado:
            st.error("Codigo de caso nao encontrado. Verifica se copiaste corretamente apos a auditoria na Aba 1.")
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
                <div class="legal-box">
                    <strong>Processo Associado:</strong> {emp_c} | <strong>Distrito:</strong> {dist_c}<br>
                    <strong>Infracao:</strong> {tipo_c}<br>
                    <strong>Progresso do Grupo:</strong> {total_grupo} de {LIMIAR_GRUPO_COLETIVO} casos validados necessarios
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
                st.success("Limiar de Massa Critica atingido! O canal encriptado deste grupo esta disponivel.")
                aceite_saida = st.checkbox(
                    "Declaro que compreendo que este link abre uma sala externa encriptada em memoria RAM, "
                    "sem moderacao, acesso ou armazenamento por parte do criador deste site, e comprometo-me "
                    "a usar um pseudonimo sem expor dados pessoais nem difamar terceiros."
                )
                if aceite_saida:
                    links = gerar_links_sala_autonoma(emp_c, dist_c, tipo_c)
                    st.markdown(
                        f"""
                        <div class="alert-amber">
                            <strong>Canal Seguro Desbloqueado (Usa Pseudonimo):</strong><br>
                            - Sala de Chat Encriptado (Texto em RAM): <a href="{links['chat_texto']}" target="_blank">{links['chat_texto']}</a><br>
                            - Sala de Reuniao de Voz (Opcional): <a href="{links['sala_voz']}" target="_blank">{links['sala_voz']}</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# ==============================================================================
# ABA 5: FAQ, TERMOS & PROTECAO LEGAL
# ==============================================================================
with aba5:
    st.subheader("Quadro Legal, Privacidade e Perguntas Frequentes")

    st.markdown("### Aviso Legal e Isencao de Responsabilidade")
    st.markdown(
        """
        <div class="legal-box">
            <strong>1. Natureza Informativa:</strong> Esta plataforma e uma ferramenta independente de calculo
            matematico e literacia laboral baseada nos Contratos Coletivos de Trabalho (CCT) e no Codigo do
            Trabalho portugues. Os resultados tem carater indicativo e nao constituem aconselhamento juridico
            profissional.<br><br>
            <strong>2. Politica de Privacidade Custodia Zero (RGPD):</strong> Em cumprimento do Artigo 5. do RGPD,
            esta plataforma nao recolhe nem armazena nomes, NIFs, moradas, contactos ou ficheiros PDF. Qualquer
            documento submetido e lido exclusivamente em memoria RAM e eliminado imediatamente.<br><br>
            <strong>3. Prevencao de Difamacao e Responsabilidade do Utilizador:</strong> O site nao publica
            acusacoes nominais contra chefias ou clientes individuais. O utilizador declara que os dados
            inseridos correspondem a verdade dos factos, assumindo responsabilidade legal nos termos do
            Artigo 365. do Codigo Penal (Denuncia Caluniosa).
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Perguntas Frequentes (FAQ)")
    with st.expander("1. A minha empresa ou chefia consegue descobrir que usei este site?"):
        st.write(
            "Nao. O site nao exige registo, nome, email nem numero de funcionario. Para protecao adicional, "
            "utiliza sempre os dados moveis do teu telemovel e nunca a rede Wi-Fi do posto ou da empresa."
        )
    with st.expander("2. O criador do site fica com copia do meu recibo de vencimento?"):
        st.write(
            "Nao. O ficheiro PDF e processado apenas na memoria temporaria do servidor para verificar a "
            "autenticidade e gerar um codigo criptografico anonimo, sendo apagado no mesmo segundo."
        )
    with st.expander("3. Como evitam denuncias falsas que retirem credibilidade ao site?"):
        st.write(
            "As estatisticas publicas e os grupos coletivos aceitam apenas auditorias acompanhadas pela "
            "leitura estrutural de um recibo original com NIPC valido, bloqueando submissoes duplicadas "
            "atraves de uma assinatura criptografica irreversivel (SHA-256)."
        )
    with st.expander("4. Como funciona o grupo quando atingimos 10 casos na mesma empresa?"):
        st.write(
            "O sistema gera automaticamente um link para uma sala encriptada externa onde os detentores "
            "dos codigos de caso podem coordenar uma queixa conjunta coordenada na ACT ou contratar "
            "um advogado laboralista em grupo, dividindo custos."
        )