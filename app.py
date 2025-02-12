from flask import Flask, request, jsonify
import xgboost as xgb
import pandas as pd
import requests

app = Flask(__name__)

# Links para a Planilha Google Sheets e Google Apps Script
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/1RfqS0FfOZeZnGjWcuVcFl-R8Pmt8_mxTRoqqbCNfZ6k/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzTI92TQ2LdS68vPAbSt8YH7k3ki9bYHoxTKzpbVtqulsx31axwd7Ol5Hm9SO9haL29lw/exec"

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

        # 📌 Filtragem de Ruído (ATR) para remover volatilidade alta
        df["ATR"] = df["Preço"].rolling(window=14).apply(lambda x: x.max() - x.min(), raw=True)
        df = df[df["ATR"] < df["ATR"].quantile(0.75)]  # Remove os 25% mais voláteis

        # 📌 Confirmação de Tendência (SMA(50))
        df["SMA50"] = df["Preço"].rolling(window=50).mean()
        df["SohCompra"] = df["Preço"] > df["SMA50"]
        df["SohVenda"] = df["Preço"] < df["SMA50"]

        # Pega o último registro sem previsão
        ultimo = df[df["Sinal IA"] == "Pendente"].iloc[-1]
        
        if pd.isna(ultimo["Preço"]) or pd.isna(ultimo["RSI"]):
            return jsonify({"status": "Nenhum dado novo"}), 200

        # 📌 Melhorar Machine Learning com otimização de hiperparâmetros
        entrada = pd.DataFrame([[ultimo["Preço"], ultimo["RSI"]]], columns=["Preço", "RSI"])
        previsao = modelo.predict(xgb.DMatrix(entrada))

        # Define "BUY" ou "SELL" se a tendência confirmar
        if previsao[0] > 0.5 and ultimo["SohCompra"]:
            resultado = "BUY"
        elif previsao[0] <= 0.5 and ultimo["SohVenda"]:
            resultado = "SELL"
        else:
            resultado = "Neutro"

        # Atualiza a planilha com o resultado da IA
        requests.post(SCRIPT_URL, json={"sinal": resultado})

        return jsonify({"status": "Previsão atualizada", "sinal": resultado}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
