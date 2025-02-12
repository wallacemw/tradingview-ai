from flask import Flask, request, jsonify
import xgboost as xgb
import pandas as pd
import requests

app = Flask(__name__)

# Links para a Planilha Google Sheets e Google Apps Script
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/1RfqS0FfOZeZnGjWcuVcFl-R8Pmt8_mxTRoqqbCNfZ6k/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/SEU_SCRIPT_ID/exec"

# Carregar modelo de Machine Learning
try:
    modelo = xgb.Booster()
    modelo.load_model("modelo_xgb.bin")  # Certifique-se de que este arquivo está no GitHub!
except Exception as e:
    print(f"Erro ao carregar o modelo: {e}")

@app.route('/atualizar', methods=['GET'])
def atualizar():
    try:
        # Baixa os dados do Google Sheets
        df = pd.read_csv(SHEET_URL)

        # Pega o último registro sem previsão
        ultimo = df[df["Sinal IA"] == "Pendente"].iloc[-1]
        
        if pd.isna(ultimo["Preço"]) or pd.isna(ultimo["RSI"]):
            return jsonify({"status": "Nenhum dado novo"}), 200

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
