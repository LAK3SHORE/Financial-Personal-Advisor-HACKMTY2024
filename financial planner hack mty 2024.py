import streamlit as st
from openai import OpenAI
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

# Load API key
OPENAI_API_KEY = ('OPEN AI KEY')
# OpenAI configuration
client = OpenAI(api_key=OPENAI_API_KEY)

# Check for API key
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY variable.")
    st.stop()

def simulate_nessie_data(user_id):
    prompt = f"""
    Simula datos financieros detallados para un usuario con ID {user_id}. Incluye:
    1. Una lista de cuentas (al menos 2) con saldos.
    2. Una lista de transacciones recientes (al menos 10) con fechas, cantidades, tipos (depósito o retiro) y categorías.
    3. Una lista de préstamos (si los hay) con montos y tasas de interés.
    4. Una lista de facturas pendientes.
    
    Proporciona los datos en el siguiente formato JSON, pero simula los datos y las fechas y los saldos y los montos de los siguientes 
    concpetos, es decir modifica los datos de la cuenta coriente y de la de ahorros, de transacciones, loans  and bills:
    {{
        "accounts": [
            {{"nombre": "Cuenta Corriente", "saldo": 100}},
            {{"nombre": "Cuenta de Ahorros", "saldo": 390.00}}
        ],
        "transactions": [
            {{"fecha": "2023-09-15", "cantidad": 500.00, "tipo": "depósito", "categoría": "Salario"}},
            {{"fecha": "2023-09-16", "cantidad": 50.00, "tipo": "retiro", "categoría": "Alimentación"}}
        ],
        "loans": [
            {{"tipo": "Préstamo Personal", "monto": 10000.00, "tasa_interes": 5.5}}
        ],
        "bills": [
            {{"nombre": "Electricidad", "monto": 200.00, "fecha_vencimiento": "2023-09-30"}}
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un simulador de datos financieros precisos y realistas. Debes responder únicamente con un objeto JSON válido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            n=1,
            temperature=0.7
        )
        
        # Obtener el contenido de la respuesta
        content = response.choices[0].message.content.strip()
        
        # Imprimir el contenido para depuración
        st.write("Respuesta de OpenAI (raw):", content)
        
        # Intentar analizar el JSON
        simulated_data = json.loads(content)
        return simulated_data
    except json.JSONDecodeError as e:
        st.error(f"Error al analizar JSON: {str(e)}")
        st.write("Contenido que causó el error:", content)
    except Exception as e:
        st.error(f"Error simulando datos financieros: {str(e)}")
    
    return None

def analyze_spending_patterns(transactions):
    categories = {}
    for transaction in transactions:
        category = transaction.get('categoría', 'Sin categoría')
        amount = transaction.get('cantidad', 0)
        if transaction.get('tipo') == 'retiro':
            if category in categories:
                categories[category] += amount
            else:
                categories[category] = amount
    return categories

def calculate_savings_rate(transactions):
    income = sum(t['cantidad'] for t in transactions if t.get('tipo') == 'depósito')
    expenses = sum(t['cantidad'] for t in transactions if t.get('tipo') == 'retiro')
    if income > 0:
        return (income - expenses) / income
    return 0

def predict_future_expenses(transactions, months_ahead=3):
    total_expenses = sum(t['cantidad'] for t in transactions if t.get('tipo') == 'retiro')
    avg_monthly_expense = total_expenses / len(transactions) * 30  # Asumiendo que las transacciones cubren un mes
    future_expenses = [avg_monthly_expense * (1 + 0.02 * i) for i in range(1, months_ahead + 1)]
    
    return future_expenses

def generate_financial_plan(simulated_data, user_input):
    spending_patterns = analyze_spending_patterns(simulated_data['transactions'])
    savings_rate = calculate_savings_rate(simulated_data['transactions'])

    prompt = f"""
    El usuario ha proporcionado la siguiente información financiera:
    - Cuentas: {simulated_data['accounts']}
    - Transacciones: {simulated_data['transactions']}
    - Préstamos: {simulated_data['loans']}
    - Facturas: {simulated_data['bills']}
    
    Patrones de gasto: {spending_patterns}
    Tasa de ahorro actual: {savings_rate:.2%}
    
    El objetivo financiero del usuario es: {user_input}
    
    Por favor, genera un plan financiero detallado y personalizado que incluya recomendaciones para ahorrar, invertir y gestionar deudas. Considera los patrones de gasto actuales del usuario y su tasa de ahorro en tus consejos.
    
    Al final, añade una recomendación específica y práctica que el usuario pueda implementar inmediatamente para mejorar su situación financiera.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asesor financiero profesional y experto."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            n=1,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generando el plan financiero: {str(e)}")
        return None

