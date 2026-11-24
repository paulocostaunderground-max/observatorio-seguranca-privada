TODOS_CCTS = [
    "CCT AES / STAD",
    "CCT AES / ASSP",
    "CCT AESIRF / FETESE",
    "CCT AESIRF / SUSP",
    "Portaria de Extensão (CCT Setorial)",
]

# Base de empresas de segurança privada em Portugal (Palavras-chave de identificação + CCTs mais frequentes)
EMPRESAS_SEGURANCA = {
    "2045 - Empresa de Segurança, S.A.": {
        "keywords": ["2045"],
        "ccts_sugeridos": ["CCT AESIRF / SUSP", "CCT AES / ASSP", "CCT AESIRF / FETESE"],
    },
    "Securitas - Serviços e Tecnologia de Segurança, S.A.": {
        "keywords": ["securitas"],
        "ccts_sugeridos": ["CCT AES / STAD", "CCT AES / ASSP"],
    },
    "Prosegur - Companhia de Segurança, Lda.": {
        "keywords": ["prosegur"],
        "ccts_sugeridos": ["CCT AES / STAD", "CCT AES / ASSP"],
    },
    "Strong Charon - Soluções de Segurança, S.A.": {
        "keywords": ["strong charon", "charon"],
        "ccts_sugeridos": ["CCT AES / STAD", "CCT AES / ASSP"],
    },
    "Ronsegur - Rondas e Segurança, S.A.": {
        "keywords": ["ronsegur"],
        "ccts_sugeridos": ["CCT AESIRF / FETESE", "CCT AESIRF / SUSP"],
    },
    "Prestibel - Empresa de Segurança, S.A.": {
        "keywords": ["prestibel"],
        "ccts_sugeridos": ["CCT AES / STAD", "CCT AES / ASSP"],
    },
    "PSG - Segurança Privada, S.A.": {
        "keywords": ["psg"],
        "ccts_sugeridos": ["CCT AESIRF / FETESE", "CCT AESIRF / SUSP"],
    },
    "Comansegur - Segurança Privada, S.A.": {
        "keywords": ["comansegur"],
        "ccts_sugeridos": ["CCT AESIRF / FETESE", "CCT AESIRF / SUSP"],
    },
    "Grupo 8 - Vigilância e Prevenção Eletrónica, Lda.": {
        "keywords": ["grupo 8"],
        "ccts_sugeridos": ["CCT AES / STAD", "CCT AES / ASSP"],
    },
    "Loomis Portugal, S.A.": {
        "keywords": ["loomis"],
        "ccts_sugeridos": ["CCT AES / STAD", "CCT AES / ASSP"],
    },
    "Prosegur Cash, S.A.": {
        "keywords": ["prosegur cash", "prosegur"],
        "ccts_sugeridos": ["CCT AES / STAD", "CCT AES / ASSP"],
    },
    "Outra Empresa (Abrangida por Portaria de Extensão)": {
        "keywords": [],
        "ccts_sugeridos": ["Portaria de Extensão (CCT Setorial)", "CCT AES / STAD", "CCT AESIRF / FETESE"],
    },
}

DISTRITOS_PORTUGAL = [
    "Aveiro", "Beja", "Braga", "Bragança", "Castelo Branco", "Coimbra",
    "Évora", "Faro", "Guarda", "Leiria", "Lisboa", "Portalegre",
    "Porto", "Santarém", "Setúbal", "Viana do Castelo", "Vila Real",
    "Viseu", "R.A. Açores", "R.A. Madeira"
]

TIPOS_INCUMPRIMENTO = [
    "Trabalho Suplementar (Horas Extras) não pago ou acumulado",
    "Horas Noturnas (21h-06h) mal pagas ou omitidas",
    "Trabalho em Dia Feriado não remunerado corretamente",
    "Falta de pagamento de Horas de Formação realizadas",
    "Falta de Horas de Formação Obrigatória (40h/ano - Art. 131.º CT)",
    "Mudança de Posto sem aviso prévio legal (Art. 194.º CT)",
    "Alteração de Escala em cima da hora (Art. 217.º CT)",
    "Pressão ou corte de antiguidade na Transmissão de Estabelecimento (Art. 285.º CT)",
    "Desconto ilegal de Fardamento, Calçado ou Cartão MAI",
    "Atraso no pagamento de Retribuição ou Subsídios",
    "Falta de pagamento de Despesas de Deslocação / Km",
]

