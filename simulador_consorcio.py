import streamlit as st
import pandas as pd
import numpy as np

# --- Funções auxiliares ---
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual(valor):
    return f"{valor * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def highlight_contemplacao(row):
    if row["Número da parcela"] == prazo_contemplacao:
        return ['border: 2px solid #00b050; color: black; background-color: lightgreen'] * len(row)
    elif row["Número da parcela"] == "Total":
        return ['background-color: lightgray; color: black'] * len(row)
    else:
        return [''] * len(row)

# --- Incluindo configurações iniciais da página ---
st.set_page_config(page_title="Pequod Investimentos - Simulador de consórcio", layout="wide", page_icon="https://media.licdn.com/dms/image/v2/D4D0BAQG2_JBVV8qXDQ/company-logo_200_200/company-logo_200_200/0/1666039591735/pequod_investimentos_logo?e=1753920000&v=beta&t=MNVypwcv4ktZTwaEOWAT2iAH7ZYB5AiQ5onMIoSzqKc", initial_sidebar_state="collapsed")

# --- Personalizando logo marca ---
st.image("Marca_Pequod.png", use_container_width = True)
st.title("Simulador de consórcio")
st.caption("Disclaimer: Esta ferramenta de simulação de consórcio oferece resultados aproximados e apenas para fins ilustrativos. Os valores aqui apresentados podem variar e não constituem promessa de contemplação ou oferta formal.")

# --- Entradas do usuário ---
col1, col2 = st.columns(2)

with col1:
    valor_credito = st.number_input("Valor do crédito (R$)", min_value=0.0, step=1000.0, format="%.2f")
    taxa_adm = st.number_input("Taxa de administração (%)", min_value=0.0, step=0.1, format="%.2f") / 100
    seguro_prestamista = st.number_input("Seguro prestamista (%)", min_value=0.0, step=0.0001, format="%.5f") / 100
    fundo_reserva = st.number_input("Fundo de reserva (%)", min_value=0.0, step=0.1, format="%.2f") / 100
    taxa_antecipacao = st.number_input("Taxa de antecipação (%)", min_value=0.0, step=0.1, format="%.2f") / 100
    lance_proprio = st.number_input("Lance com recursos próprios (R$)", min_value=0.0, step=100.0, format="%.2f")
    opcao_lance = st.selectbox("Utilização do lance", ["Reduzir Parcela", "Reduzir Prazo"])

with col2:
    prazo_meses = st.number_input("Prazo total (meses)", min_value=1, step=1)
    prazo_contemplacao = st.number_input("Expectativa de contemplação (meses)", min_value=0, max_value=prazo_meses, step=1)
    tipo_consorcio = st.selectbox("Tipo de consórcio", ["Imóvel", "Veículo", "Serviços"])
    #tem_upgrade = st.checkbox("Simulação com upgrade?")
    #if tem_upgrade:
    #    upgrade = st.number_input("Upgrade (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f") / 100
    tipo_estrategia = st.selectbox("Tipo de estratégia", ["Tradicional", "Alavancagem"])
    if tipo_estrategia == "Alavancagem":
        tipo_investimento = st.selectbox("Tipo de investimento", ["Prefixado", "Inflação", "Pós-fixado (% CDI)"])
        if tipo_investimento in ["Prefixado", "Inflação"]:
            taxa_juros = st.number_input("Taxa de juros anual (%)", min_value=0.0, step=0.1, format="%.2f") / 100
        else:
            perc_cdi = st.number_input("% do CDI", min_value=0.0, step=1.0, format="%.2f") / 100
            cdi_estimado = st.number_input("CDI estimado ao ano (%)", min_value=0.0, step=0.1, format="%.2f") / 100

