from bson import ObjectId


class IdentificadorMongo:
    regex = '[0-9a-fA-F]{24}'

    def to_python(self, valor):
        return ObjectId(valor)

    def to_url(self, valor):
        return str(valor)
