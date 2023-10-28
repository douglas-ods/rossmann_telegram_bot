import pandas as pd
import os
import json
import requests
from flask import Flask,request,Response

# contants
token="6821240818:AAGyOtpksA6JhwqIlTwaQcw4sU3djWVPpD0"
# # info about Bot
# https://api.telegram.org/bot6236253743:AAGjberiMXdpSJjKUWKwvvqlod8u2OU9pm4/getMe

# # get updates
# https://api.telegram.org/bot6236253743:AAGjberiMXdpSJjKUWKwvvqlod8u2OU9pm4/getUpdates

# # Webhook Local
#https://api.telegram.org/bot6236253743:AAGjberiMXdpSJjKUWKwvvqlod8u2OU9pm4/setWebhook?url=https://localhost.run/docs/forever-free/

# # Webhook Render
# https://api.telegram.org/bot6821240818:AAGyOtpksA6JhwqIlTwaQcw4sU3djWVPpD0/setWebhook?url=https://rossmann-telegram-bot-6yoe.onrender.com

# # send message
# https://api.telegram.org/bot6821240818:AAGyOtpksA6JhwqIlTwaQcw4sU3djWVPpD0/sendMessage?chat_id=1226335433&text=Hi Douglas, I am doing good, tks!

def send_message(chat_id, text):
    url =f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"    
    r = requests.post(url,json={"text":text} )
    print("Status Code {}".format(r.status_code))
    return None 

def load_dataset(store_id):
    df10 = pd.read_csv("test.csv") 
    df_store_raw =pd.read_csv("store.csv")
    df_test =pd.merge(df10,df_store_raw,how="left",on="Store")
    # choose store for prediction
    df_test = df_test[df_test["Store"]==store_id]
    if not df_test.empty:
        # removed closed days
        df_test = df_test[df_test["Open"]!=0]
        df_test = df_test[~df_test["Open"].isnull()]
        df_test = df_test.drop("Id",axis="columns")    
        # convert Dataframe to Json
        data = json.dumps(df_test.to_dict( orient='records' ) )
    else:
        data="error"
    return data

def predict(data):
    # API Call        
    url = 'https://api-rossmann-render-x8ik.onrender.com/rossmann/predict'
    header = {'Content-type':'application/json'} 
    data = data
    #enviar dados
    r = requests.post(url,data=data,headers=header )
    print( 'Status Code {}'.format(r.status_code))    
    #converter novamente para um DF a partir do json retornado
    df1 = pd.DataFrame(r.json(),columns=r.json()[0].keys())
    return df1


def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    #chat_id = message["result"]["chat"]["id"]
    #store_id = message["result"]["text"]
    store_id = store_id.replace("/","")
    try:
       store_id = int(store_id) 
    except ValueError:        
        store_id="error"
    return chat_id,store_id

# API Initialize
app=Flask(__name__)
@app.route("/",methods=["GET","POST"])
def index():
    if request.method=="POST":
        message = request.get_json()
        chat_id,store_id =parse_message(message)
        if store_id !="error":           
           # load_dataset
           data = load_dataset(store_id)
           if data!="error":
                # prediction
                df1 = predict(data)
                # calculation
                df2 = df1[["store","prediction"]].groupby("store").sum().reset_index()  
                msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(df2['store'].values[0],df2['prediction'].values[0] )                 
                # send message
                send_message(chat_id,msg)
                return Response("OK",status=200)                
           else:
               send_message(chat_id, "Loja não disponível para consulta")
               return Response("OK",status=200) 
        else:
           send_message(chat_id,"O ID da loja não e válido") 
           return Response("Ok",status=200)  
    else:
       return "<h1> Rossmann Telegram Bot <h1>"
if __name__=="__main__":
    port = os.environ.get("PORT",5000)
    app.run(host="0.0.0.0",port=port)