# Tabelas salariais de referência por ano e CCT (Categoria: Vigilante)
_REGRAS_BASE_ANO = {
    2023: {"base": 838.44, "sub_alim_dia": 6.40, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_pct": 0.375},
    2024: {"base": 892.94, "sub_alim_dia": 6.80, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_pct": 0.375},
    2025: {"base": 942.05, "sub_alim_dia": 7.15, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_pct": 0.375},
    2026: {"base": 985.00, "sub_alim_dia": 7.45, "noturno_pct": 0.25, "feriado_pct": 1.00, "extra_pct": 0.375},
}

TABELAS_CCT = {cct: _REGRAS_BASE_ANO for cct in TODOS_CCTS}


def validar_nipc_portugues(nipc: str) -> bool:
    """Valida matematicamente um NIPC empresarial português através do algoritmo Módulo 11."""
    if not nipc or len(nipc) != 9 or not nipc.isdigit():
        return False
    if nipc[0] not in ("5", "6", "7", "8", "9"):
        return False
    soma = sum(int(nipc[i]) * (9 - i) for i in range(8))
    resto = soma % 11
    digito_controlo = 0 if resto in (0, 1) else 11 - resto
    return int(nipc[8]) == digito_controlo


def obter_sugestoes_cct(empresa: str) -> list:
    info = EMPRESAS_SEGURANCA.get(
        empresa,
        {"keywords": [], "ccts_sugeridos": ["Portaria de Extensão (CCT Setorial)"]},
    )
    sugeridos = info["ccts_sugeridos"]
    return sugeridos + [c for c in TODOS_CCTS if c not in sugeridos]


def obter_enquadramento(empresa: str, ano: int, cct_escolhido: str) -> dict:
    ano_ref = max(2023, min(2026, ano))
    regras = TABELAS_CCT[cct_escolhido][ano_ref]

    # Fórmula legal do valor hora: (Retribuição Base * 12) / (52 semanas * 40 horas)
    valor_hora = round((regras["base"] * 12) / (52 * 40), 4)

    return {
        "cct": cct_escolhido,
        "ano_aplicado": ano_ref,
        "valor_hora": valor_hora,
        **regras,
    }


def calcular_auditoria_periodo(
    empresa: str,
    ano: int,
    cct_escolhido: str,
    num_meses: int,
    horas_noturnas_totais: float,
    horas_feriado_totais: float,
    horas_extras_totais: float,
    horas_formacao_nao_pagas: float,
    dias_trabalhados_totais: int,
    base_pago_total: float,
    noturno_pago_total: float,
    feriado_pago_total: float,
    extras_pago_total: float,
    formacao_pago_total: float,
    alim_pago_total: float,
) -> dict:
    regras = obter_enquadramento(empresa, ano, cct_escolhido)
    vh = regras["valor_hora"]

    base_devido = round(regras["base"] * num_meses, 2)
    noturno_devido = round(horas_noturnas_totais * vh * regras["noturno_pct"], 2)
    feriado_devido = round(horas_feriado_totais * vh * regras["feriado_pct"], 2)
    extras_devido = round(horas_extras_totais * vh * (1 + regras["extra_pct"]), 2)
    formacao_devido = round(horas_formacao_nao_pagas * vh, 2)
    alim_devido = round(dias_trabalhados_totais * regras["sub_alim_dia"], 2)

    total_devido = round(
        base_devido + noturno_devido + feriado_devido + extras_devido + formacao_devido + alim_devido,
        2,
    )
    total_pago = round(
        base_pago_total + noturno_pago_total + feriado_pago_total + extras_pago_total + formacao_pago_total + alim_pago_total,
        2,
    )
    desvio_total = round(total_devido - total_pago, 2)

    detalhes = [
        {
            "Rubrica": f"Retribuição Base ({num_meses} mês/meses)",
            "Devido (EUR)": base_devido,
            "Pago (EUR)": base_pago_total,
            "Diferença (EUR)": round(base_devido - base_pago_total, 2),
        },
        {
            "Rubrica": f"Acréscimo Noturno ({int(regras['noturno_pct']*100)}%)",
            "Devido (EUR)": noturno_devido,
            "Pago (EUR)": noturno_pago_total,
            "Diferença (EUR)": round(noturno_devido - noturno_pago_total, 2),
        },
        {
            "Rubrica": f"Trabalho em Feriado (+{int(regras['feriado_pct']*100)}%)",
            "Devido (EUR)": feriado_devido,
            "Pago (EUR)": feriado_pago_total,
            "Diferença (EUR)": round(feriado_devido - feriado_pago_total, 2),
        },
        {
            "Rubrica": "Trabalho Suplementar (Horas Extras)",
            "Devido (EUR)": extras_devido,
            "Pago (EUR)": extras_pago_total,
            "Diferença (EUR)": round(extras_devido - extras_pago_total, 2),
        },
        {
            "Rubrica": "Horas de Formação (Art. 131.º CT)",
            "Devido (EUR)": formacao_devido,
            "Pago (EUR)": formacao_pago_total,
            "Diferença (EUR)": round(formacao_devido - formacao_pago_total, 2),
        },
        {
            "Rubrica": "Subsídio de Alimentação",
            "Devido (EUR)": alim_devido,
            "Pago (EUR)": alim_pago_total,
            "Diferença (EUR)": round(alim_devido - alim_pago_total, 2),
        },
    ]

    return {
        "regras": regras,
        "num_meses": num_meses,
        "total_devido": total_devido,
        "total_pago": total_pago,
        "desvio_total": desvio_total,
        "detalhes": detalhes,
    }
