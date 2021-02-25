# ------------------------------------------------------------
# Arbolito digital Bitso
# ------------------------------------------------------------
# Permite convertir facilmente entre monedas, poner ordenes, etc
# Sirve para el exchange Bitso, es una navaja suiza de crypto
# ------------------------------------------------------------
# Alvaro "Krono" - Febrero 2021 - Desde el exilio en Costa Rica
# En memoria de mi querido padre
# ------------------------------------------------------------
# APIs - hay que tener cuenta en los dos sitios!
#
# Bitso para usar el exchange
#
# https://bitso.com/api_info
# https://blog.bitso.com/presentando-bitso-api-v3-e78beff0888
#
# API para obtener indicadores economicos de bitcoin
#
# https://taapi.io/documentation/integration/direct/
# https://taapi.io/
#
# API de Crito Ya para dolar en Argentina, etc
#
# https://criptoya.com/api/
#
# ------------------------------------------------------------
# Librerias
#
# Necesita Python 3.9.x y las librerías:
#
# https://github.com/bitsoex/bitso-py
#
# https://packaging.python.org/tutorials/installing-packages/
#
# Instalar dependencias con (linea de comandos)
#
# pip install bitso-py
# pip install requests
#
# ------------------------------------------------------------
# MIT License
#
# Copyright (c) 2021 Alvaro "Krono"
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------

from decimal import Decimal  # para los calculos

import bitso  # bitso api
import time  # temporizaciones
import requests  # para la api de indicadores, REST API JSON

# ----------
import krono_bot_config  # configuración de cuenta

# -- globales

VERSION = "0.25.02.2021"  # TODO cambiar esta version en cada revision

# balances de dinero disponible
usd_total = 0
ars_total = 0
btc_total = 0

usd_blue = 0  # cotizacion dolar

wealth_usd = 0  # riqueza total
wealth_ars = 0

btc_price_usd = 0  # ultimo precio btc
btc_price_ars = 0

# indicadores de la API de https://taapi.io/
ema = 0
rsi = 0
macd = 0
sar = 0
tr = 0
taapi_endpoint = "https://api.taapi.io/"
taapi_parameters = {
    'secret': krono_bot_config.TAAPI_SECRET,
    'exchange': 'binance',
    'symbol': 'BTC/USDT',
    'interval': '1h'  # DEBUG TODO una hora? un minuto? por ahora una hora
    }
# TODO DEBUG PONER MAS INDICADORES


# -- funciones --

# recorrer y buscar el ultimo precio de compra y venta que hice
# los historicos pueden ser viejos no importan
def ultimos_precios(api, book_use):
    btc_last_buy_price = 0  # cual fue el mayor precio que pagaste por btc ? si esta mas barato, compra papa
    btc_last_sell_price = 0  # cual fue el precio mas barato que vendiste ? si esta mas caro, vende
    last_buy_found = False
    last_sell_found = False

    # trades realizados, buscar las ultimas compras a ver el ultimo precio de compra...
    try:
        utx = api.user_trades(book=book_use)
    except Exception as e:
        print("ERROR: no puedo consultar tus trades. Fin\n", e)
        exit()

    for u in utx:
        if u.major > 0 and not last_buy_found:
            btc_last_buy_price = u.price
            last_buy_found = True

        if u.major < 0 and not last_sell_found:  # las ventas son moneda major negativa
            btc_last_sell_price = u.price
            last_sell_found = True

    print("\n", book_use, " >> Ultimo precio btc compra $", btc_last_buy_price, "| venta $", btc_last_sell_price,
          "| diff $", round(btc_last_sell_price - btc_last_buy_price, 2))


# reiniciar ordenes
# recibe la api funcionando de bitso
# devuelve cuantas ordenes cancelo
def borrar_ordenes(api, book_use):
    try:
        oo = api.open_orders(book_use)
        for oo_i in oo:
            api.cancel_order(oo_i.oid)  # cancelar orden pendiente
    except Exception as e:
        print(e)
        return -1  # error

    return len(oo)


