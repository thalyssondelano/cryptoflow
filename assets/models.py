from django.db import models
import uuid

class CryptoCurrency(models.UUIDModel if hasattr(models, 'UUIDModel') else models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=10, unique=True)
    current_price = models.DecimalField(max_digits=18, decimal_places=8)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"