{% macro generate_schema_name(custom_schema_name, node) -%}
    {#- Custom schema verilmişse target schema ile birleştirmeden doğrudan kullan -#}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
