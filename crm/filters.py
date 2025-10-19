import django_filters
from django.db.models import Q
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    """Filter class for Customer model"""
    
    # Case-insensitive partial match for name
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Name (partial match)'
    )
    
    # Case-insensitive partial match for email
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        label='Email (partial match)'
    )
    
    # Date range filters for created_at
    created_at_gte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created after (inclusive)'
    )
    
    created_at_lte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created before (inclusive)'
    )
    
    # Custom filter for phone number pattern
    phone_pattern = django_filters.CharFilter(
        method='filter_phone_pattern',
        label='Phone pattern (e.g., +1 for US numbers)'
    )
    
    def filter_phone_pattern(self, queryset, name, value):
        """
        Custom filter method to match phone numbers starting with a pattern
        Example: phone_pattern="+1" will match all US numbers
        """
        if value:
            return queryset.filter(phone__startswith=value)
        return queryset
    
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'created_at': ['exact', 'gte', 'lte'],
            'phone': ['exact', 'icontains'],
        }


class ProductFilter(django_filters.FilterSet):
    """Filter class for Product model"""
    
    # Case-insensitive partial match for name
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Name (partial match)'
    )
    
    # Price range filters
    price_gte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Minimum price'
    )
    
    price_lte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Maximum price'
    )
    
    # Stock range filters
    stock_gte = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='gte',
        label='Minimum stock'
    )
    
    stock_lte = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='lte',
        label='Maximum stock'
    )
    
    # Custom filter for low stock products
    low_stock = django_filters.BooleanFilter(
        method='filter_low_stock',
        label='Low stock (less than 10)'
    )
    
    def filter_low_stock(self, queryset, name, value):
        """
        Filter products with stock less than 10
        Usage: low_stock=true
        """
        if value:
            return queryset.filter(stock__lt=10)
        return queryset
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }


class OrderFilter(django_filters.FilterSet):
    """Filter class for Order model"""
    
    # Total amount range filters
    total_amount_gte = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        label='Minimum total amount'
    )
    
    total_amount_lte = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        label='Maximum total amount'
    )
    
    # Order date range filters
    order_date_gte = django_filters.DateTimeFilter(
        field_name='order_date',
        lookup_expr='gte',
        label='Order date from (inclusive)'
    )
    
    order_date_lte = django_filters.DateTimeFilter(
        field_name='order_date',
        lookup_expr='lte',
        label='Order date to (inclusive)'
    )
    
    # Filter by customer name (related field lookup)
    customer_name = django_filters.CharFilter(
        field_name='customer__name',
        lookup_expr='icontains',
        label='Customer name (partial match)'
    )
    
    # Filter by customer email
    customer_email = django_filters.CharFilter(
        field_name='customer__email',
        lookup_expr='icontains',
        label='Customer email (partial match)'
    )
    
    # Filter by product name (related field lookup)
    product_name = django_filters.CharFilter(
        field_name='products__name',
        lookup_expr='icontains',
        label='Product name (partial match)',
        distinct=True
    )
    
    # Filter orders containing a specific product ID
    product_id = django_filters.NumberFilter(
        field_name='products__id',
        lookup_expr='exact',
        label='Product ID',
        distinct=True
    )
    
    # Multiple product IDs filter
    product_ids = django_filters.BaseInFilter(
        field_name='products__id',
        lookup_expr='in',
        label='Product IDs (comma-separated)',
        distinct=True
    )
    
    # Custom filter for high-value orders
    high_value = django_filters.BooleanFilter(
        method='filter_high_value',
        label='High value orders (>= $1000)'
    )
    
    def filter_high_value(self, queryset, name, value):
        """
        Filter orders with total_amount >= 1000
        Usage: high_value=true
        """
        if value:
            return queryset.filter(total_amount__gte=1000)
        return queryset
    
    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte'],
            'order_date': ['exact', 'gte', 'lte'],
            'customer': ['exact'],
        }