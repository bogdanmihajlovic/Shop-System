from xmlrpc.server import SimpleXMLRPCServer

# Definišite funkciju koju želite da izložite putem XML-RPC-a
def primer():
    return "Da"

# Kreirajte server objekat i registrujte funkciju
server = SimpleXMLRPCServer(('0.0.0.0', 8000))
server.register_function(primer, 'primer')

# Pokrenite server
print("Server pokrenut...")
server.serve_forever()
