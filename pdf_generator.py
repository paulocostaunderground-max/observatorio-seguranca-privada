import datetime
from fpdf import FPDF


def _limpar_texto(texto: str) -> str:
    """Garante compatibilidade total com fontes Latin-1 no FPDF2 sem erros."""
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
        self.rect(0, 0, 210, 24, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 13)
        self.set_xy(12, 7)
        self.cell(0, 6, _limpar_texto("OBSERVATORIO TECNICO DA SEGURANCA PRIVADA"), ln=True)
        self.set_font("helvetica", "", 9)
        self.set_x(12)
        self.cell(0, 5, _limpar_texto("Dossie Tecnico de Apuramento Laboral - Documento para Uso do Trabalhador"), ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-18)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        aviso = (
            "Documento gerado localmente para apoio documental junto da ACT, Sindicato ou Advogado. "
            "Calculo indicativo baseado no CCT e Codigo do Trabalho em vigor."
        )
        self.multi_cell(0, 4, _limpar_texto(aviso), align="C")


def gerar_pdf_auditoria(
    codigo_caso: str,
    empresa: str,
    distrito: str,
    mes_ano: str,
    resultado: dict,
    validado_pdf: bool,
) -> bytes:
    pdf = DossiePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=22)

    regras = resultado["regras"]
    data_emissao = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    # Bloco de Identificacao Tecnica
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("1. IDENTIFICACAO DA AUDITORIA"), ln=True)

    pdf.set_font("helvetica", "", 10)
    linhas_meta = [
        f"Codigo de Referencia: {codigo_caso}",
        f"Data de Emissao: {data_emissao}",
        f"Entidade Empregadora: {empresa} (NIPC: {regras['nipc']})",
        f"Distrito do Posto: {distrito}",
        f"Periodo Auditado: {mes_ano}",
        f"Instrumento Aplicavel: {regras['cct']} (Tabela Ref. {regras['ano_aplicado']})",
        f"Valor Hora Base Apurado: {regras['valor_hora']:.4f} EUR/hora",
        f"Origem dos Dados: {'Recibo Original Validado Tecnicamente' if validado_pdf else 'Simulacao Manual pelo Trabalhador'}",
    ]
    for linha in linhas_meta:
        pdf.cell(0, 6, _limpar_texto(linha), ln=True)

    pdf.ln(5)

    # Tabela Comparativa
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("2. DISCRIMINACAO DE VALORES (EUR)"), ln=True)

    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(85, 8, _limpar_texto("Rubrica Salarial"), border=1, fill=True)
    pdf.cell(35, 8, _limpar_texto("Valor Devido"), border=1, align="R", fill=True)
    pdf.cell(35, 8, _limpar_texto("Valor Pago"), border=1, align="R", fill=True)
    pdf.cell(35, 8, _limpar_texto("Diferenca"), border=1, align="R", fill=True, ln=True)

    pdf.set_font("helvetica", "", 9)
    for item in resultado["detalhes"]:
        pdf.cell(85, 7, _limpar_texto(item["rubrica"]), border=1)
        pdf.cell(35, 7, f"{item['devido']:.2f} EUR", border=1, align="R")
        pdf.cell(35, 7, f"{item['pago']:.2f} EUR", border=1, align="R")
        pdf.cell(35, 7, f"{item['diferenca']:.2f} EUR", border=1, align="R", ln=True)

    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(85, 8, _limpar_texto("TOTAL MENSAL APURADO"), border=1, fill=True)
    pdf.cell(35, 8, f"{resultado['total_devido']:.2f} EUR", border=1, align="R", fill=True)
    pdf.cell(35, 8, f"{resultado['total_pago']:.2f} EUR", border=1, align="R", fill=True)
    pdf.cell(35, 8, f"{resultado['desvio_total']:.2f} EUR", border=1, align="R", fill=True, ln=True)

    pdf.ln(6)

    # Resumo para Queixa ACT / Interpelacao
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("3. TEXTO BASE PARA QUEIXA NA ACT OU INTERPELACAO ESCRITA"), ln=True)
    pdf.set_font("helvetica", "", 9.5)

    texto_act = (
        f"Exmos. Senhores,\n\n"
        f"Na qualidade de trabalhador(a) da categoria profissional de Vigilante ao servico da entidade "
        f"{empresa} (NIPC {regras['nipc']}), venho reportar a existencia de divergencias no apuramento "
        f"retributivo referente ao periodo de {mes_ano}, ao abrigo do {regras['cct']} e do Codigo do Trabalho.\n\n"
        f"Concretamente, apura-se um diferencial total de {resultado['desvio_total']:.2f} EUR entre os valores "
        f"legalmente devidos ({resultado['total_devido']:.2f} EUR) e os valores liquidados em recibo "
        f"({resultado['total_pago']:.2f} EUR), conforme discriminacao acima.\n\n"
        f"Anexo a este dossie copia do recibo de vencimento e registo de escala de servico para efeitos de "
        f"verificacao e regularizacao."
    )
    pdf.multi_cell(0, 5.5, _limpar_texto(texto_act))

    return bytes(pdf.output())


def gerar_pdf_ocorrencia(
    empresa: str,
    distrito: str,
    tipo_infracao: str,
    data_ocorrencia: str,
    posto_tipo: str,
    descricao_factual: str,
    provas_reunidas: list,
) -> bytes:
    pdf = DossiePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=22)

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, _limpar_texto("RELATORIO CRONOLOGICO DE OCORRENCIA LABORAL"), ln=True)

    pdf.set_font("helvetica", "", 10)
    campos = [
        f"Entidade Empregadora: {empresa}",
        f"Distrito: {distrito}",
        f"Tipologia Legal: {tipo_infracao}",
        f"Data dos Factos: {data_ocorrencia}",
        f"Tipologia do Posto (sem identificacao individual): {posto_tipo}",
    ]
    for c in campos:
        pdf.cell(0, 6, _limpar_texto(c), ln=True)

    pdf.ln(4)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, _limpar_texto("Descricao Objetiva dos Factos:"), ln=True)
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
        pdf.cell(0, 6, _limpar_texto("Nenhuma prova selecionada no momento da geracao."), ln=True)

    return bytes(pdf.output())