# Streamlit interface
st.title("Herramienta de Planificación Financiera Personalizada")

user_id = st.text_input("Ingrese un ID de usuario para simular sus datos financieros:")

if user_id:
    if not user_id.strip():
        st.error("Por favor, ingrese un ID de usuario válido.")
        st.stop()

    st.info("Simulando datos financieros... Esto puede tomar un momento.")
    simulated_data = simulate_nessie_data(user_id)
    
    if simulated_data:
        st.success("Datos financieros simulados con éxito!")
        
        # Displaying accounts
        st.subheader("Sus Cuentas")
        accounts_df = pd.DataFrame(simulated_data['accounts'])
        st.dataframe(accounts_df)
        
        # Displaying recent transactions
        st.subheader("Transacciones Recientes")
        transactions_df = pd.DataFrame(simulated_data['transactions'])
        transactions_df['fecha'] = pd.to_datetime(transactions_df['fecha'])
        transactions_df = transactions_df.sort_values('fecha', ascending=False).head(10)
        st.dataframe(transactions_df)
        
        # Displaying loans
        if simulated_data['loans']:
            st.subheader("Sus Préstamos")
            loans_df = pd.DataFrame(simulated_data['loans'])
            st.dataframe(loans_df)
        
        # Displaying bills
        if simulated_data['bills']:
            st.subheader("Sus Facturas Pendientes")
            bills_df = pd.DataFrame(simulated_data['bills'])
            st.dataframe(bills_df)

        # Spending patterns
        spending_patterns = analyze_spending_patterns(simulated_data['transactions'])
        st.subheader("Sus Patrones de Gasto")
        fig_spending = px.pie(values=list(spending_patterns.values()), names=list(spending_patterns.keys()), title="Distribución de Gastos")
        st.plotly_chart(fig_spending)

        # Savings rate
        savings_rate = calculate_savings_rate(simulated_data['transactions'])
        st.subheader("Su Tasa de Ahorro Actual")
        st.metric("Tasa de Ahorro", f"{savings_rate:.2%}")

        # Future expenses prediction
        future_expenses = predict_future_expenses(simulated_data['transactions'])
        st.subheader("Gastos Previstos para los Próximos 3 Meses")
        fig_expenses = px.line(x=["Mes 1", "Mes 2", "Mes 3"], y=future_expenses, title="Predicción de Gastos")
        st.plotly_chart(fig_expenses)
        
        st.subheader("Defina Su Objetivo Financiero")
        financial_goal = st.text_input("¿Cuál es su objetivo financiero? (Ej: Ahorrar para una casa, pagar deudas, etc.)")
        financial_timeframe = st.slider("¿En cuántos años quiere alcanzar su objetivo?", 1, 10, 5)
        
        if financial_goal and financial_timeframe:
            st.write(f"Objetivo: {financial_goal} en {financial_timeframe} años.")
            
            if st.button("Generar Plan Financiero"):
                user_input = f"Objetivo: {financial_goal}, Plazo: {financial_timeframe} años."
                financial_plan = generate_financial_plan(simulated_data, user_input)
                
                if financial_plan:
                    st.subheader("Plan Financiero Generado")
                    st.write(financial_plan)
                else:
                    st.error("No se pudo generar el plan financiero. Por favor, intente de nuevo más tarde.")

        st.subheader("¿Tiene alguna otra pregunta sobre su plan financiero?")
        additional_question = st.text_input("Haga una pregunta (Ej: ¿Cómo puedo mejorar mi plan de ahorro?)")

        if additional_question:
            if st.button("Enviar"):
                prompt = f"""
                Basado en los siguientes datos financieros:
                - Cuentas: {simulated_data['accounts']}
                - Transacciones: {simulated_data['transactions']}
                - Préstamos: {simulated_data['loans']}
                - Facturas: {simulated_data['bills']}
                - Patrones de gasto: {spending_patterns}
                - Tasa de ahorro actual: {savings_rate:.2%}
                
                Y la pregunta: "{additional_question}"
                
                Por favor, proporciona una respuesta precisa y personalizada.
                """
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Eres un asesor financiero profesional y experto."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        n=1,
                        temperature=0.7
                    )
                    
                    st.subheader("Respuesta a Su Pregunta")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error generando la respuesta: {str(e)}")
    else:
        st.error("No se pudieron simular los datos financieros. Por favor, intente de nuevo.")