if st.button("Simular"):
    prazo_anos = prazo_meses / 12
    indice_medio = 0.068 if tipo_consorcio == "Imóvel" else 0.058
    nome_indice = "INCC" if tipo_consorcio == "Imóvel" else "IPCA"

    taxa_total = taxa_adm + fundo_reserva
    total_pagar = valor_credito * (1 + taxa_total)
    parcela_cheia = total_pagar / prazo_meses

    amortizacao_contemplacao = parcela_cheia * prazo_contemplacao
    saldo_devedor = total_pagar - amortizacao_contemplacao
    parcelas_restantes = prazo_meses - prazo_contemplacao

    anos_corrigidos = prazo_contemplacao // 12
    saldo_devedor_corrigido = saldo_devedor * ((1 + indice_medio) ** anos_corrigidos)

    saldo_pos_lance = max(saldo_devedor_corrigido - lance_proprio, 0)
    quitou_na_contemplacao = lance_proprio >= saldo_devedor_corrigido

    if quitou_na_contemplacao:
        novo_prazo = 0
        nova_parcela = 0
    else:
        if opcao_lance == "Reduzir Prazo":
            novo_prazo = int(np.ceil(saldo_pos_lance / parcela_cheia))
            nova_parcela = parcela_cheia
        else:
            novo_prazo = parcelas_restantes
            nova_parcela = saldo_pos_lance / novo_prazo if novo_prazo > 0 else 0.0

    parcelas = []
    saldo_restante_total = total_pagar
    saldo_credor = valor_credito

    for i in range(1, prazo_meses + 1):
        if i <= prazo_contemplacao:
            valor_parcela = parcela_cheia
        else:
            if quitou_na_contemplacao:
                break
            if opcao_lance == "Reduzir Prazo":
                if (i - prazo_contemplacao) > novo_prazo:
                    break
                valor_parcela = parcela_cheia
            else:
                valor_parcela = nova_parcela

        # aplicando taxa de antecipação na 1ª e 2ª parcela
        if i in [1, 2]:
            valor_parcela += taxa_antecipacao * valor_credito / 2

        anos_passados = (i - 1) // 12
        fator_correcao = (1 + indice_medio) ** anos_passados
        correcao = (valor_parcela * fator_correcao) - valor_parcela if anos_passados > 0 else 0.0

        saldo_credor_corrigido = saldo_credor * fator_correcao
        custo_seguro = saldo_credor_corrigido * seguro_prestamista

        total = valor_parcela + correcao + custo_seguro

        amortizacao = valor_parcela
        saldo_restante_total = max(saldo_restante_total - amortizacao, 0)
        saldo_credor = max(saldo_credor - (valor_parcela * (valor_credito / total_pagar)), 0)

        if i == prazo_contemplacao:
            saldo_restante_total = saldo_pos_lance
            #saldo_credor = max(valor_credito * ((1 + indice_medio) ** anos_corrigidos) - lance_proprio, 0)
            saldo_credor_corrigido_na_contemplacao = saldo_credor * ((1 + indice_medio) ** anos_corrigidos)
            saldo_credor = max(saldo_credor_corrigido_na_contemplacao - lance_proprio, 0)
            if saldo_restante_total <= 0:
                saldo_restante_total = 0

        parcelas.append({
            "Número da parcela": i,
            "Saldo devedor (R$)": saldo_restante_total,
            "Valor da parcela (R$)": valor_parcela,
            "Seguro (R$)": custo_seguro,
            "Correção monetária (R$)": correcao,
            "Total (R$)": total
        })

        if saldo_restante_total <= 0:
            break

    df_parcelas = pd.DataFrame(parcelas).round(2)

    valor_credito_corrigido = valor_credito * ((1 + indice_medio) ** anos_corrigidos)
    fundo_reserva_reais = valor_credito * fundo_reserva
    custo_total = df_parcelas["Total (R$)"].sum() + lance_proprio - fundo_reserva_reais
    custo_real = custo_total - valor_credito_corrigido

    cet_aa = (((df_parcelas["Total (R$)"].sum() + lance_proprio) / valor_credito) - 1) / prazo_anos
    cet_am = cet_aa / 12

    totais = {
        "Número da parcela": "Total",
        "Saldo devedor (R$)": "",
        "Valor da parcela (R$)": df_parcelas["Valor da parcela (R$)"].sum(),
        "Seguro (R$)": df_parcelas["Seguro (R$)"].sum(),
        "Correção monetária (R$)": df_parcelas["Correção monetária (R$)"].sum(),
        "Total (R$)": df_parcelas["Total (R$)"].sum()
    }

    df_parcelas = pd.concat([df_parcelas, pd.DataFrame([totais])], ignore_index=True)
    styled_df = df_parcelas.style.apply(highlight_contemplacao, axis=1)

    # --- Análise de Alavancagem ---
    if tipo_estrategia == "Alavancagem":
        valor_investido_inicial = valor_credito

        if tipo_investimento == "Pós-fixado (% CDI)":
            taxa_bruta_aa = perc_cdi * cdi_estimado
        elif tipo_investimento == "Inflação":
            taxa_bruta_aa = (1 + taxa_juros) * (1 + 0.058) - 1
        else:
            taxa_bruta_aa = taxa_juros

        taxa_mensal = (1 + taxa_bruta_aa) ** (1/12) - 1

        montante_contemplacao = valor_investido_inicial * (1 + taxa_mensal) ** prazo_contemplacao
        rendimento_contemplacao = montante_contemplacao - valor_investido_inicial

        if prazo_contemplacao <= 6:
            ir_contemplacao = 0.225
        elif prazo_contemplacao <= 12:
            ir_contemplacao = 0.20
        elif prazo_contemplacao <= 24:
            ir_contemplacao = 0.175
        else:
            ir_contemplacao = 0.15

        imposto_contemplacao = rendimento_contemplacao * ir_contemplacao
        resgate_liquido = lance_proprio

        montante_pos_resgate = montante_contemplacao - resgate_liquido - imposto_contemplacao
        meses_pos_contemplacao = prazo_meses - prazo_contemplacao

        if montante_pos_resgate <= 0:
            montante_final = 0
            rendimento_pos_resgate = 0
            montante_pos_resgate = 0
        else:
            montante_final = montante_pos_resgate * (1 + taxa_mensal) ** meses_pos_contemplacao
            rendimento_pos_resgate = montante_final - montante_pos_resgate

        if meses_pos_contemplacao <= 6:
            ir_final = 0.225
        elif meses_pos_contemplacao <= 12:
            ir_final = 0.20
        elif meses_pos_contemplacao <= 24:
            ir_final = 0.175
        else:
            ir_final = 0.15

        imposto_final = rendimento_pos_resgate * ir_final

        rendimento_liquido_total = (rendimento_contemplacao - imposto_contemplacao) + (rendimento_pos_resgate - imposto_final)

        resultado_liquido = rendimento_liquido_total - custo_real

        # --- Cálculo da taxa de breakeven ---
        if resultado_liquido < 0:
            taxa_breakeven = 0.0001
            while True:
                taxa_mensal_breakeven = (1 + taxa_breakeven) ** (1 / 12) - 1

                # Montante até a contemplação
                montante_contemplacao_bk = valor_investido_inicial * (1 + taxa_mensal_breakeven) ** prazo_contemplacao
                rendimento_contemplacao_bk = montante_contemplacao_bk - valor_investido_inicial

                # IR contemplação
                if prazo_contemplacao <= 6:
                    ir_contemplacao_bk = 0.225
                elif prazo_contemplacao <= 12:
                    ir_contemplacao_bk = 0.20
                elif prazo_contemplacao <= 24:
                    ir_contemplacao_bk = 0.175
                else:
                    ir_contemplacao_bk = 0.15

                imposto_contemplacao_bk = rendimento_contemplacao_bk * ir_contemplacao_bk
                resgate_liquido_bk = lance_proprio

                montante_pos_resgate_bk = montante_contemplacao_bk - resgate_liquido_bk - imposto_contemplacao_bk
                meses_pos_contemplacao = prazo_meses - prazo_contemplacao

                if montante_pos_resgate_bk <= 0:
                    montante_final_bk = 0
                    rendimento_pos_resgate_bk = 0
                    montante_pos_resgate_bk = 0
                else:
                    montante_final_bk = montante_pos_resgate_bk * (1 + taxa_mensal_breakeven) ** meses_pos_contemplacao
                    rendimento_pos_resgate_bk = montante_final_bk - montante_pos_resgate_bk

                # IR final
                if meses_pos_contemplacao <= 6:
                    ir_final_bk = 0.225
                elif meses_pos_contemplacao <= 12:
                    ir_final_bk = 0.20
                elif meses_pos_contemplacao <= 24:
                    ir_final_bk = 0.175
                else:
                    ir_final_bk = 0.15

                imposto_final_bk = rendimento_pos_resgate_bk * ir_final_bk

                rendimento_liquido_total_bk = (rendimento_contemplacao_bk - imposto_contemplacao_bk) + (
                            rendimento_pos_resgate_bk - imposto_final_bk)

                resultado_liquido_bk = rendimento_liquido_total_bk - custo_real

                if resultado_liquido_bk >= 0 or taxa_breakeven > 0.25:
                    break
                else:
                    taxa_breakeven += 0.0001

            taxa_anual_breakeven = taxa_breakeven

        else:
            taxa_anual_breakeven = None

    try:
        if taxa_anual_breakeven > 0.25:
            taxa_anual_breakeven = "Superior a 25%"
    except:
        pass

    # --- Exibição dos Resultados ---
    st.subheader("📊 Resultado da simulação")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### 🔢 Dados gerais")
        st.write(f"**Prazo em anos:** {prazo_anos:.2f}".replace(".", ","))
        st.write(f"**Índice de correção:** {nome_indice} ({(indice_medio*100):.2f}% aa)".replace(".", ","))
        if not df_parcelas.empty and df_parcelas.loc[0, 'Total (R$)'] != "Total":
            st.write(f"**1ª parcela:** {formatar_moeda(df_parcelas.loc[0, 'Total (R$)'])}")
            st.write(f"**Média das demais parcelas:** {formatar_moeda(df_parcelas.loc[2:len(df_parcelas)-2, 'Total (R$)'].mean())}")
        st.write(f"**CET a.a:** {formatar_percentual(cet_aa)} | **CET a.m:** {formatar_percentual(cet_am)}")
        st.write(f"**Crédito corrigido na contemplação:** {formatar_moeda(valor_credito_corrigido)}")
        #st.write(f"**Custo real:** {formatar_moeda(custo_real)}")
        #st.info("Custo real = Total pago em parcelas + lance - crédito recebido - fundo de reserva")

    with colB:
        if tipo_estrategia == "Alavancagem":
            st.markdown("### 🚀 Análise de alavancagem")
            st.write(f"**Valor inicial:** {formatar_moeda(valor_investido_inicial)}")
            st.write(f"**Rendimento líquido até contemplação ({prazo_contemplacao} meses):** {formatar_moeda(rendimento_contemplacao - imposto_contemplacao)}")
            st.write(f"**Valor remanescente após contemplação:** {formatar_moeda(montante_pos_resgate)}")
            st.write(f"**Rendimento líquido após contemplação ({meses_pos_contemplacao} meses):** {formatar_moeda(rendimento_pos_resgate - imposto_final)}")
            st.write(f"**Rendimento líquido total:** {formatar_moeda(rendimento_liquido_total)}")
            if resultado_liquido >= 0:
                st.success(f"**Resultado da alavancagem:** {formatar_moeda(resultado_liquido)}")
                st.info(f"Resultado = Rendimentos líquidos + Crédito recebido - Total pago")
            else:
                st.error(f"**Resultado da alavancagem:** {formatar_moeda(resultado_liquido)}")
                if taxa_anual_breakeven is not None:
                    if taxa_anual_breakeven == "Superior a 25%":
                        st.info("Taxa anual necessária para breakeven é superior a 25% a.a.")
                    elif tipo_investimento == "Inflação":
                        st.info(f"**Taxa anual necessária para breakeven:** {formatar_percentual(taxa_anual_breakeven- 0.058)}")
                    else:
                            st.info(f"**Taxa anual necessária para breakeven:** {formatar_percentual(taxa_anual_breakeven)}")

    st.subheader("📋 Detalhamento das parcelas")
    for col in ["Saldo devedor (R$)", "Valor da parcela (R$)", "Seguro (R$)", "Correção monetária (R$)", "Total (R$)"]:
        df_parcelas[col] = df_parcelas[col].apply(lambda x: formatar_moeda(x) if isinstance(x, (int, float)) else x)

    st.dataframe(styled_df, use_container_width=True, height=len(df_parcelas) * 35 + 50, hide_index=True)