from .models import MenuItem, Category, Cart, Order
from rest_framework import serializers
from django.contrib.auth.models import User


class MenuItemSerializers(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    
    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category",]
        depth = 1
        

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["title", "slug"]


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'quantity', 'unit_price', 'price', 'menuitem']
        read_only_fields = ['user', 'unit_price', 'price']


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['total', 'user']