from django.contrib import admin
from .models import Donor, Donation, Transaction

admin.site.register(Donor)
admin.site.register(Donation)
admin.site.register(Transaction)
