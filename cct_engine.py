import datetime

# Base de empresas de seguranca privada em Portugal (NIPC + Associacao Patronal / CCT)
EMPRESAS_SEGURANCA = {
    "Securitas - Servicos e Tecnologia de Seguranca, S.A.": {
        "nipc": "500243726",
        "cct": "CCT AES / STAD",
    },
    "Prosegur - Companhia de Seguranca, Lda.": {
        "nipc": "500826659",
        "cct": "CCT AES / STAD",
    },
    "Strong Charon - Solucoes de Seguranca, S.A.": {
        "nipc": "503212767",
        "cct": "CCT AES / STAD",
    },
    "2045 - Empresa de Seguranca, S.A.": {
        "nipc": "504493131",
        "cct": "CCT AESIRF / FETESE",
    },
    "Ronsegur - Rondas e Seguranca, S.A.": {
        "nipc": "505264705",
        "cct": "CCT AESIRF / FETESE",
    },
    "Prestibel - Empresa de Seguranca, S.A.": {
        "nipc": "501342108",
        "cct": "CCT AES / STAD",
    },
    "PSG - Seguranca Privada, S.A.": {
        "nipc": "504556834",
        "cct": "CCT AESIRF / FETESE",
    },
    "Comansegur - Seguranca Privada, S.A.": {
        "nipc": "503727260",
        "cct": "CCT AESIRF / FETESE",
    },
    "Grupo 8 - Vigilancia e Prevencao Eletronica, Lda.": {
        "nipc": "501279880",
        "cct": "CCT AES / STAD",
    },
    "Outra Empresa (Abrangida por Portaria de Extensao)": {
        "nipc": "000000000",
        "cct": "Portaria de Extensao (CCT Setorial)",
    },
}

DISTRITOS_PORTUGAL = [
    "Aveiro", "Beja", "Braga", "Braganca", "Castelo Branco", "Coimbra",
    "Evora", "Faro", "Guarda", "Leiria", "Lisboa", "Portalegre",
    "Porto", "Santarem", "Setubal", "Viana do Castelo", "Vila Real",
    "Viseu", "R.A. Acores", "R.A. Madeira"
]

TIPOS_INCUMPRIMENTO = [
    "Horas Noturnas (21h-06h) mal pagas ou omitidas",
    "Trabalho Suplementar (Horas Extras) nao pago",
    "Trabalho em Dia Feriado nao remunerado corretamente",
    "Mudanca de Posto sem aviso previo legal (Art. 194. CT)",
    "Alteracao de Escala em cima da hora (Art. 217. CT)",
    "Pressao na Transmissao de Estabelecimento (Art. 285. CT)",
    "Falta de Formacao Continua Obrigatoria (Art. 131. CT)",
    "Desconto ilegal de Fardamento ou Cartao MAI",
    "Atraso no pagamento de Retribuicao / Subsidios",
]

# Tabelas salariais de referencia por ano e CCT (Categoria: Vigilante)
# Atualiza estes valores sempre que sair nova tabela no BTE
TABELAS_CCT = {
    "CCT AES / STAD": {
        2023: {"base": 838.44, "sub_alim_dia": 6.40, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2024: {"base": 892.94, "sub_alim_dia": 6.80, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2025: {"base": 942.05, "sub_alim_dia": 7.15, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2026: {"base": 985.00, "sub_alim_dia": 7.45, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
    },
    "CCT AESIRF / FETESE": {
        2023: {"base": 835.00, "sub_alim_dia": 6.35, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2024: {"base": 890.00, "sub_alim_dia": 6.75, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2025: {"base": 938.50, "sub_alim_dia": 7.10, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2026: {"base": 980.00, "sub_alim_dia": 7.40, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
    },
    "Portaria de Extensao (CCT Setorial)": {
        2023: {"base": 835.00, "sub_alim_dia": 6.35, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2024: {"base": 890.00, "sub_alim_dia": 6.75, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2025: {"base": 938.50, "sub_alim_dia": 7.10, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
        2026: {"base": 980.00, "sub_alim_dia": 7.40, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_1h_pct": 0.25, "extra_seg_pct": 0.375},
    },
}


def obter_enquadramento(empresa: str, ano: int) -> dict:
    info_empresa = EMPRESAS_SEGURANCA.get(
        empresa, {"nipc": "000000000", "cct": "Portaria de Extensao (CCT Setorial)"}
    )
    cct_nome = info_empresa["cct"]
    ano_ref = max(2023, min(2026, ano))
    regras = TABELAS_CCT[cct_nome][ano_ref]

    # Formula legal do valor hora: (Retribuicao Base * 12) / (52 semanas * 40 horas)
    valor_hora = round((regras["base"] * 12) / (52 * 40), 4)

    return {
        "nipc": info_empresa["nipc"],
        "cct": cct_nome,
        "ano_aplicado": ano_ref,
        "valor_hora": valor_hora,
        **regras,
    }


def calcular_auditoria_mensal(
    empresa: str,
    ano: int,
    horas_noturnas_reais: float,
    horas_feriado_reais: float,
    horas_extras_reais: float,
    dias_trabalhados: int,
    base_pago: float,
    noturno_pago: float,
    feriado_pago: float,
    extras_pago: float,
    alim_pago: float,
) -> dict:
    regras = obter_enquadramento(empresa, ano)
    vh = regras["valor_hora"]

    base_devido = regras["base"]
    noturno_devido = round(horas_noturnas_reais * vh * regras["noturno_pct"], 2)
    feriado_devido = round(horas_feriado_reais * vh * regras["feriado_pct"], 2)
    extras_devido = round(horas_extras_reais * vh * (1 + regras["extra_seg_pct"]), 2)
    alim_devido = round(dias_trabalhados * regras["sub_alim_dia"], 2)

    total_devido = round(
        base_devido + noturno_devido + feriado_devido + extras_devido + alim_devido, 2
    )
    total_pago = round(
        base_pago + noturno_pago + feriado_pago + extras_pago + alim_pago, 2
    )
    desvio_total = round(total_devido - total_pago, 2)

    detalhes = [
        {
            "rubrica": "Retribuicao Base",
            "devido": base_devido,
            "pago": base_pago,
            "diferenca": round(base_devido - base_pago, 2),
        },
        {
            "rubrica": f"Acrescimo Noturno ({int(regras['noturno_pct']*100)}%)",
            "devido": noturno_devido,
            "pago": noturno_pago,
            "diferenca": round(noturno_devido - noturno_pago, 2),
        },
        {
            "rubrica": f"Trabalho em Feriado (+{int(regras['feriado_pct']*100)}%)",
            "devido": feriado_devido,
            "pago": feriado_pago,
            "diferenca": round(feriado_devido - feriado_pago, 2),
        },
        {
            "rubrica": "Trabalho Suplementar (Horas Extras)",
            "devido": extras_devido,
            "pago": extras_pago,
            "diferenca": round(extras_devido - extras_pago, 2),
        },
        {
            "rubrica": "Subsidio de Alimentacao",
            "devido": alim_devido,
            "pago": alim_pago,
            "diferenca": round(alim_devido - alim_pago, 2),
        },
    ]

    return {
        "regras": regras,
        "total_devido": total_devido,
        "total_pago": total_pago,
        "desvio_total": desvio_total,
        "detalhes": detalhes,
    }