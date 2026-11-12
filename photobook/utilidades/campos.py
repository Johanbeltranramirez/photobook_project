from django.utils import timezone
from djongo import models

class FechaDocumento(models.DateTimeField):
    def to_python(self, valor):
        fecha = super().to_python(valor)
        if fecha is not None and timezone.is_naive(fecha):
            fecha = timezone.make_aware(fecha, timezone.utc)
        return fecha
