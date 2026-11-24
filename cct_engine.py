TODOS_CCTS = [
    "CCT AESIRF / SUSP",
    "CCT AESIRF / FETESE",
    "CCT AES / STAD",
    "CCT AES / ASSP",
    "Portaria de Extensão (CCT Setorial)",
]

CATEGORIAS_PROFISSIONAIS = [
    "Vigilante / Porteiro / Guarda (Nível XIX)",
    "Vigilante Aeroportuário / Portuário APA-A / APA-P (Nível XIII)",
    "Vigilante Chefe / Controlador (Nível XIV)",
    "Operador de Valores (Nível XVI)",
    "Vigilante de Transporte de Valores (Nível VII)",
]

# Base de empresas de segurança privada em Portugal (Palavras-chave + CCTs mais frequentes)
EMPRESAS_SEGURANCA = {
    "2045 - Empresa de Segurança, S.A.": {
        "keywords": ["2045"],
        "ccts_sugeridos": ["CCT AESIRF / SUSP", "CCT AESIRF / FETESE", "CCT AES / ASSP"],
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
        "ccts_sugeridos": ["Portaria de Extensão (CCT Setorial)", "CCT AES / STAD", "CCT AESIRF / SUSP"],
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
    "Trabalho em Dia Feriado ou Descanso Semanal não remunerado",
    "Falta de pagamento de Horas de Formação realizadas",
    "Falta de Horas de Formação Obrigatória (40h/ano - Art. 131.º CT)",
    "Mudança de Posto sem aviso prévio legal (Art. 194.º CT)",
    "Alteração de Escala em cima da hora (Art. 217.º CT)",
    "Pressão ou corte de antiguidade na Transmissão de Estabelecimento (Art. 285.º CT)",
    "Desconto ilegal de Fardamento, Calçado ou Cartão MAI",
    "Atraso no pagamento de Retribuição ou Subsídios",
    "Falta de pagamento de Despesas de Deslocação / Km",
]

# Tabelas salariais oficiais publicadas no BTE (BTE 29/2023, BTE 4/2024, BTE 48/2024 e BTE 5/2025)
TABELAS_OFICIAIS_BTE = {
    "Vigilante / Porteiro / Guarda (Nível XIX)": {
        2023: {"base": 860.00, "sub_alim_dia": 6.65},
        2024: {"base": 912.53, "sub_alim_dia": 7.05},
        2025: {"base": 960.62, "sub_alim_dia": 7.42},
        2026: {"base": 1015.95, "sub_alim_dia": 7.85},
    },
    "Vigilante Aeroportuário / Portuário APA-A / APA-P (Nível XIII)": {
        2023: {"base": 963.36, "sub_alim_dia": 6.65},
        2024: {"base": 1022.13, "sub_alim_dia": 7.05},
        2025: {"base": 1076.00, "sub_alim_dia": 7.42},
        2026: {"base": 1137.98, "sub_alim_dia": 7.85},
    },
    "Vigilante Chefe / Controlador (Nível XIV)": {
        2023: {"base": 951.97, "sub_alim_dia": 6.65},
        2024: {"base": 1010.04, "sub_alim_dia": 7.05},
        2025: {"base": 1063.27, "sub_alim_dia": 7.42},
        2026: {"base": 1124.51, "sub_alim_dia": 7.85},
    },
    "Operador de Valores (Nível XVI)": {
        2023: {"base": 925.96, "sub_alim_dia": 6.85},
        2024: {"base": 982.45, "sub_alim_dia": 7.26},
        2025: {"base": 1034.23, "sub_alim_dia": 7.64},
        2026: {"base": 1093.80, "sub_alim_dia": 8.08},
    },
    "Vigilante de Transporte de Valores (Nível VII)": {
        2023: {"base": 1197.98, "sub_alim_dia": 7.64},
        2024: {"base": 1271.06, "sub_alim_dia": 8.10},
        2025: {"base": 1338.06, "sub_alim_dia": 8.53},
        2026: {"base": 1415.13, "sub_alim_dia": 9.02},
    },
}

# Acréscimos convencionais do CCT da Segurança Privada:
# - Trabalho noturno (21h às 06h): +25% sobre o valor hora base
# - Trabalho suplementar diurno: +50% (1,50 x Valor Hora)
# - Trabalho suplementar noturno: +75% (1,75 x Valor Hora)
# - Trabalho normal em dia feriado: +100% acréscimo (1,00 x Valor Hora adicional ao base)
# - Trabalho suplementar em dia feriado ou descanso semanal: +100% total (2,00 x Valor Hora)
ACRESCIMOS_CCT = {
    "noturno_pct": 0.25,
    "extra_diurna_mult": 1.50,
    "extra_noturna_mult": 1.75,
    "feriado_normal_mult": 1.00,
    "feriado_descanso_extra_mult": 2.00,
}


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


def obter_enquadramento(
    empresa: str,
    ano: int,
    cct_escolhido: str,
    categoria: str = "Vigilante / Porteiro / Guarda (Nível XIX)",
) -> dict:
    ano_ref = max(2023, min(2026, ano))
    tabela_cat = TABELAS_OFICIAIS_BTE.get(
        categoria, TABELAS_OFICIAIS_BTE["Vigilante / Porteiro / Guarda (Nível XIX)"]
    )
    valores_ano = tabela_cat[ano_ref]

    # Fórmula legal do valor hora: (Retribuição Base * 12) / (52 semanas * 40 horas)
    valor_hora = round((valores_ano["base"] * 12) / (52 * 40), 4)

    return {
        "cct": cct_escolhido,
        "categoria": categoria,
        "ano_aplicado": ano_ref,
        "base": valores_ano["base"],
        "sub_alim_dia": valores_ano["sub_alim_dia"],
        "valor_hora": valor_hora,
        **ACRESCIMOS_CCT,
    }


def calcular_auditoria_periodo(
    empresa: str,
    ano: int,
    cct_escolhido: str,
    categoria: str,
    num_meses: int,
    horas_noturnas_totais: float,
    horas_feriado_normais: float,
    horas_extras_diurnas: float,
    horas_extras_noturnas: float,
    horas_extras_feriado_descanso: float,
    horas_formacao_nao_pagas: float,
    dias_trabalhados_totais: int,
    base_pago_total: float,
    noturno_pago_total: float,
    feriado_pago_total: float,
    extras_pago_total: float,
    formacao_pago_total: float,
    alim_pago_total: float,
) -> dict:
    regras = obter_enquadramento(empresa, ano, cct_escolhido, categoria)
    vh = regras["valor_hora"]

    base_devido = round(regras["base"] * num_meses, 2)
    noturno_devido = round(horas_noturnas_totais * vh * regras["noturno_pct"], 2)

    # Feriado normal (já incluído no base, acresce +100%) + Horas extras em feriado/descanso (200% total)
    feriado_devido = round(
        (horas_feriado_normais * vh * regras["feriado_normal_mult"])
        + (horas_extras_feriado_descanso * vh * regras["feriado_descanso_extra_mult"]),
        2,
    )

    # Horas extras diurnas (+50% = 1,50x VH) + Horas extras noturnas (+75% = 1,75x VH)
    extras_devido = round(
        (horas_extras_diurnas * vh * regras["extra_diurna_mult"])
        + (horas_extras_noturnas * vh * regras["extra_noturna_mult"]),
        2,
    )

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
            "Rubrica": "Acréscimo Noturno 21h-06h (+25%)",
            "Devido (EUR)": noturno_devido,
            "Pago (EUR)": noturno_pago_total,
            "Diferença (EUR)": round(noturno_devido - noturno_pago_total, 2),
        },
        {
            "Rubrica": "Trabalho em Feriado / Descanso Semanal (+100%)",
            "Devido (EUR)": feriado_devido,
            "Pago (EUR)": feriado_pago_total,
            "Diferença (EUR)": round(feriado_devido - feriado_pago_total, 2),
        },
        {
            "Rubrica": "Trabalho Suplementar (Diurno +50% / Noturno +75%)",
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
            "Rubrica": f"Subsídio de Alimentação ({regras['sub_alim_dia']:.2f} EUR/dia)",
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
