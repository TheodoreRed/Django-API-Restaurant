from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import MenuItemSerializers, CategorySerializer, ManagerSerializer, CartSerializer, OrdersSerializer
from rest_framework import generics, status
from .permissions import IsManager, IsDeliveryCrew, IsCustomer, IsAdminOrManager
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from django.contrib.auth.models import User, Group
from rest_framework.response import Response


class PermissionsMixin:
    def get_permissions(self):
        permission_classes = [IsAuthenticatedOrReadOnly]
        if self.request.method != 'GET':
            permission_classes = [IsAdminOrManager]
        return [permission() for permission in permission_classes]

class MenuItemListView(PermissionsMixin, generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializers
    filterset_fields = ['category','price']
    search_fields = ['title']

class SingleMenuItemView(PermissionsMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializers


class CategoryView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        permission_classes = [IsAuthenticatedOrReadOnly]
        if self.request.method != 'GET':
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ManagersView(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name='Managers')
    serializer_class = ManagerSerializer
    permission_classes = [IsAdminOrManager]

    def create(self, request):
        username = request.data.get('username')
        if username:
            user = User.objects.get(username=username)
            managers = Group.objects.get(name='Managers')
            managers.user_set.add(user)
            return Response(status=status.HTTP_201_CREATED, data={'message':f'User added to Managers group'})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message':f'Username is required'})


class ManagerDeleteView(generics.DestroyAPIView):
    queryset = User.objects.filter(groups__name='Managers')
    permission_classes = [IsAdminOrManager]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        managers = Group.objects.get(name='Managers')
        managers.user_set.remove(user)
        return Response(status=status.HTTP_200_OK)


class DeliveryCrewView(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name='DeliveryCrew')
    serializer_class = ManagerSerializer
    permission_classes = [IsAuthenticated, IsAdminUser | IsManager]

    def create(self, request):
        username = request.data.get('username')
        if username:
            user = User.objects.get(username=username)
            delivery_crew = Group.objects.get(name='DeliveryCrew')
            delivery_crew.user_set.add(user)
            return Response(status=status.HTTP_201_CREATED, data={'message':f'User added to DeliveryCrew group'})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message':f'Username is required'})


class DeliveryCrewDeleteView(generics.DestroyAPIView):
    queryset = User.objects.filter(groups__name='DeliveryCrew')
    permission_classes = [IsAuthenticated, IsAdminUser | IsManager]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        managers = Group.objects.get(name='DeliveryCrew')
        managers.user_set.remove(user)
        return Response(status=status.HTTP_200_OK)


class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serialized_data = self.get_serializer(data=request.data)
        serialized_data.is_valid(raise_exception=True)

        # Get menuitem and quantity from the validated data
        menuitem = serialized_data.validated_data['menuitem']
        quantity = serialized_data.validated_data['quantity']
        
        serialized_data.validated_data['unit_price'] = menuitem.price
        serialized_data.validated_data['price'] = quantity * menuitem.price

        serialized_data.save(user=self.request.user)
        return Response(status=status.HTTP_201_CREATED, data={'message':f'Added menu item to cart'})
    
    def delete(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response(
            {'message': f'Cart successfully deleted for {request.user.username}'},
            status.HTTP_200_OK
        )

class OrderView(generics.ListCreateAPIView):
    serializer_class = OrdersSerializer

    def get_permissions(self):
        
        if self.request.method == 'POST' : 
            permission_classes = [IsCustomer]
        else:
            permission_classes = [IsAuthenticated]
        return[permission() for permission in permission_classes]


    def get_queryset(self, *args, **kwargs):
        if self.request.user.groups.filter(name='Managers').exists() or self.request.user.is_superuser:
            # Manager : Returns all orders with order items by all users
            query = Order.objects.all()
        elif self.request.user.groups.filter(name='DeliveryCrew').exists():
            # Delivery crew : Returns all orders with order items assigned to the delivery crew
            query = Order.objects.filter(delivery_crew=self.request.user)
        else:
            # Customer : Returns all orders with order items created by this user
            query = Order.objects.filter(user=self.request.user)
        return query


    def create(self, request, *args, **kwargs):

        # Get the users cart
        cart = Cart.objects.filter(user=self.request.user)

        if cart.exists():
            serialized_data = self.serializer_class(data=request.data)
            serialized_data.is_valid(raise_exception=True)

            serialized_data.save(user=self.request.user, total=0)

            order = Order.objects.get(id=serialized_data.data['id'])

            total = 0

            for item in cart:
                order_item = OrderItem(order=order, menuitem=item.menuitem, quantity=item.quantity, unit_price=item.unit_price, price=item.price,)
                order_item.save()
                total += item.price
            
            cart.delete()
            order.total = total
            order.save()
            return Response({'message': f'Order added'}, status.HTTP_201_CREATED)
        else:
            return Response({'message': f'No items in cart!'}, status.HTTP_400_BAD_REQUEST)


class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrdersSerializer 
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            self.permission_classes = [IsManager | IsAdminUser]
        elif self.request.method == 'PATCH':
            self.permission_classes = [IsAdminUser | IsManager|IsDeliveryCrew]
        return [permission() for permission in self.permission_classes]

    def retrieve(self, request, *args, **kwargs):
        order = self.queryset.get(pk=kwargs['pk'])

        # If the requesting user is the customer, delivery_crew, manager, or admin
        if request.user == order.user or request.user == order.delivery_crew or request.user.groups.filter(name='Managers').exists() or request.user.is_superuser:
            serialized_order = self.get_serializer(order)
            return Response(serialized_order.data, status.HTTP_200_OK)
        return Response({'message': 'You do not have permission to see this page!'}, status.HTTP_403_FORBIDDEN)

    '''If the user making the request (request.user) is the
     same as the delivery crew associated with the order (order.delivery_crew),
      the order's status is updated to the value provided in the request data'''
    def partial_update(self, request, *args, **kwargs):

        order = self.queryset.get(pk=kwargs['pk'])
        if IsDeliveryCrew:
            order.status = request.data.get('status', order.status)
            order.save()
            serialized_order = self.get_serializer(order)
            return Response(serialized_order.data, status.HTTP_200_OK)
        elif IsManager or IsAdminUser:
            order.delivery_crew = request.data.get('delivery_crew', order.delivery_crew)
            order.status = request.data.get('status', order.status)
            order.save()
            serialized_order = self.get_serializer(order)
            return Response(serialized_order.data, status.HTTP_200_OK)
        else:
            return Response({'message': 'You do not have permission to perform this action!'}, status.HTTP_403_FORBIDDEN)



