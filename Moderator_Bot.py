import discord
import random
import json
from discord.ext import commands
import urllib
import os
import requests
import token

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Diccionario para economía
user_money = {}

# Tienda con artículos
store = {
    "rol_fancy": 100,  # Nombre del artículo: precio
    "emoji_extra": 50,
    "titulo_especial": 200
}

# Inventario de usuarios
user_inventory = {}

# Función para obtener ofertas
def get_steam_offers():
    url = "https://store.steampowered.com/api/featuredcategories"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        offers = data.get("specials", {}).get("items", [])
        return [
            {"name": game["name"], "price": game["final_price"] / 100, "url": f"https://store.steampowered.com/app/{game['id']}"}
            for game in offers
        ]
    return []

# Cargar datos de economía e inventario al iniciar el bot
try:
    with open('economia.json', 'r') as f:
        user_money = json.load(f)
except FileNotFoundError:
    user_money = {}

try:
    with open('inventario.json', 'r') as f:
        user_inventory = json.load(f)
except FileNotFoundError:
    user_inventory = {}

# Lista de emojis exclusivos
exclusive_emojis = ['🎉', '✨', '🥳', '🔥', '🌟']  # Emojis que estarán disponibles solo para quienes tengan "emoji_extra"

# Guardar datos de economía al cerrar el bot
@client.event
async def on_disconnect():
    with open('economia.json', 'w') as f:
        json.dump(user_money, f)
    with open('inventario.json', 'w') as f:
        json.dump(user_inventory, f)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if any(emoji in message.content for emoji in exclusive_emojis):
        if "emoji_extra" not in inventory:
            await message.delete()  # Borra el mensaje si no tiene permiso
            await message.channel.send(
                f"{message.author.name}, necesitas comprar el ítem `emoji_extra` para usar esos emojis. Usa `$tienda` para ver los artículos disponibles. 💸"
            )
            return

    # Comando $ayuda
    if message.content.startswith('$ayuda'):
        await message.channel.send(
            'Comandos disponibles: \n「Saludos 👋」 \nhola - hello - hey - gato - perro, \n \n「Juegos e interacciones 🎮」 \n$ping - activa un ping pong, \n$juego - juego de piedra papel o tijeras, escribelo y siguelo con una de las 3 opciones, \n$encuesta - escribe el comando seguido de la cosa a encuestar, \n$fiesta - celebra, \n$novedades - muestra las ofertas de videojuegos \n \n「comandos de la tienda 💰」 \n$dinero - tu dinero actual, \n$trabajar - te genera dinero para comprar en la tienda, \n$tienda - muestra los objetos que puedes comprar, \n$comprar - escribe el comando seguido del objeto de la tienda a comprar, \n$inventario - muestra los items comprados, \n \n「limpiar」 \n$limpiar - limpia el canal si tiene los permisos necesarios'
        )

    # Responder saludos
    if message.content.lower() in ['hola', 'hello', 'hey']:
        await message.channel.send(f'¡Hola, {message.author.name}! 😊')

    if 'gato' in message.content.lower():
        await message.channel.send('¡Meow! 🐱')

    if 'perro' in message.content.lower():
        await message.channel.send('¡Woof woof! 🐶')

    # Comando $ping
    if message.content.startswith('$ping'):
        await message.channel.send('Pong! 🏓')

    # Comando $juego
    if message.content.startswith('$juego'):
        try:
            user_choice = message.content.split('$juego ', 1)[1].lower()
            choices = ['piedra', 'papel', 'tijera']
            if user_choice not in choices:
                await message.channel.send('Opción inválida. Usa: piedra, papel o tijera.')
                return

            bot_choice = random.choice(choices)
            if user_choice == bot_choice:
                result = '¡Empate! 😐'
            elif (user_choice == 'piedra' and bot_choice == 'tijera') or \
                 (user_choice == 'papel' and bot_choice == 'piedra') or \
                 (user_choice == 'tijera' and bot_choice == 'papel'):
                result = '¡Ganaste! 🎉'
            else:
                result = '¡Perdiste! 😢'

            await message.channel.send(f'Yo elegí: {bot_choice}. {result}')
        except IndexError:
            await message.channel.send('Uso correcto: `$juego <piedra/papel/tijera>`')

    # Comando $encuesta
    if message.content.startswith('$encuesta'):
        try:
            question = message.content.split('$encuesta ', 1)[1]
            poll_message = await message.channel.send(f'📊 {question}\n✅ para sí\n❌ para no')
            await poll_message.add_reaction('✅')
            await poll_message.add_reaction('❌')
        except IndexError:
            await message.channel.send('Uso correcto: `$encuesta <pregunta>`')

    # Comando $fiesta
    if message.content.startswith('$fiesta'):
        await message.add_reaction('🎉')

    # Sistema de economía
    if message.content.startswith('$dinero'):
        user_id = str(message.author.id)
        saldo = user_money.get(user_id, 0)  # Saldo inicial es 0
        await message.channel.send(f'{message.author.name}, tienes {saldo} monedas. 💰')

    if message.content.startswith('$trabajar'):
        user_id = str(message.author.id)
        ganancia = random.randint(10, 50)  # Genera entre 10 y 50 monedas
        user_money[user_id] = user_money.get(user_id, 0) + ganancia
        await message.channel.send(f'{message.author.name}, has ganado {ganancia} monedas trabajando. ¡Sigue así! 💼')

    if message.content.startswith('$tienda'):
        tienda_mensaje = "🛒 **Tienda:**\n"
        for item, precio in store.items():
            tienda_mensaje += f'- {item}: {precio} monedas\n'
        await message.channel.send(tienda_mensaje)

    if message.content.startswith('$comprar'):
        try:
            user_id = str(message.author.id)
            item = message.content.split('$comprar ', 1)[1].lower()

            if item not in store:
                await message.channel.send(f'El artículo "{item}" no está disponible en la tienda. ❌')
                return

            precio = store[item]
            saldo = user_money.get(user_id, 0)

            if saldo >= precio:
                user_money[user_id] -= precio
                user_inventory.setdefault(user_id, []).append(item)  # Agregar el ítem al inventario
                await message.channel.send(f'¡Has comprado "{item}" por {precio} monedas! 🎉')

                # Efecto del ítem comprado
                if item == "rol_fancy":
                    role = discord.utils.get(message.guild.roles, name="Fancy")
                    if role:
                        await message.author.add_roles(role)
                        await message.channel.send("¡Te he otorgado el rol **Fancy**! ✨")
                elif item == "emoji_extra":
                    await message.channel.send("¡Ahora puedes usar emojis exclusivos en este servidor! 🥳")
                elif item == "titulo_especial":
                    await message.channel.send("¡Tu título especial será visible en la próxima actualización! 🏆")
            else:
                await message.channel.send(f'No tienes suficientes monedas para comprar "{item}". 💸')
        except IndexError:
            await message.channel.send('Uso correcto: `$comprar <nombre del artículo>`')
    
    if message.content.startswith('$inventario'):
        user_id = str(message.author.id)
        inventory = user_inventory.get(user_id, [])
        if inventory:
            inventory_message = f'{message.author.name}, estos son tus artículos:\n' + '\n'.join(f'- {item}' for item in inventory)
        else:
            inventory_message = f'{message.author.name}, tu inventario está vacío. 👜'
        await message.channel.send(inventory_message)
    
    if message.content.startswith('$limpiar'):
        # Verifica si el usuario tiene permiso para borrar mensajes
        if message.author.guild_permissions.manage_messages:
            try:
                # Obtener el argumento después del comando
                argumento = message.content.split('$limpiar ', 1)[1]

                if argumento.lower() == "all":
                    # Borra todos los mensajes en el canal
                    await message.channel.purge()
                    await message.channel.send('¡Todos los mensajes han sido borrados! ✅', delete_after=5)
                else:
                    # Intenta convertir el argumento en un número
                    cantidad = int(argumento)
                    if cantidad <= 0:
                        await message.channel.send('Debes especificar un número mayor a 0. ❌')
                        return

                    # Purga los mensajes especificados
                    await message.channel.purge(limit=cantidad + 1)  # +1 para incluir el comando
                    await message.channel.send(f'Se han borrado {cantidad} mensajes. ✅', delete_after=5)
            except (IndexError, ValueError):
                await message.channel.send('Uso correcto: `$limpiar <número de mensajes>` o `$limpiar all`. ❌')
        else:
            await message.channel.send('No tienes permiso para borrar mensajes. 🚫')
    
    if message.content.startswith('$novedades'):
        offers = get_steam_offers()
        if not offers:
            await message.channel.send("No hay ofertas disponibles en este momento. 😢")
            return
        
        # Muestra solo las ofertas sin encabezado
        for offer in offers[:5]:  # Muestra las primeras 5 ofertas
            novedades_msg = f"**{offer['name']}** - ${offer['price']:.2f}\n"
            novedades_msg += f"[Ver en Steam]({offer['url']})"
            
            # Envia la oferta sin texto adicional
            await message.channel.send(novedades_msg)


@client.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="Miembro")
    if role:
        await member.add_roles(role)
        await member.send(f'¡Bienvenido a {member.guild.name}, {member.name}! 🎉')

client.run('token')