from flask import Flask, request, jsonify
import xgboost as xgb
import pandas as pd
import requests
import os

app = Flask(__name__)

# URL do Google Sheets (substitua pelo seu link correto)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/1RfqS0FfOZeZnGjWcuVcFl-R8Pmt8_mxTRoqqbCNfZ6k/pub?output=csv"

# URL do Google Apps Script para atualizar os sinais
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyngOe0KwoCPgwhHz0kGy9l4sff218Pco8gG8K96NEmvRpuu89RzozmWwlREDrimoCf/exec"

SCRIPT_URL = "https://colab.research.google.com/drive/1WS7DtBUch66qXmE8pZpesJXTvOcZlvBk?usp=sharing"

# 📌 Verifica se o modelo XGBoost existe antes de carregar
modelo_path = "modelo_xgb.bin"
if os.path.exists(modelo_path):
    modelo = xgb.Booster()
    modelo.load_model(modelo_path)
else:
    print("❌ ERRO: Arquivo modelo_xgb.bin não encontrado!")

@app.route('/atualizar', methods=['GET'])
def atualizar():
    try:
        # Baixa os dados do Google Sheets
        df = pd.read_csv(SHEET_URL)

        # 📌 Verifica se há pelo menos um dado válido
        if df.empty or "Sinal IA" not in df.columns:
            return jsonify({"status": "Nenhum dado novo"}), 200

        # Pega o último registro sem previsão
        ultimo = df[df["Sinal IA"] == "Pendente"].iloc[-1]
        
        if pd.isna(ultimo["Preço"]) or pd.isna(ultimo["RSI"]):
            return jsonify({"status": "Nenhum dado válido"}), 200

        # Faz a previsão usando Machine Learning
        entrada = pd.DataFrame([[ultimo["Preço"], ultimo["RSI"]]], columns=["Preço", "RSI"])
        previsao = modelo.predict(xgb.DMatrix(entrada))

        # Define "BUY" ou "SELL"
        resultado = "BUY" if previsao[0] > 0.5 else "SELL"

        # Atualiza a planilha com o resultado da IA
        requests.post(SCRIPT_URL, json={"sinal": resultado})

        return jsonify({"status": "Previsão atualizada", "sinal": resultado}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