# lista las ordenes activas
# devuelve cuantas hay
def mostrar_ordenes(api, book_use):
    oo = api.open_orders(book_use)
    if len(oo) > 0:
        print("- Ordenes pendientes ", book_use, '-')
        for idx, oo_i in enumerate(oo, start=1):
            print(idx, oo_i.side.upper(), oo_i.type, "Precio {:.2f}".format(oo_i.price),
                  "Cant {:.9f}".format(oo_i.original_amount), "= $ {:.2f}".format(oo_i.price * oo_i.original_amount))
    return len(oo)

# muestra el dolar en Argentina , con la API de Cripto YA
# https://criptoya.com/api/
def show_dolar():
    dolar = requests.get("https://criptoya.com/api/dolar")
    print("Dolar en Argentina:", dolar.json())


# muestra balances y cotizaciones, y ademas las pone globales
def show_balance(api):
    global usd_total
    global ars_total
    global btc_total
    global usd_blue
    global wealth_usd
    global wealth_ars
    global btc_price_usd
    global btc_price_ars

    try:
        balances = api.balances()
    except Exception as e:
        print("ERROR: no puedo consultar balances. Fin\n", e)
        exit()

    print("Balances\nDisponible", balances.ars.name, "{:.2f}".format(balances.ars.available), "|", balances.usd.name,
          "{:.2f}".format(balances.usd.available), "|", balances.btc.name, "{:.9f}".format(balances.btc.available))

    print("Total", balances.ars.name, "{:.2f}".format(balances.ars.total), "|", balances.usd.name,
          "{:.2f}".format(balances.usd.total), "|", balances.btc.name, "{:.9f}".format(balances.btc.total))

    # precio btc de referencia y riqueza total
    try:
        tick_usd = api.ticker('btc_usd')
    except Exception as e:
        print("ERROR: No puedo obtener precios btc_usd.\n", e)
        exit()

    try:
        tick_ars = api.ticker('btc_ars')
    except Exception as e:
        print("ERROR: No puedo obtener precios btc_ars.\n", e)
        exit()

    # TODO falta consultar comisiones en pesos y dolares

    # calcular precio del dolar bitcoin aproximado
    usd_blue = round(tick_ars.last / tick_usd.last, 2)

    # setear globales utiles - los roud eliminan valores anomalos
    ars_total = round(balances.ars.total, 2)
    usd_total = round(balances.usd.total, 2)
    btc_total = round(balances.btc.total, 8)

    btc_price_usd = round(tick_usd.last, 2)
    btc_price_ars = round(tick_ars.last, 2)

    # riqueza total aproximada
    wealth_usd = round(ars_total / usd_blue + usd_total + btc_total * btc_price_usd, 2)

    wealth_ars = round(ars_total + usd_blue * usd_total + btc_total * btc_price_ars, 2)

    print("** RIQUEZA TOTAL APROXIMADA USD ", wealth_usd, "| ARS", wealth_ars)

    print("\n!! Precio BTC/USD ${:.2f}".format(tick_usd.last), "| BTC/ARS ${:.2f}".format(tick_ars.last), "| DolarBTC = ARS ", usd_blue)


# menu principal
def show_menu(api):
    print("---------------------------------------")
    print("Krono Arbolito", VERSION)
    print("---------------------------------------\n")

    show_balance(api)

    print("---------------------------------------")

    mostrar_ordenes(api, 'btc_usd')

    ultimos_precios(api, 'btc_usd')

    print("---------------------------------------")

    mostrar_ordenes(api, 'btc_ars')

    ultimos_precios(api, 'btc_ars')

    print("---------------------------------------\n")

    show_dolar()

    print("---------------------------------------\n")
    print("Opciones:")
    print("1) ARS > USD  | ARS$", usd_blue, " MAX U$S", round(ars_total / usd_blue, 2))
    print("2) ARS > BTC  | ARS$", btc_price_ars, " MAX btc {:.08f}".format(round(ars_total / btc_price_ars, 8)))
    print("3) USD > BTC  | USD$", btc_price_usd, " MAX btc {:.08f}".format(round(usd_total / btc_price_usd, 8)))
    print("4) BTC > USD  | BTC {:.08f}".format(btc_total), " MAX USD$", round(btc_total * btc_price_usd, 2))
    print("5) BTC > ARS  | BTC {:.08f}".format(btc_total), "MAX ARS$", round(btc_total * btc_price_ars, 2))
    print("6) USD > ARS  | ARS$", usd_blue, " MAX ARS", round(usd_total * usd_blue, 2))
    print("7) Cancelar ordenes pendientes.")
    print("8) Meter orden a mano")
    print("9) Ver indicadores economicos")

    print("r) Refrescar datos")

    print("\n0) Salir")

    return input("? >").strip().lower()


