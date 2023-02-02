from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    slug = models.SlugField()
    # db_index creates an index for the `title` field
    # Should only be user on fields that are frequently searched
    title = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.title

# specific menu item
class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    # Is it the featured item?
    featured = models.BooleanField(db_index=True)
    # Every menu item belongs to a category
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.title

class Cart(models.Model):
    # If a user gets deleted all the cart data assosiated with that
    # user gets deleted too.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    '''the Meta class can also be used to specify
     other options such as ordering, database table name,
      permissions, and other options that are not related to fields.'''
    class Meta:
        unique_together = ('menuitem','user')

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True)
    # Is the order delivered?
    status = models.BooleanField(db_index=True, default=0)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(db_index=True)

# One entry for each menu item
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ('order','menuitem')
