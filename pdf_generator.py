import datetime
from fpdf import FPDF


def _limpar_texto(texto: str) -> str:
    """Preserva todos os acentos portugueses (Latin-1) e substitui apenas o símbolo Euro."""
    if not texto:
        return ""
    substituicoes = {
        "€": "EUR",
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)
    return texto.encode("latin-1", "replace").decode("latin-1")


class DossiePDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 25, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 13)
        self.set_xy(12, 7)
        self.cell(0, 6, _limpar_texto("OBSERVATÓRIO TÉCNICO DA SEGURANÇA PRIVADA"), ln=True)
        self.set_font("helvetica", "", 9)
        self.set_x(12)
        self.cell(0, 5, _limpar_texto("Dossiê Técnico de Apuramento Laboral - Documento Exclusivo do Trabalhador"), ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-18)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        aviso = (
            "Documento gerado localmente para apoio documental junto da ACT, Sindicato ou Advogado. "
            "Cálculo indicativo baseado no CCT e Código do Trabalho em vigor."
        )
        self.multi_cell(0, 4, _limpar_texto(aviso), align="C")


def gerar_pdf_auditoria(
    codigo_caso: str,
    empresa: str,
    distrito: str,
    periodo_texto: str,
    resultado: dict,
    validado_pdf: bool,
) -> bytes:
    pdf = DossiePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=22)

    regras = resultado["regras"]
    nipc_str = f" (NIPC: {regras['nipc']})" if regras.get("nipc") else ""
    data_emissao = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("1. IDENTIFICAÇÃO DA AUDITORIA LABORAL"), ln=True)

    pdf.set_font("helvetica", "", 10)
    linhas_meta = [
        f"Código de Referência: {codigo_caso}",
        f"Data de Emissão: {data_emissao}",
        f"Entidade Empregadora: {empresa}{nipc_str}",
        f"Distrito do Posto: {distrito}",
        f"Período Auditado: {periodo_texto} ({resultado['num_meses']} mês/meses)",
        f"Instrumento Aplicável: {regras['cct']} (Tabela Ref. {regras['ano_aplicado']})",
        f"Valor Hora Base Apurado: {regras['valor_hora']:.4f} EUR/hora",
        f"Origem dos Dados: {'Recibo Original Validado Tecnicamente' if validado_pdf else 'Simulação Manual pelo Trabalhador'}",
    ]
    for linha in linhas_meta:
        pdf.cell(0, 6, _limpar_texto(linha), ln=True)

    pdf.ln(5)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("2. DISCRIMINAÇÃO DE VALORES APURADOS (EUR)"), ln=True)

    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(85, 8, _limpar_texto("Rubrica Salarial"), border=1, fill=True)
    pdf.cell(35, 8, _limpar_texto("Valor Devido"), border=1, align="R", fill=True)
    pdf.cell(35, 8, _limpar_texto("Valor Pago"), border=1, align="R", fill=True)
    pdf.cell(35, 8, _limpar_texto("Diferença"), border=1, align="R", fill=True, ln=True)

    pdf.set_font("helvetica", "", 9)
    for item in resultado["detalhes"]:
        pdf.cell(85, 7, _limpar_texto(item["Rubrica"]), border=1)
        pdf.cell(35, 7, f"{item['Devido (EUR)']:.2f} EUR", border=1, align="R")
        pdf.cell(35, 7, f"{item['Pago (EUR)']:.2f} EUR", border=1, align="R")
        pdf.cell(35, 7, f"{item['Diferença (EUR)']:.2f} EUR", border=1, align="R", ln=True)

    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(85, 8, _limpar_texto("TOTAL ACUMULADO NO PERÍODO"), border=1, fill=True)
    pdf.cell(35, 8, f"{resultado['total_devido']:.2f} EUR", border=1, align="R", fill=True)
    pdf.cell(35, 8, f"{resultado['total_pago']:.2f} EUR", border=1, align="R", fill=True)
    pdf.cell(35, 8, f"{resultado['desvio_total']:.2f} EUR", border=1, align="R", fill=True, ln=True)

    pdf.ln(6)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("3. MINUTA BASE PARA QUEIXA NA ACT OU INTERPELAÇÃO ESCRITA"), ln=True)
    pdf.set_font("helvetica", "", 9.5)

    texto_act = (
        f"Exmos. Senhores,\n\n"
        f"Na qualidade de trabalhador(a) da categoria profissional de Vigilante ao serviço da entidade "
        f"{empresa}{nipc_str}, venho reportar a existência de divergências no apuramento "
        f"retributivo referente ao período de {periodo_texto}, ao abrigo do {regras['cct']} e do Código do Trabalho.\n\n"
        f"Concretamente, apura-se um diferencial total de {resultado['desvio_total']:.2f} EUR entre os valores "
        f"legalmente devidos ({resultado['total_devido']:.2f} EUR) e os valores liquidados em recibo "
        f"({resultado['total_pago']:.2f} EUR), conforme discriminação técnica acima.\n\n"
        f"Anexo a este dossiê cópia dos recibos de vencimento e registos de escala de serviço para efeitos de "
        f"verificação inspetiva e regularização."
    )
    pdf.multi_cell(0, 5.5, _limpar_texto(texto_act))

    return bytes(pdf.output())


def gerar_pdf_ocorrencia(
    empresa: str,
    distrito: str,
    tipo_infracao: str,
    periodo_ocorrencia: str,
    posto_tipo: str,
    descricao_factual: str,
    provas_reunidas: list,
) -> bytes:
    pdf = DossiePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=22)

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("RELATÓRIO CRONOLÓGICO DE OCORRÊNCIA LABORAL"), ln=True)

    pdf.set_font("helvetica", "", 10)
    campos = [
        f"Entidade Empregadora: {empresa}",
        f"Distrito: {distrito}",
        f"Tipologia Legal: {tipo_infracao}",
        f"Data / Período dos Factos: {periodo_ocorrencia}",
        f"Tipologia do Posto (sem identificação individual): {posto_tipo}",
    ]
    for c in campos:
        pdf.cell(0, 6, _limpar_texto(c), ln=True)

    pdf.ln(4)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, _limpar_texto("Descrição Objetiva dos Factos:"), ln=True)
    pdf.set_font("helvetica", "", 9.5)
    pdf.multi_cell(0, 5.5, _limpar_texto(descricao_factual))

    pdf.ln(4)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, _limpar_texto("Checklist de Provas Documentais Reunidas pelo Trabalhador:"), ln=True)
    pdf.set_font("helvetica", "", 9.5)
    if provas_reunidas:
        for p in provas_reunidas:
            pdf.cell(0, 6, _limpar_texto(f"[X] {p}"), ln=True)
    else:
        pdf.cell(0, 6, _limpar_texto("Nenhuma prova selecionada no momento da geração."), ln=True)

    return bytes(pdf.output())