# --- inicio
# arrancar la api de bitso con las keys secretas
api = None
try:
    api = bitso.Api(krono_bot_config.BITSO_API_KEY, krono_bot_config.BITSO_API_SECRET)
    status = api.account_status()
    print("Status cuenta:", status.status)
except Exception as e:
    print("ERROR: no puedo obtener status de cuenta. Fin\n", e)
    exit()

# parametros del trade
use_book = ''  # libro a usar
cant_exchange_max = 0  # cantidad a cambiar de la moneda origen

# ------ loop principal ------
opt = show_menu(api)
while not opt == '0':

    ok_trade = False  # proceder con el trade?

    if opt == '1':
        print("ARS > USD")
        # este es complejo, lleva dos trades uno de ARS a BTC, y otro de BTC a USD
        print("ERROR: No implementado. Por ahora pasa de ARS a BTC y de BTC a USD...")
    elif opt == '2':
        print("ARS > BTC")
        use_book = 'btc_ars'
        cant_exchange_max = ars_total
        ok_trade = True
    elif opt == '3':
        print("USD > BTC")
        use_book = 'btc_usd'
        cant_exchange_max = usd_total
        ok_trade = True
    elif opt == '4':
        print("BTC > USD")
        use_book = 'btc_usd'
        cant_exchange_max = btc_total
        ok_trade = True
    elif opt == '5':  # pasar btc a pesos? estas loco papa?
        print('BTC > ARS')
        use_book = 'btc_ars'
        cant_exchange_max = btc_total
        ok_trade = True
    elif opt == '6':
        print("USD > ARS (estas loco?)")
        print("ERROR: No implementado. Por ahora pasa de USD a BTC y de BTC a ARS...")
    elif opt == '7':  # cancelar ordenes
        # TODO falta confirmar antes de cancelar !
        # liquidar ordenes pendientes
        print(borrar_ordenes(api, 'btc_usd'), " ordenes USD pendientes canceladas.")
        print(borrar_ordenes(api, 'btc_ars'), " ordenes ARS pendientes canceladas.\n")
    elif opt == '8':
        print("Sin hacer!")

    elif opt == '9':
        # TODO DEBUG MEJORAR INDICADORES
        # TODO preguntar si quiere minuto, hora, diario, etc
        # TODO evaluar el significado humano de cada indicador (compra / venta)

        print ("-- Indicadores --")

        print("Intervalo:", taapi_parameters['interval'])

        print("EMA", requests.get(taapi_endpoint + "ema", params=taapi_parameters).json())
        print("RSI", requests.get('https://api.taapi.io/rsi', params=taapi_parameters).json())
        print("MACD", requests.get("https://api.taapi.io/macd", params=taapi_parameters).json())
        print("SAR", requests.get("https://api.taapi.io/sar", params=taapi_parameters).json())
        print("TR", requests.get("https://api.taapi.io/tr", params=taapi_parameters).json())
        print("SUPERTREND", requests.get("https://api.taapi.io/supertrend", params=taapi_parameters).json())

        print ('\n\n')

        # TODO DEBUG DEBERIA IDENTIFICAR TENDENCIAS BAJISTAS O ALZA Y ACTUAR EN CONSECUENCIA // MUY IMPOSIBLE REALMENTE CON ALGO COMO BTC

    elif opt == 'r':
        # refrescar
        print("Refrescar datos. Presione ENTER")

    else:
        print("Opción no valida!")

    if ok_trade:
        if not cant_exchange_max == 0:
            print("Tenes un maximo de ", cant_exchange_max)

            print("Podes cambiar un porcentaje o una cantidad especifica.")

            print("Para porcentaje, pone el numero seguido de %, para cantidad seguido de $ o nada.")

            print("Ejemplo: 10 % o 25 $")
            leer = input("Cuanto % o $ ?").strip().lower()

            cantidad = 0.0
            if leer.find("%") > 0:  # puso un porcentaje?
                porcentaje = float(leer.replace("%", ""))
                if porcentaje < 1:
                    print("Error, no puede ser tan bajo. %", porcentaje)
                    ok_trade = False
                else:
                    cantidad = cant_exchange_max * Decimal(porcentaje) / Decimal(100.0)
            else:
                cantidad = float(leer.replace("$", ""))

            if opt == '4' or opt == '5':
                cantidad = round(cantidad, 8) # hacia btc
            else:
                cantidad = round(cantidad, 2) # hacia fiat usd / ars

            print("Cantidad a cambiar: ", cantidad)
            s = input("Es correcto? S / N").lower().strip()[0]

            cantidad = Decimal(cantidad) # conversion importante para usarlo mas abajo

            if s == 's':
                # tomar ordenes altas y bajas
                try:
                    ob = api.order_book(use_book)
                except Exception as e:
                    print("Fallo obteniendo valores de mercado.\n", e)
                    exit(-1)

                print("-- Mercados ", use_book, "--")
                # sacar promedios
                ask_prom = 0
                bid_prom = 0
                ic = 0

                # zip nos da un iterator doble, se detiene en el mas corto, igual devuelve los dos del mismo
                # tamano normalmente
                for ask, bid in zip(ob.asks, ob.bids):
                    ask_prom = ask_prom + ask.price
                    bid_prom = bid_prom + bid.price
                    ic = ic + 1

                ask_prom = ask_prom / ic
                bid_prom = bid_prom / ic

                # las puntas ask están al reves, la mas barata primera
                # guardar estos valores
                ask_min = ob.asks[0].price
                ask_max = ob.asks[len(ob.asks) - 1].price

                bid_max = ob.bids[0].price
                bid_min = ob.bids[len(ob.bids) - 1].price

                print("Puntas ask (venta) min $ ", ask_min, "| max $", ask_max)
                print("Puntas bid (compra) max $", bid_max, "| min $", bid_min)

                print("Promedios: ask $", ask_prom, "  |  bid $", bid_prom)

                # --- preparar orden
                colocar_orden = False

                if opt == '2' or opt == '3':  # ARS o USD, a BTC
                    price = ask_min + Decimal('0.02')  # mas 2 centavo para asegurar la compra
                    side_x = 'buy'
                    ord_c = round(cantidad / price, 8)
                    print("Comprar BTC $", price, " > btc ", ord_c)
                    colocar_orden = True

                if opt == '4' or opt == '5':  # BTC a fiat USD o ARS
                    price = bid_max - Decimal('0.02')  # menos 2 centavo para asegurar la venta
                    side_x = 'sell'
                    ord_c = round(cantidad, 8)
                    print("Vender BTC $", price, " > btc ", ord_c)
                    colocar_orden = True

                if colocar_orden:
                    try:
                        order = api.place_order(book=use_book, side=side_x, order_type='limit', major=ord_c,
                                                price=price)
                    except Exception as e:
                        print("ERROR: Fallo colocar la orden de compra...\n", e)
                    else:  # todo bien
                        print("** Orden colocada!:", order)

                        mostrar_ordenes(api, use_book)

                        print("Esperando unos segundos para que se ejecute.")
                        time.sleep(30)
                else:
                    print("DEBUG - algo esta mal con la orden, no debio llegar aqui.")

            else:
                print("Cancelado!")
        else:
            print("ERROR: No tenes de esa moneda para cambiar, ratonazo!!")  # es un barats

    input("-- ENTER para continuar --")

    opt = show_menu(api)

print("Cambio! Cambio! Pago mas!")
