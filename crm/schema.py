import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from crm.models import Product

# Object Types with Connection support
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)
    order_date = graphene.DateTime()


# Filter Input Types for custom filtering
class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.DateTime()
    created_at_lte = graphene.DateTime()
    phone_pattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    price_gte = graphene.Decimal()
    price_lte = graphene.Decimal()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()
    low_stock = graphene.Boolean()


class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Decimal()
    total_amount_lte = graphene.Decimal()
    order_date_gte = graphene.DateTime()
    order_date_lte = graphene.DateTime()
    customer_name = graphene.String()
    customer_email = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()
    high_value = graphene.Boolean()


# Helper Functions
def validate_phone(phone):
    """Validate phone format: +1234567890 or 123-456-7890"""
    if not phone:
        return True
    pattern = r'^(\+?\d{10,15}|\d{3}-\d{3}-\d{4})$'
    return re.match(pattern, phone) is not None


def validate_email_unique(email, exclude_id=None):
    """Check if email is unique"""
    query = Customer.objects.filter(email=email)
    if exclude_id:
        query = query.exclude(id=exclude_id)
    return not query.exists()


def apply_custom_filters(queryset, filter_input):
    """Apply custom filters to queryset"""
    if not filter_input:
        return queryset
    
    filter_dict = {}
    for key, value in filter_input.items():
        if value is not None:
            # Convert GraphQL filter names to Django filter syntax
            if key.endswith('_icontains'):
                field_name = key.replace('_icontains', '__icontains')
            elif key.endswith('_gte'):
                field_name = key.replace('_gte', '__gte')
            elif key.endswith('_lte'):
                field_name = key.replace('_lte', '__lte')
            else:
                field_name = key
            
            filter_dict[field_name] = value
    
    return queryset.filter(**filter_dict) if filter_dict else queryset


# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate email uniqueness
            if not validate_email_unique(input.email):
                return CreateCustomer(
                    customer=None,
                    message="Email already exists",
                    success=False
                )

            # Validate phone format
            if input.phone and not validate_phone(input.phone):
                return CreateCustomer(
                    customer=None,
                    message="Invalid phone format. Use +1234567890 or 123-456-7890",
                    success=False
                )

            # Create customer
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone if input.phone else None
            )
            customer.full_clean()
            customer.save()

            return CreateCustomer(
                customer=customer,
                message=f"Customer '{customer.name}' created successfully",
                success=True
            )

        except ValidationError as e:
            return CreateCustomer(
                customer=None,
                message=str(e),
                success=False
            )
        except Exception as e:
            return CreateCustomer(
                customer=None,
                message=f"Error creating customer: {str(e)}",
                success=False
            )


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success = graphene.Boolean()

    def mutate(self, info, input):
        created_customers = []
        errors = []

        with transaction.atomic():
            for idx, customer_data in enumerate(input):
                try:
                    # Validate email uniqueness
                    if not validate_email_unique(customer_data.email):
                        errors.append(
                            f"Row {idx + 1}: Email '{customer_data.email}' already exists"
                        )
                        continue

                    # Validate phone format
                    if customer_data.phone and not validate_phone(customer_data.phone):
                        errors.append(
                            f"Row {idx + 1}: Invalid phone format for '{customer_data.name}'"
                        )
                        continue

                    # Create customer
                    customer = Customer(
                        name=customer_data.name,
                        email=customer_data.email,
                        phone=customer_data.phone if customer_data.phone else None
                    )
                    customer.full_clean()
                    customer.save()
                    created_customers.append(customer)

                except ValidationError as e:
                    errors.append(f"Row {idx + 1}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {idx + 1}: {str(e)}")

        return BulkCreateCustomers(
            customers=created_customers,
            errors=errors if errors else None,
            success=len(created_customers) > 0
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate price
            if input.price <= 0:
                return CreateProduct(
                    product=None,
                    message="Price must be positive",
                    success=False
                )

            # Validate stock
            stock = input.stock if input.stock is not None else 0
            if stock < 0:
                return CreateProduct(
                    product=None,
                    message="Stock cannot be negative",
                    success=False
                )

            # Create product
            product = Product(
                name=input.name,
                price=input.price,
                stock=stock
            )
            product.full_clean()
            product.save()

            return CreateProduct(
                product=product,
                message=f"Product '{product.name}' created successfully",
                success=True
            )

        except ValidationError as e:
            return CreateProduct(
                product=None,
                message=str(e),
                success=False
            )
        except Exception as e:
            return CreateProduct(
                product=None,
                message=f"Error creating product: {str(e)}",
                success=False
            )


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                return CreateOrder(
                    order=None,
                    message=f"Customer with ID {input.customer_id} does not exist",
                    success=False
                )

            # Validate at least one product
            if not input.product_ids or len(input.product_ids) == 0:
                return CreateOrder(
                    order=None,
                    message="At least one product must be provided",
                    success=False
                )

            # Validate all products exist
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    return CreateOrder(
                        order=None,
                        message=f"Invalid product ID: {product_id}",
                        success=False
                    )

            # Create order with transaction
            with transaction.atomic():
                order = Order(customer=customer)
                if input.order_date:
                    order.order_date = input.order_date
                order.save()

                # Associate products
                order.products.set(products)

                # Calculate total amount
                total = sum(product.price for product in products)
                order.total_amount = total
                order.save()

            return CreateOrder(
                order=order,
                message=f"Order #{order.id} created successfully with total ${order.total_amount}",
                success=True
            )

        except ValidationError as e:
            return CreateOrder(
                order=None,
                message=str(e),
                success=False
            )
        except Exception as e:
            return CreateOrder(
                order=None,
                message=f"Error creating order: {str(e)}",
                success=False
            )


# Queries with Filtering
class Query(graphene.ObjectType):
    # Relay-style connection fields with filtering
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        order_by=graphene.String()
    )
    
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        order_by=graphene.String()
    )
    
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        order_by=graphene.String()
    )
    
    # Single object queries
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
    # List queries with custom filtering (non-relay)
    customers_list = graphene.List(
        CustomerType,
        filter=CustomerFilterInput(),
        order_by=graphene.String()
    )
    
    products_list = graphene.List(
        ProductType,
        filter=ProductFilterInput(),
        order_by=graphene.String()
    )
    
    orders_list = graphene.List(
        OrderType,
        filter=OrderFilterInput(),
        order_by=graphene.String()
    )

    # Resolvers for single objects
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

    # Resolvers for list queries with custom filtering
    def resolve_customers_list(self, info, filter=None, order_by=None):
        queryset = Customer.objects.all()
        
        if filter:
            if filter.get('name_icontains'):
                queryset = queryset.filter(name__icontains=filter['name_icontains'])
            if filter.get('email_icontains'):
                queryset = queryset.filter(email__icontains=filter['email_icontains'])
            if filter.get('created_at_gte'):
                queryset = queryset.filter(created_at__gte=filter['created_at_gte'])
            if filter.get('created_at_lte'):
                queryset = queryset.filter(created_at__lte=filter['created_at_lte'])
            if filter.get('phone_pattern'):
                queryset = queryset.filter(phone__startswith=filter['phone_pattern'])
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset

    def resolve_products_list(self, info, filter=None, order_by=None):
        queryset = Product.objects.all()
        
        if filter:
            if filter.get('name_icontains'):
                queryset = queryset.filter(name__icontains=filter['name_icontains'])
            if filter.get('price_gte'):
                queryset = queryset.filter(price__gte=filter['price_gte'])
            if filter.get('price_lte'):
                queryset = queryset.filter(price__lte=filter['price_lte'])
            if filter.get('stock_gte'):
                queryset = queryset.filter(stock__gte=filter['stock_gte'])
            if filter.get('stock_lte'):
                queryset = queryset.filter(stock__lte=filter['stock_lte'])
            if filter.get('low_stock'):
                queryset = queryset.filter(stock__lt=10)
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset

    def resolve_orders_list(self, info, filter=None, order_by=None):
        queryset = Order.objects.select_related('customer').prefetch_related('products').all()
        
        if filter:
            if filter.get('total_amount_gte'):
                queryset = queryset.filter(total_amount__gte=filter['total_amount_gte'])
            if filter.get('total_amount_lte'):
                queryset = queryset.filter(total_amount__lte=filter['total_amount_lte'])
            if filter.get('order_date_gte'):
                queryset = queryset.filter(order_date__gte=filter['order_date_gte'])
            if filter.get('order_date_lte'):
                queryset = queryset.filter(order_date__lte=filter['order_date_lte'])
            if filter.get('customer_name'):
                queryset = queryset.filter(customer__name__icontains=filter['customer_name'])
            if filter.get('customer_email'):
                queryset = queryset.filter(customer__email__icontains=filter['customer_email'])
            if filter.get('product_name'):
                queryset = queryset.filter(products__name__icontains=filter['product_name']).distinct()
            if filter.get('product_id'):
                queryset = queryset.filter(products__id=filter['product_id']).distinct()
            if filter.get('high_value'):
                queryset = queryset.filter(total_amount__gte=1000)
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset

class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    def mutate(self, info):
        from .models import Product

        # Find products with stock < 10
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated_list = []

        for product in low_stock_products:
            product.stock += 10  # restock
            product.save()
            updated_list.append(product)

        return UpdateLowStockProducts(
            updated_products=updated_list,
            message=f"{len(updated_list)} products restocked successfully."
        )


# Mutations
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()

# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)

